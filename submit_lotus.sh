#!/bin/bash

# Will only work when run on Francesca's home directory and in the correct directory (relative to Fran's env) - this wrapper is run on Fran's CRON machine, this is for reference only

source $HOME/.bash_profile
BASEDIR=/home/users/eggleton/CEDA/CMIP6/cmip6-fileset-estimator/

cd ${BASEDIR}
cd scripts/

sbatch -o ../lotus_logs/slurm-%j.out -t 6:00 ./fileset_table_creator_wrapper.sh


