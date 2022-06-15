#! /bin/tcsh -f
#
#	retrieve CIF data from the PDB, convert it to MTZ format
#
#

foreach pdbID ( $* )

set SG = ""

set pdbid = `echo $pdbID | awk '{print tolower($1)}'`
set PDBID = `echo $pdbID | awk '{print toupper($1)}'`

if(-s ${pdbid}.mtz) then
    set test = `ls -l ${pdbid}.mtz | awk '{print ($5>1000)}'`
    if($test) then
        echo "already got ${pdbid}.mtz"
        exit
    endif
endif

set pdbin = ${pdbid}.pdb
if(! -e "$pdbin") then
    getpdb.com $pdbid >! $pdbin
endif
if(! -s "$pdbin") then
    set ID = `echo $pdbid | awk '{print toupper($1)}'`
    wget -O test.gz http://www.rcsb.org/pdb/files/${ID}.pdb.gz > /dev/null
    gunzip test.gz
    mv test $pdbin
endif

if(-e ${pdbid}_orig.cif) cp -p ${pdbid}_orig.cif ${pdbid}.cif
if(! $?NOCACHE && -s /data3/jamesh/all_sf/${pdbid}.cif) then
    cp -p /data3/jamesh/all_sf/${pdbid}.cif ${pdbid}.cif
endif
if(! $?NOCACHE && -s /data3/jamesh/all_sf/${pdbid}_orig.cif) then
    cp -p /data3/jamesh/all_sf/${pdbid}_orig.cif ${pdbid}_orig.cif
endif
if(! -s ${pdbid}.cif) then
    # check to see if there IS experimental data?
    wget -O ${pdbid}.cif 'http://www.rcsb.org/pdb/download/downloadFile.do?fileFormat=STRUCTFACT&compression=NO&structureId='$PDBID > /dev/null
    if(! -s ${pdbid}.cif) then
	set BAD = "no cif available."
	goto exit
    endif
endif


set CELL = `awk '/^CRYST1/{print $2,$3,$4,$5,$6,$7;exit}' ${pdbid}.pdb`
if("$SG" == "") then
    set pdbSG = `awk '/^CRYST1/{SG=substr($0,56,14);if(length(SG)==14)while(gsub(/[^ ]$/,"",SG));print SG;exit}' ${pdbid}.pdb | head -1`
    if("$pdbSG" == "R 32") set pdbSG = "R 3 2"
#    if("$pdbSG" == "P 21") set pdbSG = "P 1 21 1"
#    if("$pdbSG" == "A 2") set pdbSG = "A 1 2 1"
    if("$pdbSG" == "I 21") set pdbSG = "I 1 21 1"
    if("$pdbSG" == "A 1") set pdbSG = "P 1"
    if("$pdbSG" == "P 21 21 2 A") set pdbSG = "P 21 21 2"
    if("$pdbSG" == "P 1-") set pdbSG = "P -1"
    if("$pdbSG" == "R 3 2" && $CELL[6] == 120.00) set pdbSG = "H 3 2"
    if("$pdbSG" == "R 3" && $CELL[6] == 120.00) set pdbSG = "H 3"
    set SG = `awk -v pdbSG="$pdbSG" -F "[\047]" 'pdbSG==$2 || pdbSG==$4{print;exit}' ${CLIBD}/symop.lib | awk '{print $4}'`
endif
if("$SG" == "") set SG = "$pdbSG"


# does not seem to matter
#set STATUS = "STATUS XPLOR"
#set STATUS = "STATUS CCP4"

