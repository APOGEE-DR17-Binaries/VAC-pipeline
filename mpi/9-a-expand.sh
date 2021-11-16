#!/bin/bash
#SBATCH -J apogee-expamd
#SBATCH -o logs/apogee-expand.o%j
#SBATCH -e logs/apogee-expand.e%j
#SBATCH -N 6
#SBATCH -t 12:00:00
#SBATCH -p cca
#SBATCH --constraint=rome

# Relocate and initialize shell
cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries/vac-pipeline
source hq-config/init.sh
echo $HQ_RUN_PATH

date

mpirun python3 -m mpi4py.run -rc thread_level='funneled' \
$CONDA_PREFIX/bin/hq expand_samples -v --mpi

date

