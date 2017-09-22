/* Max Maguire, wmaguire
 * 
 * VERSION 4:
 * Implementation of Malloc using FILO explicit list
 *      + Remove Footer for allocated blocks
 *      + Segregated List
 * */
/*
 ******************************************************************************
 *                               mm-baseline.c                                *
 *           64-bit struct-based implicit free list memory allocator          *
 *                  15-213: Introduction to Computer Systems                  *
 *                                                                            *
 *  ************************************************************************  *
 *                               DOCUMENTATION                                *
 *                                                                            *
 *  ** STRUCTURE. **                                                          *
 *                                                                            *
 *  Both allocated and free blocks share the same header structure.           *
 *  HEADER: 8-byte, aligned to 8th byte of an 16-byte aligned heap, where     *
 *          - The lowest order bit is 1 when the block is allocated, and      *
 *            0 otherwise.                                                    *
 *          - The whole 8-byte value with the least significant bit set to 0  *
 *            represents the size of the block as a size_t                    *
 *            The size of a block includes the header and footer.             *
 *  FOOTER: 8-byte, aligned to 0th byte of an 16-byte aligned heap. It        *
 *          contains the exact copy of the block's header.                    *
 *  The minimum blocksize is 32 bytes.                                        *
 *                                                                            *
 *  Allocated blocks contain the following:                                   *
 *  HEADER, as defined above.                                                 *
 *  PAYLOAD: Memory allocated for program to store information.               *
 *  FOOTER, as defined above.                                                 *
 *  The size of an allocated block is exactly PAYLOAD + HEADER + FOOTER.      *
 *                                                                            *
 *  Free blocks contain the following:                                        *
 *  HEADER, as defined above.                                                 *
 *  FOOTER, as defined above.                                                 *
 *  The size of an unallocated block is at least 32 bytes.                    *
 *                                                                            *
 *  Block Visualization.                                                      *
 *                    block     block+8          block+size-8   block+size    *
 *  Allocated blocks:   |  HEADER  |  ... PAYLOAD ...  |  FOOTER  |           *
 *                                                                            *
 *                    block     block+8          block+size-8   block+size    *
 *  Unallocated blocks: |  HEADER  |  ... (empty) ...  |  FOOTER  |           *
 *                                                                            *
 *  ************************************************************************  *
 *  ** INITIALIZATION. **                                                     *
 *                                                                            *
 *  The following visualization reflects the beginning of the heap.           *
 *      start            start+8           start+16                           *
 *  INIT: | PROLOGUE_FOOTER | EPILOGUE_HEADER |                               *
 *  PROLOGUE_FOOTER: 8-byte footer, as defined above, that simulates the      *
 *                    end of an allocated block. Also serves as padding.      *
 *  EPILOGUE_HEADER: 8-byte block indicating the end of the heap.             *
 *                   It simulates the beginning of an allocated block         *
 *                   The epilogue header is moved when the heap is extended.  *
 *                                                                            *
 *  ************************************************************************  *
 *  ** BLOCK ALLOCATION. **                                                   *
 *                                                                            *
 *  Upon memory request of size S, a block of size S + dsize, rounded up to   *
 *  16 bytes, is allocated on the heap, where dsize is 2*8 = 16.              *
 *  Selecting the block for allocation is performed by finding the first      *
 *  block that can fit the content based on a first-fit or next-fit search    *
 *  policy.                                                                   *
 *  The search starts from the beginning of the heap pointed by heap_listp.   *
 *  It sequentially goes through each block in the implicit free list,        *
 *  the end of the heap, until either                                         *
 *  - A sufficiently-large unallocated block is found, or                     *
 *  - The end of the implicit free list is reached, which occurs              *
 *    when no sufficiently-large unallocated block is available.              *
 *  In case that a sufficiently-large unallocated block is found, then        *
 *  that block will be used for allocation. Otherwise--that is, when no       *
 *  sufficiently-large unallocated block is found--then more unallocated      *
 *  memory of size chunksize or requested size, whichever is larger, is       *
 *  requested through mem_sbrk, and the search is redone.                     *
 *                                                                            *
 *  ************************************************************************  *
 *  ** ADVICE FOR STUDENTS. **                                                *
 *  Step 0: Please read the writeup!                                          *
 *  Write your heap checker. Write your heap checker. Write. Heap. checker.   *
 *  Good luck, and have fun!                                                  *
 *                                                                            *
 ******************************************************************************
 */