set retries = 0
again:
@ retries = ( $retries + 1 )
egrep "^CRYST1" ${pdbid}.pdb
echo "CELL $CELL"
echo "SYMM $SG"  
cif2mtz hklin ${pdbid}.cif hklout ${pdbid}.mtz << EOF >&! ${pdbid}_cif2mtz.log 
CELL $CELL
SYMM "$SG"
EOF
if($status) then
    if($retries > 10) then
	set BAD = "too many retries "
	goto exit
    endif
    if(! -e ${pdbid}_orig_cif2mtz.log) cp ${pdbid}_cif2mtz.log ${pdbid}_orig_cif2mtz.log
    if(! -e ${pdbid}_orig.cif) cp ${pdbid}.cif ${pdbid}_orig.cif
    set test = `awk '/_diffrn.detail[^s]/' ${pdbid}_cif2mtz.log | wc -l`
    if("$test" != 0) then
	echo "renaming detail to details in cif file..."
	awk '{gsub(/_diffrn.detail[^s]/,"_diffrn.details");print}'  ${pdbid}_orig.cif >! new.cif
	mv new.cif ${pdbid}.cif
	goto again
    endif
    if(! $?TRIED_CLEAN) then
	set TRIED_CLEAN
	echo "attempting to clean up cif file..."
	cat ${pdbid}.cif |\
	awk '{gsub("[^[:print:]]",""); print}' |\
	awk '/^loop_/{loop=NR;next} \
	   loop && /^_refln\./{++r;next} \
	   loop && ! (NF==r || NF==0 || /^#/){print loop,r,h;loop=r=h=0} \
	   NF==r || NF==0 || /^#/{++h} END{print loop,r,h}' |\
	sort -k3gr >! loops.txt
	set bigloop = `head -1 loops.txt | awk '{print $1}'`
	set columns = `head -1 loops.txt | awk '{print $2}'`
	set lines   = `head -1 loops.txt | awk '{print $2+$3+2}'`
	echo "refln loop at line $bigloop has $lines lines"
	egrep "^data" ${pdbid}.cif | head -1 >! new.cif
	tail -n +$bigloop ${pdbid}.cif |\
	head -n $lines |\
	awk -v columns=$columns '/^loop/ || /_refln/ || NF==columns' |\
	cat >> new.cif
	mv new.cif ${pdbid}.cif
	goto again
    endif
    set test = `awk '/Unexpected context type for category /' ${pdbid}_cif2mtz.log | wc -l`
    if("$test" != 0) then
	set badlabel = `awk -F "'" '/not defined in dictionary/{print $4}' ${pdbid}_cif2mtz.log | head -1`
	set badstring = `echo $badlabel | awk -F "." '{print $NF}'`
	awk -F "." '/^_refl/{print $2,"USED"}' ${pdbid}.cif >! used_labels.txt
	strings ${CLIB}/cif_mmdic.lib | awk -F "." '/^_refln\./{print $NF}' >! okay_labels.txt
	cat used_labels.txt okay_labels.txt |\
	awk '$2=="USED"{++used[$1];next} {n=split($1,w,"_");for(l in used){\
		m=split(l,x,"_");matches=0;for(i in w)for(j in x){if(w[i]==x[j])++matches};\
	    if(matches) print matches,length($1),l,$1}}' |\
	sort -k1g -k2gr >! matches.txt
	# use most obscure label possible
	set betterstring = `grep "$badstring" matches.txt | head -1 | awk '{print $NF}'`
	set betterstring = A_calc
	if("$badstring" != "" && "$betterstring" != "") then
            echo "renaming $badstring to $betterstring in cif file..."
            awk -v badstring=$badstring -v betterstring=$betterstring '{\
	        gsub(badstring,betterstring);print}' ${pdbid}.cif >! new.cif
	    mv new.cif ${pdbid}.cif
            goto again
	endif
    endif
    set test = `awk '/Syntax error at line /' ${pdbid}_cif2mtz.log | wc -l`
    if("$test" != 0) then
        set badlines = `awk '/Syntax error at line /{print $5+0}' ${pdbid}_cif2mtz.log`
	echo "removing lines $badlines from cif file..."
        echo "$badlines" | cat - ${pdbid}.cif |\
          awk 'NR==1{for(i=1;i<=NF;++i)++bad[$i];next} ! bad[NR-1]{print}' |\
        cat >! new.cif
	mv new.cif ${pdbid}.cif
	goto again
    endif
    set BAD = "unknown problem"
    goto exit
endif

# sanitize with cad
echo labin file 1 all | cad hklin1 ${pdbid}.mtz hklout sane.mtz > /dev/null
mv sane.mtz ${pdbid}.mtz




# check for structure factors?
mtzdmp ${pdbid}.mtz | tee mtzdmp.log |\
awk '/OVERALL FILE STATISTICS/,/No. of reflections used/' |\
awk 'NF>8 && $(NF-1) ~ /[DFGHIJLPQW]/' |\
tee columns.txt |\
awk '{++n}\
     $(NF-1) ~ /^[FJGK]$/ || ($(NF-1) == "R" && $NF ~ /^[IF]/){\
        ++ds;line[ds]=n;t[ds]=$(NF-1);I[ds]=$NF; meanI[ds]=$(NF-4)} \
     $(NF-1) ~ /^[QLM]$/ || $NF ~ /^SIG/{\
        S=$NF; for(ds in I){\
           if(S=="SIG"I[ds] || S=="SIG"substr(I[ds],2) || n==line[ds]+1){\
         SNR=0;sig=$(NF-4)+0; if(sig) SNR = meanI[ds]/sig;\
         reso=$(NF-2);comp=substr($0,32)+0\
         print I[ds], S, t[ds],reso, comp, SNR;}}}' |\
sort -k3n,4 -k4nr,5 -k5nr |\
awk -v ID=$pdbid '{++seen[$1]} /[\(\\+\-]/ && seen[$1]{next} {print ID,$0}' |\
tee datasets.txt
# format: I SIGI ctyp reso completeness  signal/noise

