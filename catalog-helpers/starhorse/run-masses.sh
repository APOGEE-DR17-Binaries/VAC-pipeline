#!/bin/bash
#SBATCH -J log-run-masses
#SBATCH -o log-run-masses.out
#SBATCH -e log-run-masses.err
#SBATCH -N 2
#SBATCH -t 12:00:00
#SBATCH -p cca
#SBATCH --constraint=rome

source ~/.bash_profile
init_conda
conda activate dr17-binaries
echo $HQ_RUN_PATH

cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries/catalog-helpers/starhorse

date

mpirun python3 -m mpi4py.run -rc thread_level='funneled' \
make_masses.py -v --mpi

date