/* Do not change the following! */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stddef.h>
#include <assert.h>
#include <stddef.h>

#include "mm.h"
#include "memlib.h"

#ifdef DRIVER
/* create aliases for driver tests */
#define malloc mm_malloc
#define free mm_free
#define realloc mm_realloc
#define calloc mm_calloc
#define memset mem_memset
#define memcpy mem_memcpy
#endif /* def DRIVER */

/* You can change anything from here onward */

/*
 * If DEBUG is defined, enable printing on dbg_printf and contracts.
 * Debugging macros, with names beginning "dbg_" are allowed.
 * You may not define any other macros having arguments.
 */
//#define DEBUG // uncomment this line to enable debugging

#ifdef DEBUG
/* When debugging is enabled, these form aliases to useful functions */
#define dbg_printf(...) printf(__VA_ARGS__)
#define dbg_requires(...) assert(__VA_ARGS__)
#define dbg_assert(...) assert(__VA_ARGS__)
#define dbg_ensures(...) assert(__VA_ARGS__)
#else
/* When debugging is disnabled, no code gets generated for these */
#define dbg_printf(...)
#define dbg_requires(...)
#define dbg_assert(...)
#define dbg_ensures(...)
#endif

/* Basic constants */
typedef uint64_t word_t;
static const size_t wsize = sizeof(word_t);   // word and header size (bytes)
static const size_t dsize = 2*wsize;          // double word size (bytes)
static const size_t min_block_size = 2*dsize; // Minimum block size
static const size_t chunksize = (1 << 10);    // requires (chunksize % 16 == 0)
// segListsize: index represents blocks sizes of idx^2
static const size_t seglistsize = 10;          

static const word_t alloc_mask = 0x1;
static const word_t size_mask = ~(word_t)0xF;

// New typde def for link list
typedef struct block blkhdr;
typedef struct block
{
    /* Header contains size + allocation flag */
    word_t header;
    union{
        struct{
        blkhdr* next_p;
        blkhdr* prev_p;
    };
        char payload[0];
    };
} block_t;

static void removeFreeBlock(blkhdr* freeBlock); // new function
static void insertFreeBlock(blkhdr* freeBlock); // new function
static int findSegListInd(size_t bsize);        // new function

/* Global variables */
/* Pointer to first block */
static block_t *heap_listp = NULL;
/* Pointer to list of free blocks */
static block_t *free_listp[seglistsize];
static block_t *end_listp[seglistsize];

/* Function prototypes for internal helper routines */
static block_t *extend_heap(size_t size);
static void place(block_t *block, size_t asize);
static block_t *find_fit(size_t asize);
static block_t *coalesce(block_t *block);

static size_t max(size_t x, size_t y);
static size_t round_up(size_t size, size_t n);
static word_t pack(size_t size, bool alloc);
static word_t set_prev_alloc(size_t n_header, bool alloc); // new function

static size_t extract_size(word_t header);
static size_t get_size(block_t *block);
static size_t get_payload_size(block_t *block);

static bool extract_alloc(word_t header);
static bool get_alloc(block_t *block);
static bool get_prev_alloc(block_t *block); // new function

static void write_header(block_t *block, size_t size, bool alloc);
static void write_footer(block_t *block, size_t size, bool alloc);

static block_t *payload_to_header(void *bp);
static void *header_to_payload(block_t *block);

static block_t *find_next(block_t *block);
static word_t *find_prev_footer(block_t *block);
static block_t *find_prev(block_t *block);

bool mm_checkheap(int lineno);
//mm_checkheap helper sub-functions
bool Blockcheck();
bool EpiProCheck();
bool freelistcheck();
bool headfootcheck();
static bool aligned(const void *p);
static bool in_heap(const void *p);
static size_t align(size_t x);

/*
 * mm_init: initializes the heap; it is run once when heap_start == NULL.
 *          prior to any extend_heap operation, this is the heap:
 *              start            start+8           start+16
 *          INIT: | PROLOGUE_FOOTER | EPILOGUE_HEADER |
 * heap_listp ends up pointing to the epilogue header.
 */
