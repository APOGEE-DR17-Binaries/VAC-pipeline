#!/bin/bash
module load disBatch
sbatch -N6 --constraint=rome -p cca disBatch.py mcmc_taskfile
