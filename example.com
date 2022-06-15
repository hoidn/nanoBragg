#! /bin/tcsh -f
#
#
#
set time

pdbset xyzin lysozyme.pdb xyzout bigcell.pdb << EOF > /dev/null
CELL 250 250 250 90 90 90
SPACEGROUP 1 
EOF


phenix.fmodel bigcell.pdb high_resolution=10 k_sol=0.35 b_sol=46.5 mask.solvent_radius=0.5 mask.shrink_truncation_radius=0.16

./mtz_to_P1hkl.com bigcell.pdb.mtz

./fastBragg -cell 250 250 250 90 90 90 -misset 10 20 30 -hkl P1.hkl -lambda 1 -distance 1000 -detsize 100 -fluence 1e32 -N 1