bool mm_init(void) 
{
    dbg_printf("\n\n*******BEGINNING OF TRACE**********\n\n");
    // Create the initial empty heap 
    word_t *start = (word_t *)(mem_sbrk(dsize));
    if (start == (void *)-1){
        return false;
    }
    start[0] = pack(0, true); // Prologue footer
    start[1] = pack(0, true); // Epilogue header
    block_t* epi = (block_t *)&start[1];
    epi->header = set_prev_alloc(epi->header, true);
    
    // Heap starts with first block header (epilogue)
    heap_listp = (block_t *) &(start[1]);
    for (int list_ind = 0;list_ind < (int)seglistsize; list_ind += 1){
        end_listp[list_ind]  = NULL;
        free_listp[list_ind] = NULL; 
    }
    // Extend the empty heap with a free block of chunksize bytes
    if (extend_heap(chunksize) == NULL){
        return false;
    }
    return true;
}

/*
 * malloc: allocates a block with size at least (size + dsize), rounded up to
 *         the nearest 16 bytes, with a minimum of 2*dsize. Seeks a
 *         sufficiently-large unallocated block on the heap to be allocated.
 *         If no such block is found, extends heap by the maximum between
 *         chunksize and (size + dsize) rounded up to the nearest 16 bytes,
 *         and then attempts to allocate all, or a part of, that memory.
 *         Returns NULL on failure, otherwise returns a pointer to such block.
 *         The allocated block will not be used for further allocations until
 *         freed.
 */
void *malloc(size_t size) 
{
    dbg_requires(mm_checkheap); 
    size_t asize;      // Adjusted block size
    size_t extendsize; // Amount to extend heap if no fit is found
    block_t *block;
    void *bp = NULL;
   
    if (heap_listp == NULL) // Initialize heap if it isn't initialized
    {
        mm_init();
    }

    if (size == 0) // Ignore spurious request
    {
        dbg_ensures(mm_checkheap);
        return bp;
    }

    // Adjust block size to include overhead and to meet alignment requirements
    if (size < 16){
        asize = round_up(size,dsize)+dsize;
    } else{
        asize = round_up(size+wsize,dsize);
    }
        // Search the free list for a fit
    block = find_fit(asize);

    // If no fit is found, request more memory, and then and place the block
    if (block == NULL)
    {  
        extendsize = max(asize, chunksize);
        block = extend_heap(extendsize);
        if (block == NULL) // extend_heap returns an error
        {
            return bp;
        }

    }

    place(block, asize);
    bp = header_to_payload(block);

    dbg_printf("Malloc size %zd on address %p.\n", size, bp);
    dbg_ensures(mm_checkheap);
    return bp;
} 

/*
 * free: Frees the block such that it is no longer allocated while still
 *       maintaining its size. Block will be available for use on malloc.
 */
void free(void *bp)
{
    if (bp == NULL)
    {
        return;
    }

    block_t *block = payload_to_header(bp);
    size_t size = get_size(block);
    dbg_printf("\n\t\t ENTERING FREE: (Blk) %p, (sz) %zu\n",(char *)block,size);

    write_header(block, size, false);
    write_footer(block, size, false);

    coalesce(block);

}

/*
 * realloc: returns a pointer to an allocated region of at least size bytes:
 *          if ptrv is NULL, then call malloc(size);
 *          if size == 0, then call free(ptr) and returns NULL;
 *          else allocates new region of memory, copies old data to new memory,
 *          and then free old block. Returns old block if realloc fails or
 *          returns new pointer on success.
 */
void *realloc(void *ptr, size_t size)
{
    block_t *block = payload_to_header(ptr);
    size_t copysize;
    void *newptr;

    // If size == 0, then free block and return NULL
    if (size == 0)
    {
        free(ptr);
        return NULL;
    }

    // If ptr is NULL, then equivalent to malloc
    if (ptr == NULL)
    {
        return malloc(size);
    }

    // Otherwise, proceed with reallocation
    newptr = malloc(size);
    // If malloc fails, the original block is left untouched
    if (!newptr)
    {
        return NULL;
    }

    // Copy the old data
    copysize = get_payload_size(block); // gets size of old payload
    if(size < copysize)
    {
        copysize = size;
    }
    memcpy(newptr, ptr, copysize);

    // Free the old block
    free(ptr);

    return newptr;
}

/*
 * calloc: Allocates a block with size at least (elements * size + dsize)
 *         through malloc, then initializes all bits in allocated memory to 0.
 *         Returns NULL on failure.
 */
