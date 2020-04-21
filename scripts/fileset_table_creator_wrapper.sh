#!/bin/bash

# Wrapper script to run entire workflow of cmip6-fileset-estimator - setting directories and environment
# will run update_fileset_tabl_wrapper.py script and if successful will then run postprocess_fileset_volume_checker.py

BASEDIR=/home/users/eggleton/CEDA/CMIP6/cmip6-fileset-estimator/ # this is set up to run from Francesca's home directory as it is run on her cron machine as a job on lotus
cd ${BASEDIR}
source setup_env.sh # this sources a set up script which references a python 3 virtual environment only on Francesca's home dir
cd scripts/

python update_fileset_table_wrapper.py

if [ $? -eq 0 ]; then
    echo "updated table"
    python postprocess_fileset_volume_checker.py

    if [ $? -eq 0 ]; then
        echo "New fileset table created"
    else
        #this currently doesn't work due to env being used by lotus - works on sci5 not sci6
        mail -s "Failed to create new fileset table at postprocess_fileset_volume_checker" francesca.eggleton@stfc.ac.uk <<< "Fail"
    fi

else
    mail -s "Failed to run update on table at update_fileset_table_wrapper" francesca.eggleton@stfc.ac.uk <<< "Fail"
fi
