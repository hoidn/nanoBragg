#! /bin/tcsh -f
#
#	convert the first F in an MTZ file into a radially-averaged amorphous "F"
#	for use in simulating SAXS patterns with nonBragg
#
#		James Holton 4-4-14
#
#
set mtzfile = "$1"
set bs = 0.001

foreach arg ( $* )
    if("$arg" =~ *.mtz) set mtzfile = "$arg"
    if("$arg" =~ bs=*) set bs = `echo $arg | awk -F "=" '{print $2+0}'`
end


if(! -e "$mtzfile") then
    if("$mtzfile" != "") echo "$mtzfile does not exist"
    cat << EOF
usage: $0 mtzfile.mtz
EOF
    exit 9
endif

set tempfile = ${CCP4_SCR}/tmp_dump$$

set firstF = `mtzdmp $mtzfile | grep -v "H H H " | grep "$2" | awk 'NF>5 && $(NF-1)=="F"{print $NF;exit}'`
if("$firstF" == "") then
    echo "ERROR: cannot find any Fs in $mtzfile"
    exit 9
endif
echo "selected $firstF"

cad hklin1 $mtzfile hklout ${tempfile}.mtz << EOF > /dev/null
labin file 1 E1=$firstF
EOF

echo "averaging with bin size = $bs sin(theta)/lambda"

echo "FORMAT '(3i6,2g40.20)'\nlreso\nnref -1" |\
mtzdump hklin ${tempfile}.mtz |\
awk 'substr($0,1,18)==sprintf("%6d%6d%6d",$1,$2,$3) && $4!="?"{\
      print sqrt($4/4),$5}' |\
awk -v bs=$bs '{bin=sprintf("%.0f",$1/bs);sum[bin]+=$2*$2;++count[bin]}\
     END{for(bin in sum) print bin*bs,sqrt(sum[bin]/count[bin])}' |\
sort -g |\
cat >! mtz.stol 
rm -f ${tempfile}.mtz

set count = `cat mtz.stol | wc -l`
echo "$count stol F lines output to mtz.stol"


