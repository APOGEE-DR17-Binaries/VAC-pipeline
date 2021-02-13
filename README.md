# APOGEE DR17 binaries

Binary star science with APOGEE DR17 + [The Joker](https://github.com/adrn/thejoker).

## Environment configuration

Set up the conda environment with:

    conda env create -f environment.yml

To install mpi4py with openmpi4 on rusty, use:

    pip install mpi4py --no-binary :all:
