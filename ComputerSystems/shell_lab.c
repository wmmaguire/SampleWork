/* 
 * tsh - A tiny shell program with job control
 * 
 * Max Maguire, wmaguire
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <ctype.h>
#include <signal.h>
#include <sys/types.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <errno.h>
#include "csapp.h"

/* Misc manifest constants */
#define MAXLINE_TSH    1024   /* max line size */
#define MAXARGS     128   /* max args on a command line */
#define MAXJOBS      16   /* max jobs at any point in time */
#define MAXJID    1<<16   /* max job ID */

/* Job states */
#define UNDEF         0   /* undefined */
#define FG            1   /* running in foreground */
#define BG            2   /* running in background */
#define ST            3   /* stopped */

/* 
 * Jobs states: FG (foreground), BG (background), ST (stopped)
 * Job state transitions and enabling actions:
 *     FG -> ST  : ctrl-z
 *     ST -> FG  : fg command
 *     ST -> BG  : bg command
 *     BG -> FG  : fg command
 * At most 1 job can be in the FG state.
 */

/* Parsing states */
#define ST_NORMAL   0x0   /* next token is an argument */
#define ST_INFILE   0x1   /* next token is the input file */
#define ST_OUTFILE  0x2   /* next token is the output file */
/* Set permission mode for Read/Write */
#define MODE S_IRUSR|S_IWUSR|S_IRGRP|S_IWGRP|S_IROTH|S_IWOTH
/* Global variables */
extern char **environ;      /* defined in libc */
char prompt[] = "tsh> ";    /* command line prompt (DO NOT CHANGE) */
int verbose = 0;            /* if true, print additional output */
int nextjid = 1;            /* next job ID to allocate */
char sbuf[MAXLINE_TSH];         /* for composing sprintf messages */

struct job_t {              /* The job struct */
    pid_t pid;              /* job PID */
    int jid;                /* job ID [1, 2, ...] */
    int state;              /* UNDEF, BG, FG, or ST */
    char cmdline[MAXLINE_TSH];  /* command line */
};
struct job_t job_list[MAXJOBS]; /* The job list */

struct cmdline_tokens {
    int argc;               /* Number of arguments */
    char *argv[MAXARGS];    /* The arguments list */
    char *infile;           /* The input file */
    char *outfile;          /* The output file */
    enum builtins_t {       /* Indicates if argv[0] is a builtin command */
        BUILTIN_NONE,
        BUILTIN_QUIT,
        BUILTIN_JOBS,
        BUILTIN_BG,
        BUILTIN_FG} builtins;
};

/* End global variables */

/* Function prototypes */
void eval(char *cmdline);

void sigchld_handler(int sig);
void sigtstp_handler(int sig);
void sigint_handler(int sig);

/* Here are helper routines that we've provided for you */
int parseline(const char *cmdline, struct cmdline_tokens *tok); 
void sigquit_handler(int sig);

void clearjob(struct job_t *job);
void initjobs(struct job_t *job_list);
int maxjid(struct job_t *job_list); 
int addjob(struct job_t *job_list, pid_t pid, int state, char *cmdline);
int deletejob(struct job_t *job_list, pid_t pid); 
pid_t fgpid(struct job_t *job_list);
struct job_t *getjobpid(struct job_t *job_list, pid_t pid);
struct job_t *getjobjid(struct job_t *job_list, int jid); 
int pid2jid(pid_t pid); 
void listjobs(struct job_t *job_list, int output_fd);
int Builtinfunc(struct cmdline_tokens tok);
void processBGFG(char **arg);
void DisplayMSG(long jid,long pid,char *msg,long sig);
void usage(void);


/*
 * main - The shell's main routine 
 */
