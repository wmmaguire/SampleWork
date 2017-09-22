/* Max Maguire, wmaguire
*
* This is a proxy that serves mutli-threaded web content
* In order to use this proxy, one must configure the following
* network settings in their Mozilla browser..
* 	HTTP Proxy: hostname
* 	Port: Port #
*
* It works by serving as server to the localhost (Open_listenfd)
* and a client to other servers that are accessed via the 
* Mozilla Browser (Open_clientfd)
*
* This proxy only supports GET funcitons and will maintain
* the 'User-Agent','Connection' and 'Proxy-Connection' as 
* static headers (defined as global variables)
*
* This proxy uses the POSIX threads library to spawn threads
* that execute in parallel.  This mechanism that controls this
* takes place in the main function and the thread sub-function
*/

#include <stdio.h>

/* Recommended max cache and object sizes */
#define MAX_CACHE_SIZE 1049000
#define MAX_OBJECT_SIZE 102400

/* You won't lose style points for including this long line in your code */
static char *user_agent_hdr = "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:10.0.3) Gecko/20120305 Firefox/10.0.3\r\n";
static char *connection_hdr = "Connection: close\r\n";
static char *pconnection_hdr = "Proxy-Connection: close\r\n";
/* $begin proxymain */
/*
 * proxy.c - A simple, concurrent HTTP/1.0 Web proxy that uses the 
 *     GET method to serve multi-threaded web content.
 */
#include "csapp.h"

void doit(int fd);
void retrieve_requesthdrs(rio_t *rp,char* buf_hdr);
int parse_uri(char *uri, char *hostname, char *port,char *path);
void clienterror(int fd, char *cause, char *errnum, 
		 char *shortmsg, char *longmsg);
void *thread(void *vargp);

int main(int argc, char **argv) 
{
	pthread_t tid;
    int listenfd, *connfd;
    char hostname[MAXLINE], port[MAXLINE];
    socklen_t clientlen;
    struct sockaddr_storage clientaddr;

    /* Check command line args */
    if (argc != 2) {
	fprintf(stderr, "usage: %s <port>\n", argv[0]);
	exit(1);
    }
    
    listenfd = Open_listenfd(argv[1]);
    while (1) {
		clientlen = sizeof(clientaddr);
		connfd = Malloc(sizeof(int));
		*connfd = Accept(listenfd, (SA *)&clientaddr, &clientlen); 
        printf("Accepted connection from (%s, %s)\n", hostname, port);
    	Pthread_create(&tid,NULL,thread,connfd);
    }
}
/* $end proxymain */

/*
 * doit - handle one HTTP request/response transaction
 */
/* $begin doit */
void doit(int fd) 
{

	char hostname[MAXLINE],port[MAXLINE],path[MAXLINE],grequest[MAXLINE];
	char host_hdr[MAXLINE],buf_hdr[MAXLINE];
	size_t lresp;
	int server_fd;
    char buf[MAXLINE], method[MAXLINE], uri[MAXLINE], version[MAXLINE];
    rio_t rio,rio2;

    /* Read request line and headers */
    Rio_readinitb(&rio, fd);
    if (!Rio_readlineb(&rio, buf, MAXLINE))  
        return;
    printf("%s", buf);
    sscanf(buf, "%s %s %s", method, uri, version);      
    if (strcasecmp(method, "GET")) {                    
        clienterror(fd, method, "501", "Not Implemented",
                    "Proxy does not implement this method");
        return;
    } 
    parse_uri(uri,hostname,port,path);
    sprintf(grequest,"GET %s HTTP/1.0\r\n",path);

    
    retrieve_requesthdrs(&rio,buf_hdr);  //updated*
    server_fd = Open_clientfd(hostname,port);
    // First send GET request
    Rio_writen(server_fd,grequest,strlen(grequest)); 
    // Then send Host/Miscelaneous headers
    sprintf(host_hdr,"Host: %s\r\n",hostname);
    Rio_writen(server_fd,host_hdr,strlen(host_hdr));
    Rio_writen(server_fd,buf_hdr,strlen(buf_hdr));
    // Finally, send pre-defined headers
    Rio_writen(server_fd,user_agent_hdr,strlen(user_agent_hdr));
    Rio_writen(server_fd,connection_hdr,strlen(connection_hdr));
    Rio_writen(server_fd,pconnection_hdr,strlen(pconnection_hdr));
    /*
    printf("Request: %s\n",grequest); //diagnostics
    printf("Host Hdr: %s\n",host_hdr); //diagnostics
    printf("Additional headers: \n%s\n",buf_hdr); //diagnostics 
    printf("User-Agent Hdr: %s\n",user_agent_hdr); //diagnostics
    printf("Connection Hdr: %s\n",connection_hdr); //diagnostics
    printf("Port Connection Hdr: %s\n",pconnection_hdr); //diagnostics
    */
    //Send parsed headers
	Rio_readinitb(&rio2, server_fd);
    while((lresp = Rio_readlineb(&rio2,buf,MAXLINE)) != 0){
    	printf("server received %d bytes\n",(int)lresp);
    	Rio_writen(fd,buf,lresp);
    }

}
/* $end doit */
/*
 * retrieve_requesthdrs - retrieve HTTP request headers
 */
