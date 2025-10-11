/* Extract from nanoBragg.c lines 3820-3868 and 4143-4185 */

/* ============================================================
   RNG Core Implementation (ran1 - Minimal Standard LCG with shuffle)
   Lines 4143-4185
   ============================================================ */

/* returns a uniform random deviate between 0 and 1 */
#define IA 16807
#define IM 2147483647
#define AM (1.0/IM)
#define IQ 127773
#define IR 2836
#define NTAB 32
#define NDIV (1+(IM-1)/NTAB)
#define EPS 1.2e-7
#define RNMX (1.0-EPS)

float ran1(long *idum)
{
    int j;
    long k;
    static long iy=0;
    static long iv[NTAB];
    float temp;

    if (*idum <= 0 || !iy) {
        /* first time around.  don't want idum=0 */
        if(-(*idum) < 1) *idum=1;
        else *idum = -(*idum);

        /* load the shuffle table */
        for(j=NTAB+7;j>=0;j--) {
            k=(*idum)/IQ;
            *idum=IA*(*idum-k*IQ)-IR*k;
            if(*idum < 0) *idum += IM;
            if(j < NTAB) iv[j] = *idum;
        }
        iy=iv[0];
    }
    /* always start here after initializing */
    k=(*idum)/IQ;
    *idum=IA*(*idum-k*IQ)-IR*k;
    if (*idum < 0) *idum += IM;
    j=iy/NDIV;
    iy=iv[j];
    iv[j] = *idum;
    if((temp=AM*iy) > RNMX) return RNMX;
    else return temp;
}

/* ============================================================
   Mosaic Rotation Implementation (uses ran1 for axis+angle sampling)
   Lines 3820-3868
   ============================================================ */

double *mosaic_rotation_umat(float mosaicity, double umat[9], long *seed)
{
    float ran1(long *idum);
    double r1,r2,r3,xyrad,rot;
    double v1,v2,v3;
    double t1,t2,t3,t6,t7,t8,t9,t11,t12,t15,t19,t20,t24;
    double uxx,uxy,uxz,uyx,uyy,uyz,uzx,uzy,uzz;

    /* make three random uniform deviates on [-1:1] */
    r1= (double) 2.0*ran1(seed)-1.0;
    r2= (double) 2.0*ran1(seed)-1.0;
    r3= (double) 2.0*ran1(seed)-1.0;

    xyrad = sqrt(1.0-r2*r2);
    rot = mosaicity*powf((1.0-r3*r3),(1.0/3.0));

    v1 = xyrad*sin(M_PI*r1);
    v2 = xyrad*cos(M_PI*r1);
    v3 = r2;

    /* commence incomprehensible quaternion calculation */
    t1 =  cos(rot);
    t2 =  1.0 - t1;
    t3 =  v1*v1;
    t6 =  t2*v1;
    t7 =  t6*v2;
    t8 =  sin(rot);
    t9 =  t8*v3;
    t11 = t6*v3;
    t12 = t8*v2;
    t15 = v2*v2;
    t19 = t2*v2*v3;
    t20 = t8*v1;
    t24 = v3*v3;

    /* populate the unitary rotation matrix */
    umat[0] = uxx = t1 + t2*t3;
    umat[1] = uxy = t7 - t9;
    umat[2] = uxz = t11 + t12;
    umat[3] = uyx = t7 + t9;
    umat[4] = uyy = t1 + t2*t15;
    umat[5] = uyz = t19 - t20;
    umat[6] = uzx = t11 - t12;
    umat[7] = uzy = t19 + t20;
    umat[8] = uzz = t1 + t2*t24;

    /* return pointer to the provided array, in case that is useful */
    return umat;
}
