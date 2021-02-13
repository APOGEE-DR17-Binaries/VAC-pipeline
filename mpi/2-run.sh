#!/bin/bash
#SBATCH -J apogee-run
#SBATCH -o logs/apogee-run.o%j
#SBATCH -e logs/apogee-run.e%j
#SBATCH -N 16
#SBATCH -t 72:00:00
#SBATCH -p cca
#SBATCH --constraint=skylake

source ~/.bash_profile
init_conda
conda activate dr17-binaries
echo $HQ_RUN_PATH

cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries

date

mpirun python3 -m mpi4py.run -rc thread_level='funneled' \
$CONDA_PREFIX/bin/hq run_thejoker -v --mpi

date

