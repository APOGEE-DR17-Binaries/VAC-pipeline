#!/bin/bash
#SBATCH -J apogee-run
#SBATCH -o logs/apogee-run.o%j
#SBATCH -e logs/apogee-run.e%j
#SBATCH -N 8
#SBATCH --ntasks-per-node=56
#SBATCH -t 36:00:00
#SBATCH -p cca
#SBATCH --constraint=rome

# Setup Python environment
source ~/.bash_profile
init_conda
conda activate dr17-binaries

# Relocate and initialize shell
cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries/vac-pipeline
source hq-config/init.sh
echo $HQ_RUN_PATH

cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries

date

mpirun python3 -m mpi4py.run -rc thread_level='funneled' \
$CONDA_PREFIX/bin/hq run_thejoker -v --mpi

date