int 
main(int argc, char **argv) 
{
    char c;
    char cmdline[MAXLINE_TSH];    /* cmdline for fgets */
    int emit_prompt = 1; /* emit prompt (default) */

    /* Redirect stderr to stdout (so that driver will get all output
     * on the pipe connected to stdout) */
    dup2(1, 2);

    /* Parse the command line */
    while ((c = getopt(argc, argv, "hvp")) != EOF) {
        switch (c) {
        case 'h':             /* print help message */
            usage();
            break;
        case 'v':             /* emit additional diagnostic info */
            verbose = 1;
            break;
        case 'p':             /* don't print a prompt */
            emit_prompt = 0;  /* handy for automatic testing */
            break;
        default:
            usage();
        }
    }

    /* Install the signal handlers */

    /* These are the ones you will need to implement */
    Signal(SIGINT,  sigint_handler);   /* ctrl-c */  
    Signal(SIGTSTP, sigtstp_handler);  /* ctrl-z */ 		
    Signal(SIGCHLD, sigchld_handler);  /* Terminated or stopped child */
    Signal(SIGTTIN, SIG_IGN); 							
    Signal(SIGTTOU, SIG_IGN); 						

    /* This one provides a clean way to kill the shell */				
    Signal(SIGQUIT, sigquit_handler);  					

    /* Initialize the job list */
    initjobs(job_list);

    /* Execute the shell's read/eval loop */
    while (1) {

        if (emit_prompt) {
            printf("%s", prompt);
            fflush(stdout);
        }
        if ((fgets(cmdline, MAXLINE_TSH, stdin) == NULL) && ferror(stdin))
            app_error("fgets error");
        if (feof(stdin)) { 
            /* End of file (ctrl-d) */
            printf ("\n");
            fflush(stdout);
            fflush(stderr);
            exit(0);
        }
        
        /* Remove the trailing newline */
        cmdline[strlen(cmdline)-1] = '\0';
        
        /* Evaluate the command line */
        eval(cmdline);
        
        fflush(stdout);
        fflush(stdout);
    } 
    
    exit(0); /* control never reaches here */
}

/* 
 * eval - Evaluate the command line that the user has just typed in
 * 
 * If the user has requested a built-in command (quit, jobs, bg or fg)
 * then execute it immediately. Otherwise, fork a child process and
 * run the job in the context of the child. If the job is running in
 * the foreground, wait for it to terminate and then return.  Note:
 * each child process must have a unique process group ID so that our
 * background children don't receive SIGINT (SIGTSTP) from the kernel
 * when we type ctrl-c (ctrl-z) at the keyboard.  
 */
void 
eval(char *cmdline)
{
    // initialize variables
    int bg; 
    int fin, fout;
    int fstdin = dup(STDIN_FILENO);
    int fstdout= dup(STDOUT_FILENO);    
    struct cmdline_tokens tok;
    pid_t pid;
    sigset_t maskchld,emptymask;
    /* Parse command line */
    // returns 1 for BG, 0 for FG, -1 for ERROR
    bg = parseline(cmdline, &tok);
    if (bg == -1)
        return;
    //ignore empty lines
    if (tok.argv[0] == NULL)
        return;
    //Update file descriptor for infile and copy to stdin
    if (tok.infile != NULL){
        fin  = Open(tok.infile,O_RDONLY,MODE);
        Dup2(fin,STDIN_FILENO); 
    }
    //Update file descriptor for outfile and copy to stdout
    if(tok.outfile != NULL){
        fout = Open(tok.outfile,O_CREAT|O_TRUNC|O_WRONLY,MODE);
        Dup2(fout,STDOUT_FILENO);
    }
    // Checks to see if input is not a built in function
    if(!Builtinfunc(tok)){
        // Avoid deletejob being called before adding job
        Sigemptyset(&maskchld);
        Sigemptyset(&emptymask);  
        Sigaddset(&maskchld, SIGINT);
        Sigaddset(&maskchld, SIGTSTP);
        Sigaddset(&maskchld, SIGCHLD);
        Sigprocmask(SIG_BLOCK,&maskchld,NULL);//Block SIGCHLD 
        if((pid = Fork()) == 0){
    	//Child
            Setpgid(0,0); //wrapper located in csp.c 
            Sigprocmask(SIG_UNBLOCK,&maskchld,NULL);//UNBLOCK sigchld
    	    execve(tok.argv[0],tok.argv,environ);
    	    printf("%s: Command Not found.\n",tok.argv[0]);
            exit(0);
        }
        //Parent
        // Add to job list using BG if bg == 1,FG if bg == 0
        addjob(job_list,pid,bg ? BG:FG,cmdline);
        Sigprocmask(SIG_UNBLOCK,&maskchld,NULL);//UNBLOCK sigchld
        if(!bg){ //Foreground process
           // Safely waits for foreground to return  
           while(pid == fgpid(job_list)){
               Sigsuspend(&emptymask);
           }
        }else{ //Background process
            printf("[%d] (%d) %s\n",pid2jid(pid),pid,cmdline);
        }

    }
    //close file descriptor for infile and reset stdin descriptor 
    if (tok.infile != NULL){
        Close(fin);
        Dup2(fstdin,STDIN_FILENO);
    }
    //close file descriptor for outfile and reset stdout descriptor
    if (tok.outfile != NULL){
        Close(fout);
        Dup2(fstdout,STDOUT_FILENO);
    } 
    return;
}

