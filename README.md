# APOGEE DR17 binaries: VAC pipeline

APOGEE DR17 + [The Joker](https://github.com/adrn/thejoker).


## Environment configuration

Set up the conda environment with:

    conda env create -f environment.yml

Or install into a virtual environment:

    python -m pip install -r requirements.txt

To install mpi4py with openmpi4 on rusty, use:

    python -m pip install mpi4py --no-binary :all:


## Pipeline

The pipeline is run by executing staged MPI scripts in `mpi/`.