void *calloc(size_t nmemb, size_t size)
{
    void *bp;
    size_t asize = nmemb * size;

    if (asize/nmemb != size)
    // Multiplication overflowed
    return NULL;
    
    bp = malloc(asize);
    if (bp == NULL)
    {
        return NULL;
    }
    // Initialize all bits to 0
    memset(bp, 0, asize);

    return bp;
}

/******** The remaining content below are helper and debug routines ********/

/*
 * extend_heap: Extends the heap with the requested number of bytes, and
 *              recreates epilogue header. Returns a pointer to the result of
 *              coalescing the newly-created block with previous free block, if
 *              applicable, or NULL in failure.
 */
static block_t *extend_heap(size_t size) 
{
    void *bp;

    // Allocate an even number of words to maintain alignment
    size = round_up(size, dsize);
    if ((bp = mem_sbrk(size)) == (void *)-1)
    {
        return NULL;
    }
    
    // Initialize free block header/footer 
    block_t *block = payload_to_header(bp);
    write_header(block, size, false);
    write_footer(block, size, false);
    // Create new epilogue header
    block_t *block_next = find_next(block);
    write_header(block_next, 0, true);
    // Coalesce in case the previous block was free
    return coalesce(block);
}

/* Coalesce: Coalesces current block with previous and next blocks if either
 *           or both are unallocated; otherwise the block is not modified.
 *           Returns pointer to the coalesced block. After coalescing, the
 *           immediate contiguous previous and next blocks must be allocated.
 */
static block_t *coalesce(block_t * block) 
{
    dbg_printf("\n\t\t ENTERING Coalesce\n");
    block_t *block_prev;
    block_t *block_next = find_next(block);

    bool prev_alloc = get_prev_alloc(block);
    bool next_alloc = get_alloc(block_next);
    size_t size = get_size(block);
/// [-----]<->[BLOCK]<->[-----]
    if (prev_alloc && next_alloc)              // Case 1
    {
        dbg_printf("\tCase1:  [-----]<->[BLOCK]<->[-----]\n");
        // NOTE: only instance in which list of free block list increments
        block->header = set_prev_alloc(block->header, true);
        block_next->header = set_prev_alloc(block_next->header, false);
        insertFreeBlock(block); 
        return block;
    }
// [-----]<->[BLOCK]<->[_____]
    else if (prev_alloc && !next_alloc)        // Case 2
    {
        dbg_printf("\tCase2:  [-----]<->[BLOCK]<->[      ]\n");
        removeFreeBlock(block_next);
        size += get_size(block_next);
        write_header(block, size, false);
        write_footer(block, size, false);
        block->header = set_prev_alloc(block->header, true);
        insertFreeBlock(block); 
    }
// [_____]<->[BLOCK]<->[-----]
    else if (!prev_alloc && next_alloc)        // Case 3
    {
        dbg_printf("\tCase3:  [       ]<->[BLOCK]<->[-----]\n");
        block_prev = find_prev(block);
        removeFreeBlock(block_prev);
        size += get_size(block_prev);
        write_header(block_prev, size, false);
        write_footer(block_prev, size, false);
        block_next->header = set_prev_alloc(block_next->header, false);
        block_prev->header = set_prev_alloc(block_prev->header, true);
        block = block_prev;
        insertFreeBlock(block); 
    }
// [_____]<->[BLOCK]<->[_____]
    else                                        // Case 4
    {
        dbg_printf("\tCase4:  [      ]<->[BLOCK]<->[      ]\n");
        block_prev = find_prev(block);    
        removeFreeBlock(block_next);
        removeFreeBlock(block_prev);
        size += get_size(block_next) + get_size(block_prev);
        write_header(block_prev, size, false);
        write_footer(block_prev, size, false);
        block_prev->header = set_prev_alloc(block_prev->header, true);
        block = block_prev;
        insertFreeBlock(block); 
    }
    return block;
}

/*
 * place: Places block with size of asize at the start of bp. If the remaining
 *        size is at least the minimum block size, then split the block to the
 *        the allocated block and the remaining block as free, which is then
 *        inserted into the segregated list. Requires that the block is
 *        initially unallocated.
 */