/* $begin retrieve_requesthdrs */
void retrieve_requesthdrs(rio_t *rp,char *buf_hdr) 
{
    char buf[MAXLINE];
    char *hdr_cmp1 = "Connection";
    char *hdr_cmp2 = "User-Agent";
    char *hdr_cmp3 = "Proxy-connection";
    int eval;
    Rio_readlineb(rp, buf, MAXLINE);
    while(strcasecmp(buf, "\r\n")) {        
		Rio_readlineb(rp, buf, MAXLINE);
		if((eval = strncmp(buf,hdr_cmp1,strlen(hdr_cmp1)))==0){
			printf("\tSkip connection header...%s",buf);
			continue;
		}else if((eval = strncmp(buf,hdr_cmp2,strlen(hdr_cmp2)))==0){
			printf("\tSkip User-Agent header...%s",buf);
			continue;
		}else if((eval = strncmp(buf,hdr_cmp3,strlen(hdr_cmp3)))==0){
			printf("\tSkip Proxy-connection header...%s",buf);
			continue;
		}
		strcat(buf_hdr,buf);
    }
    return;
}
/* $end retrieve_requesthdrs */
/*
 * parse_uri - parse URI for Host,Port and Path
 */
/* $begin parse_uri */
int parse_uri(char *uri, char *hostname, char *port, char *path) 
{
    /*default outputs*/
	char *start;
	int flag = 0;
	int ind;
	int host_ind = 0,port_ind = 0,path_ind = 0;
	char temp_hostname[MAXLINE];
	char temp_port[MAXLINE];
	char temp_path[MAXLINE];
	if ((start = strstr(uri,"//")) != NULL){
		ind = (int)(start - uri)+2;
		while(uri[ind] != '\0'){
			if (uri[ind] == ':'){
				ind++;
				flag = 1;
			}
			if (uri[ind] == '/'){
				flag = 2;
			}
			switch(flag){
				case 0:
					temp_hostname[host_ind] = uri[ind];
					host_ind++;
					break;
				case 1:
					temp_port[port_ind] = uri[ind];
					port_ind++;
					break;
				default:
					temp_path[path_ind] = uri[ind];
					path_ind++;
					break;
			}	
			ind++;			
		}
	}else{
		return -1;
	}
	temp_hostname[host_ind] = '\0';
	temp_port[port_ind] 	= '\0';
	temp_path[path_ind] 	= '\0';

	
	strcpy(hostname,temp_hostname);
	strcpy(path,temp_path);
	if(strlen(temp_port)>0){
		strcpy(port,temp_port);
	}else{
		strcpy(port,"80");
	}

	return 0;
}
/* $end parse_uri */

/*
 * clienterror - returns an error message to the client
 */
/* $begin clienterror */
void clienterror(int fd, char *cause, char *errnum, 
		 char *shortmsg, char *longmsg) 
{
    char buf[MAXLINE], body[MAXBUF];

    /* Build the HTTP response body */
    sprintf(body, "<html><title>Tiny Error</title>");
    sprintf(body, "%s<body bgcolor=""ffffff"">\r\n", body);
    sprintf(body, "%s%s: %s\r\n", body, errnum, shortmsg);
    sprintf(body, "%s<p>%s: %s\r\n", body, longmsg, cause);
    sprintf(body, "%s<hr><em>The Tiny Web server</em>\r\n", body);

    /* Print the HTTP response */
    sprintf(buf, "HTTP/1.0 %s %s\r\n", errnum, shortmsg);
    Rio_writen(fd, buf, strlen(buf));
    sprintf(buf, "Content-type: text/html\r\n");
    Rio_writen(fd, buf, strlen(buf));
    sprintf(buf, "Content-length: %d\r\n\r\n", (int)strlen(body));
    Rio_writen(fd, buf, strlen(buf));
    Rio_writen(fd, body, strlen(body));
}
/* $end clienterror */

/*
 * thread - spawn thread to execute in parallel to serve
 * multiple simultaneous requests.  
 */
/* $begin thread */
void *thread(void *vargp) 
{
    int connfd = *((int *)vargp);
    Pthread_detach(pthread_self());
    Free(vargp);
    doit(connfd);
    Close(connfd);
    return NULL;
}
/* $end thread */