#!/bin/bash

#for ingest control

cd /home/badc/software/datasets/cmip6/cmip6-fileset-estimator/
source setup_env.sh
python scripts/fileset_table_creator_wrapper.sh
