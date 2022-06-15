#! /bin/tcsh -f
#
#	create random unitary orientation matricies with a given "spread"    -James Holton
#	employs a quaternion formalism I found on the internet.
#	simulates mosaic spread
#

# input "mosaic spread" and "number of matricies"

echo  $1 $2 |\
awk '{pi=atan2(1,0)*2;RTD=180/pi;\
  mos=$1/RTD;n=$2;srand($3)\
  for(i=1;i<=n;++i){\
    r1=2*rand()-1;\
    r2=2*rand()-1;\
    r3=2*rand()-1;\
    #for(r1=-1;r1<=1;r1+=0.1)for(r2=-1;r2<=1;r2+=0.1)for(r3=-1;r3<=1;r3+=0.1){\
    xyrad=sqrt(1-r2**2);\
    rot = mos*(1-r3**2)**(1./3.);\
    v1=xyrad*sin(pi*r1);v2=xyrad*cos(pi*r1);v3=r2;\
    t1 =  cos(rot);\
    t2 =  1 - t1;\
    t3 =  v1*v1;\
    t6 =  t2*v1;\
    t7 =  t6*v2;\
    t8 =  sin(rot);\
    t9 =  t8*v3;\
    t11 = t6*v3;\
    t12 = t8*v2;\
    t15 = v2*v2;\
    t19 = t2*v2*v3;\
    t20 = t8*v1;\
    t24 = v3*v3;\
    R[1, 1] = t1 + t2*t3;\
    R[1, 2] = t7 - t9;\
    R[1, 3] = t11 + t12;\
    R[2, 1] = t7 + t9;\
    R[2, 2] = t1 + t2*t15;\
    R[2, 3] = t19 - t20;\
    R[3, 1] = t11 - t12;\
    R[3, 2] = t19 + t20;\
    R[3, 3] = t1 + t2*t24;\
    print i,R[1,1],R[1,2],R[1,3];\
    print i,R[2,1],R[2,2],R[2,3];\
    print i,R[3,1],R[3,2],R[3,3];\
}}' 


exit

