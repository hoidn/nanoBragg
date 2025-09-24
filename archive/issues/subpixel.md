discrepancy between pytorch and reference C, possibly because of problem in subpixel handling. command to reproduce: 
Command: -default_F 100 -cell 100 100 100 90 90 90 -N 5 -detpixels 256 -distance 50 - lambda 1.0 # shows signs of aliasing in pytorch output