/* 
 * parseline - Parse the command line and build the argv array.
 * 
 * Parameters:
 *   cmdline:  The command line, in the form:
 *
 *                command [arguments...] [< infile] [> oufile] [&]
 *
 *   tok:      Pointer to a cmdline_tokens structure. The elements of this
 *             structure will be populated with the parsed tokens. Characters 
 *             enclosed in single or double quotes are treated as a single
 *             argument. 
 * Returns:
 *   1:        if the user has requested a BG job
 *   0:        if the user has requested a FG job  
 *  -1:        if cmdline is incorrectly formatted
 * 
 * Note:       The string elements of tok (e.g., argv[], infile, outfile) 
 *             are statically allocated inside parseline() and will be 
 *             overwritten the next time this function is invoked.
 */
int 
parseline(const char *cmdline, struct cmdline_tokens *tok) 
{

    static char array[MAXLINE_TSH];       /* holds local copy of command line */
    const char delims[10] = " \t\r\n";   /* argument delimiters (white-space) */
    char *buf = array;                   /* ptr that traverses command line */
    char *next;                          /* ptr to the end of the current arg */
    char *endbuf;                        /* ptr to end of cmdline string */
    int is_bg;                           /* background job? */

    int parsing_state;                   /* indicates if the next token is the
                                            input or output file */

    if (cmdline == NULL) {
        (void) fprintf(stderr, "Error: command line is NULL\n");
        return -1;
    }

    (void) strncpy(buf, cmdline, MAXLINE_TSH);
    endbuf = buf + strlen(buf);

    tok->infile = NULL;
    tok->outfile = NULL;

    /* Build the argv list */
    parsing_state = ST_NORMAL;
    tok->argc = 0;

    while (buf < endbuf) {
        /* Skip the white-spaces */
        buf += strspn (buf, delims);
        if (buf >= endbuf) break;

        /* Check for I/O redirection specifiers */
        if (*buf == '<') {
            if (tok->infile) {
                (void) fprintf(stderr, "Error: Ambiguous I/O redirection\n");
                return -1;
            }
            parsing_state |= ST_INFILE;
            buf++;
            continue;
        }
        if (*buf == '>') {
            if (tok->outfile) {
                (void) fprintf(stderr, "Error: Ambiguous I/O redirection\n");
                return -1;
            }
            parsing_state |= ST_OUTFILE;
            buf ++;
            continue;
        }

        if (*buf == '\'' || *buf == '\"') {
            /* Detect quoted tokens */
            buf++;
            next = strchr (buf, *(buf-1));
        } else {
            /* Find next delimiter */
            next = buf + strcspn (buf, delims);
        }
        
        if (next == NULL) {
            /* Returned by strchr(); this means that the closing
               quote was not found. */
            (void) fprintf (stderr, "Error: unmatched %c.\n", *(buf-1));
            return -1;
        }

        /* Terminate the token */
        *next = '\0';

        /* Record the token as either the next argument or the i/o file */
        switch (parsing_state) {
        case ST_NORMAL:
            tok->argv[tok->argc++] = buf;
            break;
        case ST_INFILE:
            tok->infile = buf;
            break;
        case ST_OUTFILE:
            tok->outfile = buf;
            break;
        default:
            (void) fprintf(stderr, "Error: Ambiguous I/O redirection\n");
            return -1;
        }
        parsing_state = ST_NORMAL;

        /* Check if argv is full */
        if (tok->argc >= MAXARGS-1) break;

        buf = next + 1;
    }

    if (parsing_state != ST_NORMAL) {
        (void) fprintf(stderr,
                       "Error: must provide file name for redirection\n");
        return -1;
    }

    /* The argument list must end with a NULL pointer */
    tok->argv[tok->argc] = NULL;

    if (tok->argc == 0)  /* ignore blank line */
        return 1;

    if (!strcmp(tok->argv[0], "quit")) {                 /* quit command */
        tok->builtins = BUILTIN_QUIT;
    } else if (!strcmp(tok->argv[0], "jobs")) {          /* jobs command */
        tok->builtins = BUILTIN_JOBS;
    } else if (!strcmp(tok->argv[0], "bg")) {            /* bg command */
        tok->builtins = BUILTIN_BG;
    } else if (!strcmp(tok->argv[0], "fg")) {            /* fg command */
        tok->builtins = BUILTIN_FG;
    } else {
        tok->builtins = BUILTIN_NONE;
    }

    /* Should the job run in the background? */
    if ((is_bg = (*tok->argv[tok->argc-1] == '&')) != 0)
        tok->argv[--tok->argc] = NULL;

    return is_bg;
}
/*********************
 * Built-in Functions
 *********************/
 int Builtinfunc(struct cmdline_tokens tok){
    switch(tok.builtins){
        case(BUILTIN_QUIT): 
            exit(0);
        case(BUILTIN_JOBS): 
            listjobs(job_list,STDOUT_FILENO);
            return 1;
        case(BUILTIN_BG): 
            processBGFG(tok.argv);
            return 1;
        case(BUILTIN_FG): 
            processBGFG(tok.argv);	
            return 1;
        default:
            return 0;
    }
 }

