/*
 * CS:APP Data Lab
 *
 * Max Maguire
 *
 * bits.c - Source file with your solutions to the Lab.
 *          This is the file you will hand in to your instructor.
 *
 * WARNING: Do not include the <stdio.h> header; it confuses the dlc
 * compiler. You can still use printf for debugging without including
 * <stdio.h>, although you might get a compiler warning. In general,
 * it's not good practice to ignore compiler warnings, but in this
 * case it's OK.
 */

#if 0
/*
 * Instructions to Students:
 *
 * STEP 1: Read the following instructions carefully.
 */

You will provide your solution to the Data Lab by
editing the collection of functions in this source file.

INTEGER CODING RULES:

  Replace the "return" statement in each function with one
  or more lines of C code that implements the function. Your code
  must conform to the following style:

  int Funct(arg1, arg2, ...) {
      /* brief description of how your implementation works */
      int var1 = Expr1;
      ...
      int varM = ExprM;

      varJ = ExprJ;
      ...
      varN = ExprN;
      return ExprR;
  }

  Each "Expr" is an expression using ONLY the following:
  1. Integer constants 0 through 255 (0xFF), inclusive. You are
      not allowed to use big constants such as 0xffffffff.
  2. Function arguments and local variables (no global variables).
  3. Unary integer operations ! ~
  4. Binary integer operations & ^ | + << >>

  Some of the problems restrict the set of allowed operators even further.
  Each "Expr" may consist of multiple operators. You are not restricted to
  one operator per line.

  You are expressly forbidden to:
  1. Use any control constructs such as if, do, while, for, switch, etc.
  2. Define or use any macros.
  3. Define any additional functions in this file.
  4. Call any functions.
  5. Use any other operations, such as &&, ||, -, or ?:
  6. Use any form of casting.
  7. Use any data type other than int.  This implies that you
     cannot use arrays, structs, or unions.


  You may assume that your machine:
  1. Uses 2s complement, 32-bit representations of integers.
  2. Performs right shifts arithmetically.
  3. Has unpredictable behavior when shifting an integer by more
     than the word size.

EXAMPLES OF ACCEPTABLE CODING STYLE:
  /*
   * pow2plus1 - returns 2^x + 1, where 0 <= x <= 31
   */
  int pow2plus1(int x) {
     /* exploit ability of shifts to compute powers of 2 */
     return (1 << x) + 1;
  }

  /*
   * pow2plus4 - returns 2^x + 4, where 0 <= x <= 31
   */
  int pow2plus4(int x) {
     /* exploit ability of shifts to compute powers of 2 */
     int result = (1 << x);
     result += 4;
     return result;
  }

FLOATING POINT CODING RULES

For the problems that require you to implent floating-point operations,
the coding rules are less strict.  You are allowed to use looping and
conditional control.  You are allowed to use both ints and unsigneds.
You can use arbitrary integer and unsigned constants.

You are expressly forbidden to:
  1. Define or use any macros.
  2. Define any additional functions in this file.
  3. Call any functions.
  4. Use any form of casting.
  5. Use any data type other than int or unsigned.  This means that you
     cannot use arrays, structs, or unions.
  6. Use any floating point data types, operations, or constants.


NOTES:
  1. Use the dlc (data lab checker) compiler (described in the handout) to
     check the legality of your solutions.
  2. Each function has a maximum number of operators (! ~ & ^ | + << >>)
     that you are allowed to use for your implementation of the function.
     The max operator count is checked by dlc. Note that '=' is not
     counted; you may use as many of these as you want without penalty.
  3. Use the btest test harness to check your functions for correctness.
  4. Use the BDD checker to formally verify your functions
  5. The maximum number of ops for each function is given in the
     header comment for each function. If there are any inconsistencies
     between the maximum ops in the writeup and in this file, consider
     this file the authoritative source.

/*
 * STEP 2: Modify the following functions according the coding rules.
 *
 *   IMPORTANT. TO AVOID GRADING SURPRISES:
 *   1. Use the dlc compiler to check that your solutions conform
 *      to the coding rules.
 *   2. Use the BDD checker to formally verify that your solutions produce
 *      the correct answers.
 */


#endif
//1
/*
 * evenBits - return word with all even-numbered bits set to 1
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 8
 *   Rating: 1
 */
int evenBits(void) {
	/* Set x equal to a byte with even-numbered bits set to 1
	   Set twobytes equal to number of bits in twobytes
	   use 'or' statement to compare x with itself shifted over by 1,2 and 3 bytes
	   output: returns 8 byte int with all even-numbered bits set to 1
	   */
	int x = 0x55;
	x = x | (x << 8);
	x = x | (x << 16);
	return x;
}
/*
 * bitNor - ~(x|y) using only ~ and &
 *   Example: bitNor(0x6, 0x5) = 0xFFFFFFF8
 *   Legal ops: ~ &
 *   Max ops: 8
 *   Rating: 1
 */
