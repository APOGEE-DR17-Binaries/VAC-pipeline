#!/bin/bash
#SBATCH -J apogee-tar
#SBATCH -o logs/apogee-tar.o%j
#SBATCH -e logs/apogee-tar.e%j
#SBATCH -n 1
#SBATCH -t 12:00:00
#SBATCH -p cca

source ~/.bash_profile

cd /mnt/ceph/users/apricewhelan/projects/apogee-dr17-binaries/vac-pipeline/cache/hq

date

tar -czf samples.tar.gz samples

date

