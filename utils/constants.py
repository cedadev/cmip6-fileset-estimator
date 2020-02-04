#!/usr/bin/env Python

import os

#
cmip6_source_id_CV = 'https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_source_id.json'

#
model_lats_expceptions= {}
model_lats_expceptions['AWI-CM-1-1-LR'] = "600"
model_lats_expceptions['AWI-CM-1-1-MR'] = "1000"
model_lats_expceptions['AWI-CM-1-1-HR'] = "1200"
model_lats_expceptions['E3SM-1-0'] = "800"
model_lats_expceptions['AWI-ESM-1-1-LR'] = "600"
model_lats_expceptions['AWI-ESM-1-1-HR'] = "1200"
model_lats_expceptions['AWI-ESM-1-1-MR'] = "800"


#
#BASEDIR = os.getcwd()
BASEDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
#print(BASEDIR)