int bitNor(int x, int y) {
	/*
	*/
  int resp = ~x & ~y;
  return resp;
}
/*
 * TMax - return maximum two's complement integer
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 4
 *   Rating: 1
 */
int tmax(void) {
  int x = 0x00;
  x = ~x ^ (~x << 31);
  return x;
}
//2
/*
 * implication - return x -> y in propositional logic - 0 for false, 1
 * for true
 *   Example: implication(1,1) = 1
 *            implication(1,0) = 0
 *   Legal ops: ! ~ ^ |
 *   Max ops: 5
 *   Rating: 2
 */
int implication(int x, int y) {
    int resp = x ^ y;
	return (!resp) | y;
}
/*
 * divpwr2 - Compute x/(2^n), for 0 <= n <= 30
 *  Round toward zero
 *   Examples: divpwr2(15,1) = 7, divpwr2(-33,4) = -2
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 15
 *   Rating: 2
 */
int divpwr2(int x, int n) {
	// s_eval evaluates int x: returns 1 if it is negative, returns 0 if it is positive
	//  initiate s_eval to be 32 binary number with first bit = 1
	// compare s_eval with x using & statement (positive# returns int = 0, negative returns original s_eval val)
	//  take inverse of s_eval and execut arithmatic shift to right by 30 bits
	//              (positive# returns int = -1, negative# returns int = 1)
	//  Add 1 to s_eval and shift to right 1 bit (positive # --> 0, negetiave# --> 1)
	//  Shift int x n spaces to the right and add s_eval (1 if negative, 0 if positive)
	int x_eval = 0x80 << 24, negoff = 0x00;
	x_eval = ~(x_eval & x);
	x_eval = ((x_eval >> 30)+1) >> 1;
	negoff = (~negoff ^ x_eval)+1;
	return (x +(x_eval << n) + negoff) >> n;
}
/*
 * isNegative - return 1 if x < 0, return 0 otherwise
 *   Example: isNegative(-1) = 1.
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 6
 *   Rating: 2
 */
int isNegative(int x) {
	// s_eval evaluates int x: returns 1 if it is negative, returns 0 if it is positive
	// initiate s_eval to be 32 binary number with first bit = 1
	// compare s_eval with x using & statement (positive# returns int = 0, negative returns original s_eval val)
	// take inverse of s_eval and execut arithmatic shift to right by 30 bits
	//      (positive# returns int = -1, negative# returns int = 1)
	//     Add 1 to s_eval and shift to right 1 bit (positive # --> 0, negetiave# --> 1)
  	int s_eval = 0x80 << 24;
	s_eval = (s_eval & x);
	s_eval = ~(s_eval) >> 30;
	s_eval = ((s_eval)+1) >> 1;
    return s_eval;
}
//3
/*
 * conditional - same as x ? y : z
 *   Example: conditional(2,4,5) = 4
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 16
 *   Rating: 3
 */
int conditional(int x, int y, int z) {
  	int c_eval = ~(!x)+1;
	c_eval = (~c_eval & y) | (c_eval & z);
  	return c_eval;
}
/*
 * rotateRight - Rotate x to the right by n
 *   Can assume that 0 <= n <= 31
 *   Examples: rotateRight(0x87654321,4) = 0x18765432
 *   Legal ops: ~ & ^ | + << >>
 *   Max ops: 25
 *   Rating: 3
 */
int rotateRight(int x, int n) {
  // store shift value in var shift (determined by n and nullv (0))
  // store end values in mask to carry over to front of 32 bit integer by "shift" values
  // shift the integer to the right by n
  int nullv = 0x00;
  int neg_n = ~nullv^(n+~nullv);
  int newx  = x << (32 + neg_n);
  int shift = (32 + neg_n);
  int maskx = (~nullv << shift) +!n;
  x = (x >> n);
  x = x&~maskx;
  x = x | newx;
  return x;
}
//4
/*
 * absVal - absolute value of x
 *   Example: absVal(-1) = 1.
 *   You may assume -TMax <= x <= TMax
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 10
 *   Rating: 4
 */
