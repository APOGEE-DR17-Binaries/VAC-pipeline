#!/bin/bash
#SBATCH -J apogee-combine
#SBATCH -o logs/apogee-combine.o%j
#SBATCH -e logs/apogee-combine.e%j
#SBATCH -n 1
#SBATCH -t 1:00:00
#SBATCH -p cca
#SBATCH --constraint=rome

source ~/.bash_profile
init_conda
conda activate dr17-binaries
export HQ_RUN_PATH=/mnt/home/apricewhelan/projects/apogee-dr17-binaries/hq-config
echo $HQ_RUN_PATH

cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries

date

$CONDA_PREFIX/bin/hq combine_metadata -v -o

date
