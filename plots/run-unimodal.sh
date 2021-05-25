#!/bin/bash
#SBATCH -J log-run-unimodal
#SBATCH -o log-run-unimodal.out
#SBATCH -e log-run-unimodal.err
#SBATCH -N 2
#SBATCH -t 2:00:00
#SBATCH -p cca
#SBATCH --constraint=rome

source ~/.bash_profile
init_conda
conda activate dr17-binaries
echo $HQ_RUN_PATH

cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries/plots

date

mpirun python3 -m mpi4py.run -rc thread_level='funneled' \
make_unimodal.py -v --mpi

date

