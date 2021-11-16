#!/bin/bash
#SBATCH -J apogee-const
#SBATCH -o logs/apogee-const.o%j
#SBATCH -e logs/apogee-const.e%j
#SBATCH -N 5
#SBATCH -t 24:00:00
#SBATCH -p cca
#SBATCH --constraint=rome

# Relocate and initialize shell
cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries/vac-pipeline
source hq-config/init.sh
echo $HQ_RUN_PATH

date

mpirun python3 -m mpi4py.run -rc thread_level='funneled' \
$CONDA_PREFIX/bin/hq run_constant -v --mpi

date
