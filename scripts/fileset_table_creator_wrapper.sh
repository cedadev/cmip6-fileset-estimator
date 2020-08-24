#!/bin/bash

# Wrapper script to run entire fileset workflow of cmip6-fileset-estimator (after create_model_config_wrapper workflow) - setting directories and environment
# will run update_fileset_table_wrapper.py script and if successful will then run postprocess_fileset_volume_checker.py


cd /home/badc/software/datasets/cmip6/cmip6-fileset-estimator/
source setup_env.sh
cd scripts/

python update_fileset_table_wrapper.py

if [ $? -eq 0 ]; then
    echo "updated table"
    python postprocess_fileset_volume_checker.py

    if [ $? -eq 0 ]; then
        echo "New fileset table created"
    else
        mail -s "Failed to create new fileset table at postprocess_fileset_volume_checker" francesca.eggleton@stfc.ac.uk <<< "Fail"
    fi

else
    mail -s "Failed to run update on table at update_fileset_table_wrapper" francesca.eggleton@stfc.ac.uk <<< "Fail"
fi
