#!/usr/bin/env Python
# Constants used in cmip6-fileset-estimator code

import os

# Controlled vocabularies
cmip6_source_id_CV = 'https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_source_id.json'
cmip6_exp_id_CV = "https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_experiment_id.json"

# Dictionary of exceptions
model_lats_expceptions= {}
model_lats_expceptions['AWI-CM-1-1-LR'] = "600"
model_lats_expceptions['AWI-CM-1-1-MR'] = "1000"
model_lats_expceptions['AWI-CM-1-1-HR'] = "1200"
model_lats_expceptions['E3SM-1-0'] = "800"
model_lats_expceptions['AWI-ESM-1-1-LR'] = "600"
model_lats_expceptions['AWI-ESM-1-1-HR'] = "1200"
model_lats_expceptions['AWI-ESM-1-1-MR'] = "800"


# path used as basedir which is relative to the owners dirs
p=os.path.abspath(__file__).split('/')
idx = p.index('cmip6-fileset-estimator')
BASEDIR = '/'.join(p[:idx+1])

MAX_FILESET_SIZE = 50.
ENSEMBLE_SCALE_FACTOR = 1.
VERSION_SCALE_FACTOR = 1.