static void place(block_t *block, size_t asize)
{
    dbg_printf("\n\t\t ENTERING place\n");
    size_t csize = get_size(block);
    block_t *block_next;
    removeFreeBlock(block);
    if ((csize - asize) >= min_block_size)
    {
        write_header(block, asize, true);
        block_next = find_next(block);
        write_header(block_next, csize-asize, false);
        write_footer(block_next, csize-asize, false);

        block_next->header = set_prev_alloc(block_next->header, true);
        block->header = set_prev_alloc(block->header, true);

        insertFreeBlock(block_next);
    }
    else
    { 
        write_header(block, csize, true);
        block_next = find_next(block);
        block_next->header = set_prev_alloc(block_next->header, true);
    }
}

/*
 * find_fit: Looks for a free block with at least asize bytes with
 *           first-fit policy. Returns NULL if none is found.
 */
static block_t *find_fit(size_t asize)
{
    dbg_printf("\n\t\t ENTERING find_fit\n");
    block_t *block;
    size_t bsize   = 0;
    int sl_ind = findSegListInd(asize);
 //   dbg_printf("\t Seg List Ind: %d\n",sl_ind);
    for (sl_ind = findSegListInd(asize);
            sl_ind < 10;
                sl_ind++)
    {
        for (block = end_listp[sl_ind];
            block != NULL; 
                block = block->prev_p)
        {
            bsize = get_size(block);
            if (asize <= bsize)
            {
                dbg_printf("\n BLOCK FIT: (FB)");
                dbg_printf("%p, %zd > %zd\n",block,bsize,asize);
                return block;
            }
            dbg_printf("\n\t\t In LOOP -> block");
            dbg_printf("%p: %zd < %zd\n",block,bsize,asize);
        }
    }
    dbg_printf("\n NO FIT for size: %zd\n",asize);
    return NULL; // no fit found
}
/*
 * max: returns x if x > y, and y otherwise.
 */
static size_t max(size_t x, size_t y)
{
    return (x > y) ? x : y;
}


/*
 * round_up: Rounds size up to next multiple of n
 */
static size_t round_up(size_t size, size_t n)
{
    return (n * ((size + (n-1)) / n));
}

/*
 * pack: returns a header reflecting a specified size and its alloc status.
 *       If the block is allocated, the lowest bit is set to 1, and 0 otherwise.
 */
static word_t pack(size_t size, bool alloc)
{
    return alloc ? (size | 1) : size;
}

/*
 * set_prev_alloc: returns a header reflecting the allocation status of the 
 * previous block. If the block is allocated, the 2nd lowest bit is set to 1,
 * and 0 otherwise.
 */
static word_t set_prev_alloc(size_t n_header, bool alloc)
{
    return alloc ? (n_header | 2) : (n_header & ~2);
}

/*
 * extract_size: returns the size of a given header value based on the header
 *               specification above.
 */
static size_t extract_size(word_t word)
{
    return (word & size_mask);
}

/*
 * get_size: returns the size of a given block by clearing the lowest 4 bits
 *           (as the heap is 16-byte aligned).
 */
static size_t get_size(block_t *block)
{
    return extract_size(block->header);
}

/*
 * get_payload_size: returns the payload size of a given block, equal to
 *                   the entire block size minus the header and footer sizes.
 */
static word_t get_payload_size(block_t *block)
{
    size_t asize = get_size(block);
    return asize - wsize; //footer removed
}

/*
 * extract_alloc: returns the allocation status of a given header value based
 *                on the header specification above.
 */
static bool extract_alloc(word_t word)
{
    return (bool)(word & alloc_mask);
}

/*
 * get_alloc: returns true when the block is allocated based on the
 *            block header's lowest bit, and false otherwise.
 */
static bool get_alloc(block_t *block)
{
    return extract_alloc(block->header);
}
/*
 * get_prev_alloc: returns true when the previous block is allocated based on 
 *            the block header's 2nd lowest bit, and false otherwise.
 */
static bool get_prev_alloc(block_t *block)
{
    if (block != heap_listp){
        return (bool)(block->header & 0x2);
    }
        return true;
}
/*
 * write_header: given a block and its size and allocation status,
 *               writes an appropriate value to the block header.
 */
static void write_header(block_t *block, size_t size, bool alloc)
{   
    word_t prevBLK_alloc = block->header & 0x2;
    block->header        = pack(size, alloc) | prevBLK_alloc;  
}


/*
 * write_footer: given a block and its size and allocation status,
 *               writes an appropriate value to the block footer by first
 *               computing the position of the footer.
 */