/*************************
 * End Built-in Functions
 *************************/
 /* Run stopped Background or Foreground job [BG & FG built-in function]*/
 void processBGFG(char **arg){
    // Checks to make sure that function has an argument
    sigset_t emptymask;
    Sigemptyset(&emptymask);
    if (arg[1] == NULL){
        printf("%s command requires PID or %%jobid argument\n",arg[0]);
        return;
    }
    struct job_t *job;
    int jid_flag = 0;
    int jid = -1;
    pid_t pid = -1;
    // Checks to see if argument is a jid "%#" or pid "#" 
    if(arg[1][0] == '%'){
        jid_flag = 1;
        jid  = atoi(&arg[1][1]);
        job  = getjobjid(job_list,jid); 
    }else{
        pid  = atoi(arg[1]);
        job  = getjobpid(job_list,pid); 
    }
    pid = job->pid;
    // Checks to see if arg job exists
    if (job != NULL){
        /* Checks to see BG or FG built in function
        and runs stopped job in its respective state  */   
        if(!(strcmp(arg[0],"bg"))){
            job->state = BG;
            printf("[%d] (%d) %s\n",jid,pid,job->cmdline);
            Kill(-pid,SIGCONT);
        }else{
            job->state = FG;
            Kill(-pid,SIGCONT);
            while(pid == fgpid(job_list)){
                Sigsuspend(&emptymask);
            }
        }
        return;     
    }else{
    // Outputs error if based on jid/pid entry if job doesn't exist 
        if(jid_flag){
            printf("(%d): No such job\n",jid);
            return;
        }else{
            printf("%d: No such job\n",pid);
            return;
        }
    }
 }

/*****************
 * Signal handlers
 *****************/

/* 
 * sigchld_handler - The kernel sends a SIGCHLD to the shell whenever
 *     a child job terminates (becomes a zombie), or stops because it
 *     received a SIGSTOP, SIGTSTP, SIGTTIN or SIGTTOU signal. The 
 *     handler reaps all available zombie children, but doesn't wait 
 *     for any other currently running children to terminate.  
 */
