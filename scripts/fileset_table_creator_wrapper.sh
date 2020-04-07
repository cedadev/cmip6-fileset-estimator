#!/bin/bash

BASEDIR=/home/users/rpetrie/cmip6/cmip6-fileset-estimator/
cd ${BASEDIR}
source setup_env.sh
cd scripts/

python update_fileset_table_wrapper.py


if [ $? -eq 0 ]; then
    echo "updated table"
#    python postprocess_fileset_volume_checker.py
#
#    if [ $? -eq 0 ]; then
#        echo "New fileset table created"
#    else
#        echo "Failed to create new table at postprocessor" # email
#    fi

else
    echo "Failed to run update wrapper"
    # maybe email
fi