static void write_footer(block_t *block, size_t size, bool alloc)
{
    // Modified write_footer to write at offset determined by min_block_size
    word_t *footerp = (word_t *)((block->payload) + get_size(block) - dsize);
    *footerp = pack(size, alloc);
}


/*
 * find_next: returns the next consecutive block on the heap by adding the
 *            size of the block.
 */
static block_t *find_next(block_t *block)
{
    dbg_requires(block != NULL);
    block_t *block_next = (block_t *)(((char *)block) + get_size(block));

    dbg_ensures(block_next != NULL);
    return block_next;
}

/*
 * find_prev_footer: returns the footer of the previous block.
 */
static word_t *find_prev_footer(block_t *block)
{
    // Compute previous footer position as one word before the header
    return (&(block->header)) - 1;
}

/*
 * find_prev: returns the previous block position by checking the previous
 *            block's footer and calculating the start of the previous block
 *            based on its size.
 */
static block_t *find_prev(block_t *block)
{
    word_t *footerp = find_prev_footer(block);
    size_t size = extract_size(*footerp);
    return (block_t *)((char *)block - size);
}

/*
 * payload_to_header: given a payload pointer, returns a pointer to the
 *                    corresponding block.
 */
static block_t *payload_to_header(void *bp)
{
    return (block_t *)(((char *)bp) - offsetof(block_t, payload));
}

/*
 * header_to_payload: given a block pointer, returns a pointer to the
 *                    corresponding payload.
 */
static void *header_to_payload(block_t *block)
{
    return (void *)(block->payload);
}

/* mm_checkheap: checks the heap for correctness; returns true if
 *               the heap is correct, and false otherwise.
 *               can call this function using mm_checkheap(__LINE__);
 *               to identify the line number of the call site.
 */
bool mm_checkheap(int lineno)  
{   
    /* Heap checkers*/
    // Check epi/pro-logue
    if(!EpiProCheck()){
        return false;
    }
    if(!Blockcheck()){
        return false;
    }
    /* Free list cheker*/
    // Check free list for errors
    if(!freelistcheck()){
        return false;
    }
   
    return true;
}
/*********************************************************/
/********* Beginning of helper sub-functions *************/
/*********************************************************/

bool Blockcheck(){
    // return block to start of block heap
    block_t *block = (block_t*)((char *)(mem_heap_lo()) + 8);
    while(get_size(block)>0){
        // Spec 1: check to see if block is alligned (min_block_size)
        if(!aligned(block)) {
            printf("ERROR: Block alignment issues %p\n",block); 
            return false;
        }
        // Spec 2: Check each block's header & footer
        block = find_next(block);
    }
    return true;
}

/* Check Epilogue*/
bool EpiProCheck(){
    
    // return cur block to start of block heap
    block_t *pro_block = (block_t*)((char *)(mem_heap_lo()) + 8);
    if((int)pro_block != 1){
        return false;
    }
    // return  to start of block heap
    block_t *epi_block = (block_t*)((char *)(mem_heap_hi()) - 8);
    if((int)epi_block != 1){
        return false;
    }
    return true;

}
/* Checks to see if free list follows basic specs*/
bool freelistcheck(){
    block_t *cur_block,*prev_block;
    // initialize counters
    int flist_cnt = 0;
    int alloc_cnt = 0; 
    int total_cnt = 0; 
    // initialize size variable
    size_t bsize = 0; 
    // Loop through indeces of free block pointers
    for(int i_FLP = 0; i_FLP < (int)seglistsize; i_FLP++){
        cur_block  = free_listp[i_FLP];                                   
        prev_block = cur_block;
        // loop through each block in free list
        while(cur_block != NULL){
                flist_cnt += 1;
                bsize = get_size(cur_block);
                // Spec1: check to see if pointer is bounded within heap
                if(!in_heap(cur_block)){
                    printf("ERROR: free list block Out of Heap Range\t");
                    return false;
                }
                prev_block = cur_block;
                // only proceeds to check next condition if multiple blocks in list
                if((cur_block = cur_block->next_p) == NULL){
                    break;
                }
                // Spec2: check to see if previous pointer is set correctly
                if(cur_block->prev_p != prev_block){
                    printf("ERROR: free list pointer mismatch ->\t");
                    printf("%p != %p\n",prev_block,cur_block->prev_p);
                    return false;
                }
        }
    }
    // return cur_block to start of block heap
    cur_block = (block_t*)((char *)(mem_heap_lo()) + 8);
    // Spec3: loop through all blocks to check consistency w/ free list
    while((bsize = get_size(cur_block))>0){
        total_cnt += 1;
        if(!get_alloc(cur_block)){
            printf("FREE Block %p,size %zu\n",(char *)cur_block,bsize);
            flist_cnt -= 1;
        }else{
            printf("\tALLOCATED Block %p,size %zu\n",(char *)cur_block,bsize);
            alloc_cnt += 1;
        }
        cur_block = find_next(cur_block);
    }
    // flist_cnt should decrement back to 0...
    if(flist_cnt != 0){ 
        printf("ERROR: free list False Count ->\n\t");
        printf("(tblocks) %d, (ablocks) %d\t",total_cnt,alloc_cnt);
        printf("\t(flist error) %d\n",flist_cnt);
        return false;
    }
   return true; 
}
/* rounds up to the nearest multiple of min_block_size   */
static size_t align(size_t x) {
    return min_block_size * ((x+min_block_size-1)/min_block_size);
}
/* Return whether the pointer is in the heap */
static bool in_heap(const void *p) {
    return p <= mem_heap_hi() && p >= mem_heap_lo();
}