void 
sigchld_handler(int sig) 
{
    int status;
    sigset_t maskchld;
    pid_t chld_pid;
   /* Returns only for stopped or terminated jobs*/ 
    while((chld_pid = waitpid(-1,&status,WNOHANG|WUNTRACED)) > 0){
        int jid = pid2jid(chld_pid);
    // Block other signals to protect deleting chld_pid from job_list
        Sigfillset(&maskchld);
        Sigprocmask(SIG_BLOCK,&maskchld,NULL);//Block all other signals 
        // Job terminated normally
        if (WIFEXITED(status)){
            deletejob(job_list,chld_pid);
        // Child process was terminated by a signal
        }else if (WIFSIGNALED(status)){
            deletejob(job_list,chld_pid);
    // WTERMSIG: number of the signal that caused the child process to terminate
            status = WTERMSIG(status);
            DisplayMSG((long)jid,(long)chld_pid,"terminated",(long)status);
        // child process was stopped by delivery of a signal
        }else if (WIFSTOPPED(status)){
    // WSTOPSIG: number of the signal which caused the child to stop
            status = WSTOPSIG(status);
            DisplayMSG((long)jid,(long)chld_pid,"stopped",(long)status);
            getjobpid(job_list,chld_pid)->state = ST;
        }
        //unblock all other signals
        Sigprocmask(SIG_UNBLOCK,&maskchld,NULL);
    }
    return;
}

/* 
 * sigint_handler - The kernel sends a SIGINT to the shell whenver the
 *    user types ctrl-c at the keyboard.  Catch it and send it along
 *    to the foreground job.  
 */
void 
sigint_handler(int sig) 
{
    // find foreground process
    pid_t pid = fgpid(job_list);
    //make sure fg process exists
    if(pid != 0){
        // terminate all processes in process group (pid) with signal (sig).  
        Kill(-pid,sig);
    }
    return;
}

/*
 * sigtstp_handler - The kernel sends a SIGTSTP to the shell whenever
 *     the user types ctrl-z at the keyboard. Catch it and suspend the
 *     foreground job by sending it a SIGTSTP.  
 */
void 
sigtstp_handler(int sig) 
{
    // find foreground process
    pid_t pid = fgpid(job_list);
    //make sure fg process exists
    if(pid != 0){ 
        Kill(-pid,sig);
    }
    return;
}

/*
 * sigquit_handler - The driver program can gracefully terminate the
 *    child shell by sending it a SIGQUIT signal.
 */
void 
sigquit_handler(int sig) 
{
    sio_error("Terminating after receipt of SIGQUIT signal\n");
    exit(1);
}
/*********************
 * End signal handlers
 *********************/
/**/
 void DisplayMSG(long jid,long pid,char *msg,long sig){
    // Save method to send termination/stop messages.        
        Sio_puts("Job [");
        Sio_putl((long)jid);
        Sio_puts("] (");
        Sio_putl((long)pid);
        Sio_puts(") ");
        Sio_puts(msg);
        Sio_puts(" by signal ");
        Sio_putl((long)(sig));
        Sio_puts("\n");
 }
/***********************************************
 * Helper routines that manipulate the job list
 **********************************************/

/* clearjob - Clear the entries in a job struct */
void 
clearjob(struct job_t *job) {
    job->pid = 0;
    job->jid = 0;
    job->state = UNDEF;
    job->cmdline[0] = '\0';
}

/* initjobs - Initialize the job list */
void 
initjobs(struct job_t *job_list) {
    int i;

    for (i = 0; i < MAXJOBS; i++)
        clearjob(&job_list[i]);
}

/* maxjid - Returns largest allocated job ID */
int 
maxjid(struct job_t *job_list) 
{
    int i, max=0;

    for (i = 0; i < MAXJOBS; i++)
        if (job_list[i].jid > max)
            max = job_list[i].jid;
    return max;
}

