#!/bin/bash

#for ingest_control

cd /home/badc/software/datasets/cmip6/cmip6-fileset-estimator/
source setup_env.sh
python scripts/create_model_config_wrapper.py
