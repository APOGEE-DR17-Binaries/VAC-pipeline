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

The full pipeline is a mixture of IPython notebooks and staged MPI scripts that
perform the bulk of the analysis. The IPython notebooks are used to define the
parent sample and produce re-calibrated APOGEE visit spectrum velocity
uncertainties, which are then used by the MPI scripts to perform `thejoker`
samplings (using the [hq](https://github.com/adrn/hq) pipeline tool). The full
steps to produce the final value-added catalog (VAC) are detailed below.

### APOGEE DR17 data

At the time that this pipeline was run, APOGEE DR17 data were proprietary and
not released publicly. The data can be obtained through the usual internal SDSS
data mirrors; In this case, the data files (allStar and allVisit) were stored
locally on the Flatiron compute cluster in `~/data/APOGEE_DR17/`.

### Visit uncertainty calibration and defining the parent sample

These steps are done through the pipeline IPython notebooks in
`notebooks/pipeline`:

1. `1-Visit-Error-Calibrate.ipynb` — this produces the
   `cache/allVisit-dr17-synspec-calib-verr.fits` file, containing the
   re-calibrated visit errors.
2. `2-Make-Parent-Sample.ipynb` — this produces the
   `cache/allVisit-dr17-synspec-min3-calibverr.fits` file, which contains the
   full visit data for the parent sample (sources with 3 or more visits that
   pass the quality cuts defined in the notebook).

### Main data processing

The main work in producing the VAC is done by the MPI scripts that run the
[hq](https://github.com/adrn/hq) pipeline components to generate `thejoker`
samplings for all APOGEE DR17 sources in the parent sample (defined in the
previous step). The MPI scripts in the `mpi/` subdirectory should be executed in
numerical order on a compute cluster.

At the end of these runs, the core low-level output files have been created in
the `cache/hq` directory:

- `cache/hq/metadata.fits` — this file contains source-level metadata about the
  samplings produced by *The Joker*.
- `cache/hq/thejoker-samples.hdf5` — this file contains all of the samples,
  organized by HDF5 groups with names equal to the `APOGEE_ID` of each source in
  the parent sample.
- `cache/hq/mcmc-samples.hdf5` — the same, but for samples produced by MCMC (run
  for sources that end with unimodal samplings from *The Joker*).

### Final catalog creation

The final steps of the pipeline are to produce additional catalogs (and links)
in the `catalogs` subdirectory. These catalogs are created in the final pipeline
notebooks in `notebooks/pipeline`:

1. `3-Make-gold-sample.ipynb` — this produces the "Gold Sample" binary star
   catalog, which is a subset of the sources with unimodal samplings from *The
   Joker* with selections made on statistics like the phase coverage of the data
   and the maximum gap in phase coverage to try to remove spurious unimodal
   solutions. This notebook produces `catalogs/gold-sample.fits`.
2. `4-Make-binary-catalogs.ipynb` — this produces the two catalogs of binary
   stars (generally with multimodal samplings) selected either with a strict
   selection criteria or a more lenient criteria. The selections are based on a
   likelihood ratio (comparing a Keplerian model to a constant radial velocity
   model) and based on percentile values of the velocity semi-amplitude samples
   for each source. This notebook produces the files
   `catalogs/binaries-lenient.fits` and `catalogs/binaries-strict.fits`.