/* addjob - Add a job to the job list */
int 
addjob(struct job_t *job_list, pid_t pid, int state, char *cmdline) 
{
    int i;

    if (pid < 1)
        return 0;

    for (i = 0; i < MAXJOBS; i++) {
        if (job_list[i].pid == 0) {
            job_list[i].pid = pid;
            job_list[i].state = state;
            job_list[i].jid = nextjid++;
            if (nextjid > MAXJOBS)
                nextjid = 1;
            strcpy(job_list[i].cmdline, cmdline);
            if(verbose){
                printf("Added job [%d] %d %s\n",
                       job_list[i].jid,
                       job_list[i].pid,
                       job_list[i].cmdline);
            }
            return 1;
        }
    }
    printf("Tried to create too many jobs\n");
    return 0;
}

/* deletejob - Delete a job whose PID=pid from the job list */
int 
deletejob(struct job_t *job_list, pid_t pid) 
{
    int i;

    if (pid < 1)
        return 0;

    for (i = 0; i < MAXJOBS; i++) {
        if (job_list[i].pid == pid) {
            clearjob(&job_list[i]);
            nextjid = maxjid(job_list)+1;
            return 1;
        }
    }
    return 0;
}

/* fgpid - Return PID of current foreground job, 0 if no such job */
pid_t 
fgpid(struct job_t *job_list) {
    int i;

    for (i = 0; i < MAXJOBS; i++)
        if (job_list[i].state == FG)
            return job_list[i].pid;
    return 0;
}

/* getjobpid  - Find a job (by PID) on the job list */
struct job_t 
*getjobpid(struct job_t *job_list, pid_t pid) {
    int i;

    if (pid < 1)
        return NULL;
    for (i = 0; i < MAXJOBS; i++)
        if (job_list[i].pid == pid)
            return &job_list[i];
    return NULL;
}

/* getjobjid  - Find a job (by JID) on the job list */
struct job_t *getjobjid(struct job_t *job_list, int jid) 
{
    int i;

    if (jid < 1)
        return NULL;
    for (i = 0; i < MAXJOBS; i++)
        if (job_list[i].jid == jid)
            return &job_list[i];
    return NULL;
}

/* pid2jid - Map process ID to job ID */
int 
pid2jid(pid_t pid) 
{
    int i;

    if (pid < 1)
        return 0;
    for (i = 0; i < MAXJOBS; i++)
        if (job_list[i].pid == pid) {
            return job_list[i].jid;
        }
    return 0;
}

/* listjobs - Print the job list */
void 
listjobs(struct job_t *job_list, int output_fd) 
{
    int i;
    char buf[MAXLINE_TSH];

    for (i = 0; i < MAXJOBS; i++) {
        memset(buf, '\0', MAXLINE_TSH);
        if (job_list[i].pid != 0) {
            sprintf(buf, "[%d] (%d) ", job_list[i].jid, job_list[i].pid);
            if(write(output_fd, buf, strlen(buf)) < 0) {
                fprintf(stderr, "Error writing to output file\n");
                exit(1);
            }
            memset(buf, '\0', MAXLINE_TSH);
            switch (job_list[i].state) {
            case BG:
                sprintf(buf, "Running    ");
                break;
            case FG:
                sprintf(buf, "Foreground ");
                break;
            case ST:
                sprintf(buf, "Stopped    ");
                break;
            default:
                sprintf(buf, "listjobs: Internal error: job[%d].state=%d ",
                        i, job_list[i].state);
            }
            if(write(output_fd, buf, strlen(buf)) < 0) {
                fprintf(stderr, "Error writing to output file\n");
                exit(1);
            }
            memset(buf, '\0', MAXLINE_TSH);
            sprintf(buf, "%s\n", job_list[i].cmdline);
            if(write(output_fd, buf, strlen(buf)) < 0) {
                fprintf(stderr, "Error writing to output file\n");
                exit(1);
            }
        }
    }
}
/******************************
 * end job list helper routines
 ******************************/


/***********************
 * Other helper routines
 ***********************/

/*
 * usage - print a help message
 */
void 
usage(void) 
{
    printf("Usage: shell [-hvp]\n");
    printf("   -h   print this message\n");
    printf("   -v   print additional diagnostic information\n");
    printf("   -p   do not emit a command prompt\n");
    exit(1);
}
