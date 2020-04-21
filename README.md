# cmip6-fileset-estimator
Calculation of CMIP6 CEDA fileset volumes

Here the CMIP6 source_id (models) CV (https://github.com/WCRP-CMIP/CMIP6_CVs/blob/master/CMIP6_source_id.json) is interrogated to get an approximate model resolution.

Then this code calls the CMIP6 Data Request Python Package, this is currently installed by svn as there is an issue with the pip install (http://proj.badc.rl.ac.uk/svn/exarch/CMIP6dreq/trunk/).

# Known issues

As of 28-06-2019 the controlled vocabularies are not fully up to date the model IPSL-CM6A-LR is participating in mips not listed, HighResMIP and DAMIP. The fileset look up tables need to be generated for these manually.

# Usage
All of the code in this directory is Python 3 compliant. It is recommended that to run this code, a Python 3 virtual environment be set up which has the Data Request package version 1.0.31 and install XlsxWriter (as this is not currently included in this version of the dreq). This code will be tested with the latest version of the Data Request as soon as it is available.

Use this code with the latest version of the data request that includes all models to avoid failures, currently excluded is experiment: histSST-noLu

All the constants used in this workflow (all Python scripts in ./scripts/) are contained within ./utils/constants.py

# Running manually
All of the following scripts are within the ./scripts/ subdir

To generate a single file of model configs in subdir ./ancils/model_configs_YYYY-MM-DD.txt and remove files older than 3 days (keeping the 1st of the month) run the ./scripts/create_model_configs.py script through the wrapper in the following way:

python create_model_config_wrapper.py 
Note no command line argument is required unless you would like to test today's file has been created then use:
python creat_model_config_wrapper.py --v

To generate a single file of fileset volumes in subdir ./vols/simulation_level_filesets Provide at present a single CMIP model, MIP and experiment in the following way:

python create_filesets_table.py --model <CMIP6 model_id> --mip <CMIP6 mip_id>
Note that create_filesets_table.py checks for a consistent granularity of datasets for any filesets that already exist.

To generate any missing files from the full (model, mip) list use ./scripts/update_fileset_table_wrapper.py. This script will check if a file exists for each model and mip (files in ./vols/simulation_level_filesets). If the file is missing, ./scripts/create_fileset_table.py will be run. The wrapper can be used in the following way:

python update_fileset_table_wrapper.py

# Post-processing

Run the post processing script:

python postprocess_fileset_volume_checker.py 
This checks that filesets are provided in a way that is consistent with CREPP and that the granularity of the filesets is provided in a consistent way.

This also creates a copy of the lookup table at ../vols/cmip6_fileset_volumes_latest.txt.txt and /gws/nopw/j04/cmip6_prep_vol1/cmip6_data_vols/cmip6_filesets_volume_lookup.txt which is the destination of the symlink at /gws/nopw/j04/cmip6_prep_vol1/filesets/cmip6_filesets.txt this is where CREPP expects to find the lookup table.

# Wrapper Script

In order to run the whole process described above, run ./fileset_table_creator_wrapper.sh. This does not include the running of create_model_config_wrapper.py (the first step in the workflow) - see details below about it running on the CRON machine. 

This bash script is written relative to Francesca Eggleton's environment as it is run from her home directory and setup on her CRON machine account (see below). This wrapper will run ./update_fileset_table_wrapper.py and if successful, will run ./postprocess_fileset_volume_checker.py.

This workflow will create any missing or new files in subdir ./vols/simulation_level_fileset_vols/cmip6_fileset_volumes_<model>_<mip>.txt, it will create a concatenated single file table under subdir ./vols/volume_tables/cmip6_fileset_volumes_YYY-MM-DD.txt, create a symlink between ./vols/volume_tables/cmip6_fileset_volumes_latest.txt and ./vols/volume_tables/cmip6_fileset_volumes_YYY-MM-DD.txt (created daily via CRON run below) and copy this latest file to gws described above (post-processing).

# Running on the CRON machine
The ./create_model_config_wrapper.py script is run daily on Francesca's CRON machine using a basic bash wrapper script called cron_wrapper_cmip6.sh.
This bash script has been written for use on Francesca's machine and will not run within this repo, it is for reference only to show how this is run in crontab. This produces a daily file in subdir ./ancils/model_configs_YYYY-MM-DD.txt.

The ./fileset_table_creator_wrapper.sh is run daily on Francesca's CRON machine through submission to LOTUS. A basic wrapper script called submit_lotus.sh has been created specific to Francesca's environment to submit this job to LOTUS.
This bash script will not run within this repo on anyone else's machine, however, it can be used as reference for writing a similar script relative to the users environment. 
