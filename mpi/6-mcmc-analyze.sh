#!/bin/bash
#SBATCH -J apogee-analyze-mcmc
#SBATCH -o logs/apogee-analyze-mcmc.o%j
#SBATCH -e logs/apogee-analyze-mcmc.e%j
#SBATCH -N 5
#SBATCH -t 6:00:00
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
$CONDA_PREFIX/bin/hq analyze_mcmc -v --mpi

date
