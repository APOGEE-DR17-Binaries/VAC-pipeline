#!/bin/bash
#SBATCH -J apogee-combine
#SBATCH -o logs/apogee-combine.o%j
#SBATCH -e logs/apogee-combine.e%j
#SBATCH -n 1
#SBATCH -t 1:00:00
#SBATCH -p cca
#SBATCH --constraint=rome

# Relocate and initialize shell
cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries/vac-pipeline
source hq-config/init.sh
echo $HQ_RUN_PATH

date

$CONDA_PREFIX/bin/hq combine_metadata -v -o

date
