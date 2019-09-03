#include <stdio.h>
/* 
 * evenBits - return word with all even-numbered bits set to 1
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 8
 *   Rating: 1
 */
 int evenbits(void){
 	// initiate 2 byte variable x so that all even-numbered bits are set to 1
 	// shift x by 8 bit intervals and compare it too itself with or statement to incrementally
 	// to fill all other even-numbered bits of 4 byte int with 1.
	int x = 0x55,bits = 8;
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
  int x = 0x80 << 24;
  x = ~x;
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
	int resp = !(x ^ y) | y;
    return resp;
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
	int x_eval = 0x80 << 24, negoff = 0x00;
	x_eval = ~(x_eval & x);
	x_eval = ((x_eval >> 30)+1) >> 1;
	negoff = (~negoff ^ x_eval)+1;	
	int resp = (x +(x_eval << n) + negoff) >> n;
    return resp;
}
/* 
 * isNegative - return 1 if x < 0, return 0 otherwise 
 *   Example: isNegative(-1) = 1.
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 6
 *   Rating: 2
 */
int isNegative(int x) {
	// 
	int s_eval = 0x80 << 24;
	s_eval = (s_eval & x);
	s_eval = (~(s_eval) >> 30);
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
 	// evaluate x to see if it is positive [if yes return 0x00,if no return 0xffffffff]
 	//     - evaluate x to see if it is < 0 
 	//     - Shift to the right by 31 so that if negative returns 0xffffffff, if positive returns 0x00
 	//
 	// perform (x & y) | (~x & z) --> will return y if x = mask, will return z if x = 0x00
	int c_eval = ~(!x)+1;
	c_eval = (~c_eval & y) | (c_eval & z);
  return c_eval;
}
/* 
 * absVal - absolute value of x
 *   Example: absVal(-1) = 1.
 *   You may assume -TMax <= x <= TMax
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 10
 *   Rating: 4
 */
int absVal(int x) {
  int s_eval = 0x80 << 24,negoff;
  s_eval = (s_eval & x);
  s_eval = (~(s_eval) >> 31);
  negoff = !s_eval;
  return (~s_eval^x)+negoff;
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
	int nullv = 0x00;
	int neg_n = ~nullv^(n+~nullv);
	int newx  = x << (32 + neg_n);
	int shift = (32 + neg_n);
	int maskx = (~nullv << shift) +!n;
	x = (x >> n);
	x = (x&~maskx);
	x = x | newx;
  return x;
}
/* 
 * bang - Compute !x without using !
 *   Examples: bang(3) = 0, bang(0) = 1
 *   Legal ops: ~ & ^ | + << >>
 *   Max ops: 12
 *   Rating: 4 
 */
int bang(int x) {
	int ix = ~x;
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
  int neg = ~(0x80 << 24);
  int puf  = neg & uf;	
  if ((puf>>23) == (neg>>23) && !(puf<<9)){
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
  int mask1  = 1;
  int pexp  = 0x80000000;        // used to determine xexp
  int s     = 0;
  int Moff  = 0; 
  int Rndt1 = 1;                 // Used to determine Mantissa rounding
  int Rndlf = 1;                 // Used to determine Mantissa rounding
  int Rndtr = 0x80000000;        // Used to determine Mantissa rounding
  int Mflg  = 0;                 // Used to determine Mantissa rounding

  if (!x){
  	return 0;
  }
  if (x < 0){
  	s = negf;
  	x = ~x + 1;
  }
  while (!(pexp & x)){
  	pexp = pexp >> 1;
  	xexp -= 1;    // Find index of leading bit
  }
  Moff = 23 - xexp;  // Find offset from start of Mantissa
  printf("%.8x\n",(x));
  M = x & ~pexp;  // Mask the leading exp in front of the Mantissa
  if(Moff >= 0){
  	M = M << Moff;    // Mantissa val
  }
  else{
  		Moff = -Moff;
  		Rndlf = (Rndlf<<Moff);     //evaluate for rounding
  		Rndt1 = (Rndlf>>1);        //evaluate for rounding
		Rndtr = ~(pexp>>24);      //evaluate for rounding
    printf("%d\n",Rndtr);
    printf("%.8x\n",Moff);
    printf("%.8x\n",(Rndlf ^ ~Rndtr));
    printf("%.8x\n",Mflg);
		Mflg  = (Rndt1 & x) && ((Rndlf | Rndtr) & x); 
    printf("%.8x\n",(Rndt1 && (Rndlf | Rndtr) & x) );
    printf("%.8x\n",Mflg);
		M = M >> Moff;	
		M = (M + Mflg);
  		xexp += M == 0x00800000;
  		M = (M & 0x007fffff);
  }
  fexp = (fexp + xexp);
  fexp = fexp << 23;
  return s | fexp | M;
}
int main(void){

/*  EVEN BITS
	int resp = evenbits();
	printf("%.8x\n",resp);
*/

/* BIT NOR
	int x = 0x6,y =0x5;
	int resp = bitNor(x,y);
*/

//  T MAX	
/*	int r = tmax();
	printf("%.8x\n",r);
*/

/*  IMPLICATIONS
	int x = 0,y = 0;
	int resp = implication(x,y);
	printf("%.8x\n",resp);
*/

/*	DIV PWR 2
	int x = 20,n = 0;
	int resp = divpwr2(x,n);
	printf("%d\n",resp);
*/

/*  IS NEGATIVE
	int x = 1;
	int resp = isNegative(x);
	printf("%.8x\n",resp);
*/

/*	ABS VAL
	int resp = absVal(2);
	printf("%d\n",resp);
*/

/*  CONDITIONS
	int resp = conditional(0,3,5);
	printf("%d\n",resp);
*/

//  rotateRight
	//int resp = rotateRight(0x80000000,0);
	//printf("%.8x\n",resp);

//  BANG
//	int resp = bang(0);
//	printf("%d\n",resp);


// FLOAT ABS
/*
	unsigned ui = 5
	unsigned resp = float_abs(ui);
	printf("%x\n",resp);
*/
// FLOAT PWR2
//	int x = -150;
//	printf("%.8x\n",x);
//	int resp = float_pwr2(x);
//	printf("%.8x\n",resp);

	int x = 0x7f0ffff;//0x7fffff; //0x0fffffff;//0x8000000f;////0x8000000f;////0000000;
	printf("%d\t",x); 
	printf("%.8x\n",x); 

	int resp = float_i2f(x);
	printf("\n%.8x\n",resp); 
}
