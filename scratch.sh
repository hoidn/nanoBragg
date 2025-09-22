 cd gsg && make nanoBragg_trace
 cd ..

python scripts/verify_detector_geometry.py

# baseline
gsg/nanoBragg_trace \
	-default_F 100 \
	-lambda 6.2 \
	-distance 100 \
	-pixel 0.1 \
	-detpixels 1024 \
	-Xbeam 51.25 \
	-Ybeam 51.25 \
	-cell 100 100 100 90 90 90 \
	-N 5 \
	-matrix identity.mat

# with rotation
gsg/nanoBragg_trace \
    -default_F 100 \
    -lambda 6.2 \
    -distance 100 \
    -pixel 0.1 \
    -detpixels 1024 \
    -Xbeam 51.25 \
    -Ybeam 51.25 \
    -cell 100 100 100 90 90 90 \
    -N 5 \
    -matrix identity.mat \
    -detector_rotx 5 \
    -detector_roty 3 \
    -detector_rotz 2 \
    -twotheta 15 \
    -pivot beam

pytest tests/


git grep diffuse

NANOBRAGG_TEST_DEVICE=cuda time pytest tests/test_gradients.py

time pytest tests/test_gradients.py
