#!/bin/bash

set -e

### [-s] python script to run
### [-t] number of processes
### [-p] work dir   ('.../run.tag.remarks')
### [-q] queue name
### [-y] submit type, PBS/LSF/None


while getopts "t:s:p:q:y:" arg; do
	case $arg in
		t)
			pnum=$OPTARG
			;;
		s)
			script=$OPTARG
			;;
		p)
			workdir=$OPTARG
			;;
		q)
			queue=$OPTARG
			;;
		y)
			jss=$OPTARG
			;;
		z)
			pbs_pnn=$OPTARG
			;;
		*)
			exit 1
			;;
	esac
done

jobname=${workdir##*/}
### submit file
SFILE=${workdir}/submit.sh
if [ -e $SFILE ]; then
	rm -rf $SFILE
fi

if [ "$jss"x = "PBS"x ]; then
	### different in different HPC system
	if [ -z pbs_pnn ]; then
		n_ppn=24
	else
		n_ppn=$pbs_pnn
	fi
	n_node=$[$pnum/$n_ppn+1]
	### submit command
	SUB="mpirun -n $pnum python -W ignore $script runtime.json config.ini 1>${jobname}.out 2>${jobname}.err"
	### qsub -e ${jobname}.err -o ${jobname}.out -N $jobname -l nodes=$n_node:ppn=$n_ppn
	### write to workdir
	echo "#!/bin/bash" >> $SFILE
	echo "#PBS -N ${jobname}" >> SFILE
	echo "#PBS -q low" >> SFILE
	echo "#PBS -j oe"
	echo "#PBS -o ${jobname}.joinLog"
	echo "#PBS -l nodes=${n_node}:ppn=${n_ppn}"
	echo "cd $PBS_O_WORKDIR" >> $SFILE
	echo $SUB >> $SFILE
	### print exec cmd and will be scratched by jobcenter
	echo "qsub submit.sh"
	exit 0

elif [ "$jss"x = "LSF"x ]; then
	### submit command
	SUB="bsub -q $queue -o ${jobname}.out -e ${jobname}.err -J ${jobname} -n $pnum mpirun -n $pnum python -W ignore $script runtime.json config.ini"
	### write to workdir
	echo "#!/bin/bash" >> $SFILE
	echo $SUB >> $SFILE
	### chmow and print exec cmd
	chmod u+x $SFILE
	echo "./submit.sh"
	exit 0

else
	### submit directly
	SUB="mpirun -n $pnum python -W ignore $script runtime.json config.ini 1>${jobname}.out 2>${jobname}.err"
	### write to workdir
	echo "#!/bin/bash" >> $SFILE
	echo $SUB >> $SFILE
	### chmow and print exec cmd
	chmod u+x $SFILE
	echo "./submit.sh"
	exit 0

fi