int absVal(int x) {
  // return only sign bit if it exists and shift it all the way to the right.
  // store +1 offset to be added based on if the s_eval is a number or 0.
  // Flip s_eval one more time and Nor it with x, adding the offset value.
  int s_eval = 0x80 << 24,negoff;
  s_eval = (s_eval & x);
  s_eval = (~(s_eval) >> 31);
  negoff = !s_eval;
  return (~s_eval^x)+negoff;
}
/*
 * bang - Compute !x without using !
 *   Examples: bang(3) = 0, bang(0) = 1
 *   Legal ops: ~ & ^ | + << >>
 *   Max ops: 12
 *   Rating: 4
 */
int bang(int x) {
  // take inverse of x + 1 and compare it with itself
  // only x = 0 will return +1 when incremented by 1
  int ix1 = ~x + 1;
  x = (x | ix1) >> 31;
  return (x+1);
}
//float
/*
 * float_abs - Return bit-level equivalent of absolute value of f for
 *   floating point argument f.
 *   Both the argument and result are passed as unsigned int's, but
 *   they are to be interpreted as the bit-level representations of
 *   single-precision floating point values.
 *   When argument is NaN, return argument..
 *   Legal ops: Any integer/unsigned operations incl. ||, &&. also if, while
 *   Max ops: 10
 *   Rating: 2
 */
unsigned float_abs(unsigned uf) {
  // Take positive mask of unsigned uf. Evaluate the sign bit to determine
  // which variable to return
  int neg = ~(0x80 << 24);
  int puf  = neg & uf;
  if ((puf>>23) == (neg>>23) && (puf<<9)){
      return uf;
  }
  return puf;
}
/*
 * float_pwr2 - Return bit-level equivalent of the expression 2.0^x
 *   (2.0 raised to the power x) for any 32-bit integer x.
 *
 *   The unsigned value that is returned should have the identical bit
 *   representation as the single-precision floating-point number 2.0^x.
 *   If the result is too small to be represented as a denorm, return
 *   0. If too large, return +INF.
 *
 *   Legal ops: Any integer/unsigned operations incl. ||, &&. Also if, while
 *   Max ops: 30
 *   Rating: 4
 */
unsigned float_pwr2(int x) {
    int neg  = (0x80 << 24);
    int fx   = 0x7f;
    int Mval = 0x01 << 23;
    int negl = ~0x9b; // lower than this returns 0
    int negf = ~0x7d; // below this adjusts Mantissa val
    if (x > fx){
       return ((neg>>8)& ~neg); // INF
    }
    if (x < negf){
       if(x < negl){
          return 0;
       }
       x = (~x + 1) + negf;
       return Mval >> x;  //Mantissa val (offset by x)
    }
    fx = ((fx + x) << 23);
    return fx;
}
/*
 * float_i2f - Return bit-level equivalent of expression (float) x
 *   Result is returned as unsigned int, but
 *   it is to be interpreted as the bit-level representation of a
 *   single-precision floating point values.
 *   Legal ops: Any integer/unsigned operations incl. ||, &&. also if, while
 *   Max ops: 30
 *   Rating: 4
 */
unsigned float_i2f(int x) {
  int fexp  = 0x7f;        // To calculate exp
  int xexp  = 31;          // exp will equal 2^xexp
  int M     = 0x00;        // declare var for Mantissa
  int negf  = 0x80000000;  // if negf, s = negf and make x pos
  int pexp  = 0x80000000;        // used to determine xexp
  int s     = 0;
  int Moff  = 0;
  int Rndt1 = 1;        // Used to determine Mantissa rounding
  int Rndlf = 1;        // Used to determine Mantissa
  int Rndtr = 0x80000000;        // Used to determine Mantissa rounding
  int Mflg  = 0;                 // Used to determine Mantissa rounding

  if (x == 0){
      return 0;  // return 0 if x = 0
  }
  if (x < 0){ // change s to negative  and switch x to abs value
       s = negf;
       x = ~x + 1;
  }
  while (!(pexp & x)){
        pexp = pexp >> 1;
        xexp -= 1;    // Find index of leading bit
  }
  Moff = 23 - xexp;  // Find offset from start of Mantissa
  M = x & ~pexp;  // Mask the leading exp in front of the Mantissa
  if(Moff >= 0){
      M = M << Moff;    // Mantissa val
   }
  else{
    Moff = -Moff;
    Rndlf = (Rndlf<<Moff);     //evaluate for rounding
    Rndt1 = (Rndlf>>1);        //evaluate for rounding
    Rndtr = ~(pexp>>24);      //evaluate for rounding
    Mflg  = (Rndt1 & x) && ((Rndlf | Rndtr) & x);
    M = (M >> Moff) + Mflg;
    xexp += M == 0x00800000;
    M = (M & 0x007fffff);
   }
  fexp = (fexp + xexp) << 23;
  return s | fexp | M;
}

