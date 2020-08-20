#!/bin/bash

#for ingest control

#source $HOME/.bash_profile
BASEDIR=/home/badc/software/datasets/cmip6/cmip6-fileset-estimator/

cd ${BASEDIR}
cd scripts/

sbatch -o /home/badc/software/datasets/cmip6/cmip6-fileset-estimator/lotus_logs/slurm-%j.out -t 6:00 ./fileset_table_creator_wrapper.sh