/* Return whether the pointer is aligned */
static bool aligned(const void *p) {
    size_t ip = (size_t) p;
    return align(ip) == ip;
}
/*********************************************************/
/************* End of helper sub-functions ***************/
/*********************************************************/
/* find index of segregated list associated with block size. */
static int findSegListInd(size_t bsize){
    // initialize free list chunk size to 8
    int eval_size = 0x8;
    size_t SL_ind; 
    // Shift eval_size left to increase by power of 2 
    // (8,32,64,128,256,512,1024,2048,4096,8192,16384)
    for(SL_ind = 0; SL_ind < seglistsize; SL_ind += 1){
        if((size_t)eval_size >= bsize){
            return (int)SL_ind;
        }
        eval_size = eval_size << 1; 
    }
    return (int)(seglistsize-1);
}
/* Insert freeBlock at the head of the list. */
// [FLP]<-->[NEW BLOCK]<-->[PREV NEW BLOCK]<-->....
static void insertFreeBlock(blkhdr* freeBlock) { 
    int sl_ind = findSegListInd(get_size(freeBlock));
    // [FLP = new block]<->[   ]
    if (free_listp[sl_ind] == NULL){
        freeBlock->next_p = NULL;
        freeBlock->prev_p = NULL;
        end_listp[sl_ind] = freeBlock; 
    // [FLP = new block]<-->[old new block/FLP]<->...
    }else{
        freeBlock->next_p = free_listp[sl_ind];
        freeBlock->prev_p = NULL;
        free_listp[sl_ind]->prev_p = freeBlock;
    }
    free_listp[sl_ind] = freeBlock; 
}      

/* Remove a free block from the free list. */
/* 
FROM:
 [Block N-1]<-->[BLOCK N]<-->[BLOCK N+1]<-->....
TO:
 [Block N-1]<-->[BLOCK N+1]<-->....
*/
 static void removeFreeBlock(blkhdr* freeBlock) { 	
  blkhdr *nextFree, *prevFree;
  // store next/prev pointers of freeblock to reset links
  nextFree = freeBlock->next_p;
  prevFree = freeBlock->prev_p;
  // find 
  int sl_ind = findSegListInd(get_size(freeBlock));
  /*[FLP/Block]<->[_____]*/
  if (nextFree == NULL && prevFree ==NULL) {
    free_listp[sl_ind] = NULL;
    end_listp[sl_ind]  = NULL;
  /*[-----]<->[Block]<->[_____]*/
  }else if(prevFree != NULL && nextFree == NULL){
    prevFree->next_p = NULL;
    end_listp[sl_ind]        = prevFree;
  /*[FLP/Block]<->[-----]*/
  }else if(prevFree == NULL && nextFree != NULL){
   free_listp[sl_ind] = nextFree;
   nextFree->prev_p = NULL; 
  /*[-----]<->[Block]<->[-----]*/
  }else{
    prevFree->next_p  = nextFree;    
    nextFree->prev_p  = prevFree;    
  }
  return;
}
