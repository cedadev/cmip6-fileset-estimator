#!/bin/bash

# Will only work when run on Francesca's home directory and in the correct directory (relative to Fran's env) - this wrapper is run on Fran's CRON machine, this is for reference only

source $HOME/.bash_profile
cd /home/users/eggleton/CEDA/CMIP6/cmip6-fileset-estimator/
source setup_env.sh
python scripts/create_model_config_wrapper.py