set test = `cat datasets.txt | wc -l`
if("$test" == "0") then
    cat columns.txt |\
    awk '{++n}\
     $(NF-1) ~ /^[FJGK]$/ || ($(NF-1) == "R" && $NF ~ /^[IF]/){\
           print $NF, "x", $(NF-1),$(NF-2), substr($0,32)+0, "x";}' |\
    sort -k3n,4 -k4nr,5 -k5nr |\
    awk -v ID=$pdbid '{++seen[$1]} /[\(\\+\-]/ && seen[$1]{next} {print ID,$0}' |\
    tee datasets.txt
endif

cat mtzdmp.log |\
awk '/OVERALL FILE STATISTICS/,/No. of reflections used/' |\
awk 'NF>10 && $(NF-1) ~ /[I]/' |\
awk -v ID=$pdbid '{++n}\
     $(NF-1) ~ /^[I]$/ || tolower($NF) ~ /free/{\
         mean=$(NF-4);reso=$(NF-2);comp=substr($0,32)+0\
         print ID, $NF ,reso, comp, mean;}' |\
tee freestuff.txt


set F = `awk '$4=="F"{print $2,$3}' datasets.txt`
if("$F" == "" && ! $?NO_TRUNCATE) then
    set I = `awk '$4=="J"{print $2,$3}' datasets.txt`
    echo "truncating $I to FP"
    truncate hklin ${pdbid}.mtz hklout truncated.mtz << EOF >&! ${pdbid}_truncate.log
truncate yes
labin IMEAN=$I[1] SIGIMEAN=$I[2]
labout F=FP SIGF=SIGFP
EOF
    cad hklin1 ${pdbid}.mtz hklin2 truncated.mtz hklout new.mtz << EOF >> /dev/null
labin file 1 all
labin file 2 E1=FP E2=SIGFP
EOF
    mv new.mtz ${pdbid}.mtz
    rm -f truncated.mtz
endif

set sigF = `awk '$4=="F"{print $3}' datasets.txt`
if("$sigF" == "x") then
    echo "no sigma!  adding one..."
    set F = `awk '$4=="F"{print $2}' datasets.txt`
    rm -f new.mtz
    sftools << EOF > /dev/null
    read ${pdbid}.mtz
    calc Q col SIG$F = 0.1
    write new.mtz
    y
    exit
    y
EOF
    if(-s new.mtz) then
        mv new.mtz ${pdbid}.mtz
    else
	echo "failed... "
    endif
endif



set free = `awk '$NF+0<1 && $NF+0>0{print $2;exit}' freestuff.txt`
if("$free" == "" && ! $?NO_FREE) then
    echo "adding FreeR_flag"
    uniqueify ${pdbid}.mtz >& /dev/null
    mv ${pdbid}-unique.mtz ${pdbid}.mtz
endif

rm -f mtzdmp.log columns.txt datasets.txt freestuff.txt



exit:
if($?BAD) then
    echo "ERROR: $pdbid $BAD"
    if(! $?allBAD) set allBAD
    set allBAD = "$allBAD $BAD"
    unset BAD
    continue
endif
echo "OK ${pdbid}"

end

if($?allBAD) then
    echo "ERROR: $allBAD"
    exit 9
endif
exit

#######################################################################################
#
#	notes and tests...
#

foreach oddball ( `awk '{print NR}' ~jamesh/pdb/snapshot/oddball_SGs.txt` )
    set pdbSG = `awk -v line=$oddball 'NR==line' ~jamesh/pdb/snapshot/oddball_SGs.txt`

	grep "$pdbSG" ~jamesh/pdb/snapshot/CRYST1.txt |\
	 awk '{print $1, "SELECT"}' |\
	cat - ~jamesh/pdb/snapshot/all_exp_data.txt |\
	awk '{$1=tolower($1)} /SELECT/{++selected[$1];next} selected[$1]{print}' |\
	head -10 >! tempfile.txt
	set pdbids = `cat tempfile.txt`
	echo "$pdbSG --> $pdbids" | tee -a example_oddballs.txt
    if($#pdbids > 0) then
        rm -f ${pdbids[1]}.mtz
        getcif.com $pdbids[1]
    endif
end

cp ~jamesh/pdb/snapshot/all_exp_data.txt pdb_list.txt

rm -f getcif_all.log
foreach pdbid ( `awk '{print tolower($1)}' pdb_list.txt` )

    rm ${pdbid}.mtz
    rm -f ${pdbid}.cif
    rm -f ${pdbid}_orig_cif2mtz.log
    echo "TRYING $pdbid" | tee -a getcif_all.log
    getcif.com $pdbid | tee -a getcif_all.log

end

ls -1rt *_orig.cif | awk -F "_" '{print $1}' | tee baddies.txt

