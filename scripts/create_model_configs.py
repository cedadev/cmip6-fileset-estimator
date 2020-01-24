#!/usr/bin/env Python

import sys
import os
import requests
import subprocess
import re
import datetime as dt
#sys.path.append('../utils')
from utils import constants as cts

def get_latest_models():
    """
    Calls to the the https://github.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_source_id.json and collects the most
    recent version of the list of verified CMIP6 models.

    :return: [dict] of model information
    """
    resp = requests.get(cts.cmip6_source_id_CV)
    json_resp = resp.json()
    models = json_resp['source_id']
    return models


def parse_json(model, models):
    """
    Parses CMIP6 source_id information for a given model to collect the nominal resolution
    to pass to the data request.

    :param model: The user specified model of interest
    :param models: Full list of CMIP6 models
    :return: [str] no_horiz_gridpts_ocean, no_vert_levels_ocean, no_horiz_gridpts_atmos, no_vert_levels_atmos, \
           no_strat_levels, no_soil_levels, nlats
    """
    model_details = models[model]

    lat_long_comp = 1
    lon_comp = 0
    lat_comp = 2
    level_comp = 2
    nlevels = 0
    nlongs_ocean = get_resolution_component(model_details, 'ocean', lat_long_comp, lon_comp)
    nlats_ocean = get_resolution_component(model_details, 'ocean', lat_long_comp, lat_comp)
    no_horiz_gridpts_ocean = str(int(nlongs_ocean) * int(nlats_ocean))
    no_vert_levels_ocean = get_resolution_component(model_details, 'ocean', level_comp, nlevels)

    nlongs_atmos = get_resolution_component(model_details, 'atmos', lat_long_comp, lon_comp)
    nlats_atmos = get_resolution_component(model_details, 'atmos', lat_long_comp, lat_comp)
    no_horiz_gridpts_atmos = str(int(nlongs_atmos) * int(nlats_atmos))
    no_vert_levels_atmos = get_resolution_component(model_details, 'atmos', level_comp, nlevels)

    no_strat_levels = get_no_strat_levels(no_vert_levels_atmos)
    no_soil_levels = '5'
    nlats = str(int(nlats_atmos) + int(nlats_ocean))

    return no_horiz_gridpts_ocean, no_vert_levels_ocean, no_horiz_gridpts_atmos, no_vert_levels_atmos, \
           no_strat_levels, no_soil_levels, nlats


def get_no_strat_levels(no_vert_levels_atmos):

    try:
        if float(no_vert_levels_atmos) > 60:
            no_strat_levels = '20'
        else:
            no_strat_levels = '10'
    except:
        no_strat_levels = '10'

    return no_strat_levels



def get_horizontal_ocean_resolution(description):

    """

    :param description:
    :return: Tuple of nho, n_ocean_lats
    """

    nho = None
    nlats = None
    if description == "none":
        nho = "0"
        nlats = "0"
    elif re.search(r"\s?x\s?", description):
        match = re.search(r"\s?(?P<lons>\d+)[^.]\s?x\s?(?P<lats>\d+)[^.]", description)
        nho = str(int(match.groupdict()["lons"]) * int(match.groupdict()["lats"]))
        nlats = match.groupdict()["lats"]
    elif re.search("nodes", description):
        match = re.search(r"with\s(?P<nho>\d+).*nodes", description)
        nho = match.groupdict()["nho"]
        nlats = None
    elif re.search("cells", description):
        match = re.search(r"with\s(?P<nho>\d+).*cells", description)
        nho = match.groupdict()["nho"]
        nlats = None
    else:
        if not nho: nho =  "259200"
        if not nlats: nlats = "100"

    return nho, nlats

def get_number_of_ocean_levels(description):

    if description == "none":
        return "0"
    elif re.search("levels", description):
        match = re.search("(?P<nlo>\d+)\s?(levels|vertical levels)", description)
        return match.groupdict()["nlo"]
    else:
        return "60"

def get_number_of_atmos_levels(description):

    if description == "none":
        return "0", "0"
    elif re.search("levels", description):
        match = re.search("(?P<nl>\d+)\s?(levels|vertical levels)", description)
        nlevs = match.groupdict()["nl"]
        if int(nlevs) > 49: nlas = "20"
        else: nlas = "10"
        return nlevs, nlas
    else:
        return "40", "20"

def get_horizontal_atmos_resolution(description):

    if description == "none":
        nh = "0"
        lats = "0"
    elif re.search(" icosahedral-hexagonal", description):
        match = re.search(r"(?P<nh>\d+)-point\sicosahedral-hexagonal", description)
        nh = match.groupdict()["nh"]
        lats = 0

    elif re.search(r"\s?(?P<d1>\d+)[^.]\s?x\s?(?P<d2>\d+)[^.]x\s?(?P<d3>\d+)[^.]^cubeface", description):
        match = re.search(r"\s?(?P<d1>\d+)[^.]\s?x\s?(?P<d2>\d+)[^.]x\s?(?P<d3>\d+)[^.]", description)
        nh = str(int(match.groupdict()["d1"]) * int(match.groupdict()["d2"]) * int(match.groupdict()["d3"]))
        lats = None
    elif re.search(r"\d+[^.]\s?x\s?\d+[^.]longitude\/latitude;",description):
        match = re.search(r"(?P<lons>\d+)[^.]\s?x\s?(?P<lats>\d+)[^.]longitude\/latitude",description)
        nh = str(int(match.groupdict()["lons"]) * int(match.groupdict()["lats"]))
        lats = match.groupdict()["lats"]
    elif re.search(r"\s?x\s?", description):
        match = re.search(r"\s?(?P<lons>\d+)[^.]\s?x\s?(?P<lats>\d+)[^.]", description)
        nh = str(int(match.groupdict()["lons"]) * int(match.groupdict()["lats"]))
        lats = match.groupdict()["lats"]
    elif re.search("grid points in total", description):
        match = re.search(r"(?P<nh>\d+)\s?grid points in total", description)
        nh = match.groupdict()["nh"]
        lats = None
    elif re.search("cells", description):
        match = re.search(r";\s?(?P<nh>\d+,?\d{3}?,?(\d{3})?).*cells", description)
        nh = match.groupdict()["nh"]
        if "," in nh:
            nh = nh.replace(",", "")
        lats = None
    else:
        nh = "64800"
        lats = None

    return nh, lats

def get_number_of_soil_levels(description):
    if description == "none":
        return "0"
    else:
        return "5"


def get_nlats(model, n_ocean_lats, n_atmos_lats):

    if n_ocean_lats and n_atmos_lats:
        nlats = str(int(n_ocean_lats) + int(n_atmos_lats))

    elif model in cts.model_lats_expceptions.keys():
        nlats = cts.model_lats_expceptions[model]

    else:
        nlats = 200

    return nlats

def get_resolution_component(details):

    try:
        res = details['model_component'][realm]['description'].split('; ')[part].split(' ')[res_loc]
        try:
            x = int(res)
        except:
            res = 0
    except:
        res = 0
    return res



def main():

    model_details = get_latest_models()
    models = list(model_details.keys())
    models.sort()

    for model in models:

        # if model == "IPSL-CM7A-ATM-HR":
        #   print(model)
        # for model in ["VRESM-1-0"]:
        nho, n_ocean_lats = get_horizontal_ocean_resolution(model_details[model]["model_component"]["ocean"]["description"])
        nlo = get_number_of_ocean_levels(model_details[model]["model_component"]["ocean"]["description"])
        nha, n_atmos_lats = get_horizontal_atmos_resolution(model_details[model]["model_component"]["atmos"]["description"])
        nla, nlas = get_number_of_atmos_levels(model_details[model]["model_component"]["atmos"]["description"])
        nls = get_number_of_soil_levels(model_details[model]["model_component"]["atmos"]["description"])
        nlats = get_nlats(model, n_ocean_lats, n_atmos_lats)

        with open("ancils/model_configs-{}.txt".format(dt.datetime.today().isoformat().split('T')[0]), "a_") as w:
            w.writelines("{} : {} {} {} {} {} {} {}\n".format(model, nho, nlo, nha, nla, nlas, nls, nlats))

        os.unlink("ancils/model_configs.txt")
        os.symlink("ancils/model_configs-{}.txt".format(dt.datetime.today().isoformat().split('T')[0]), "ancils/model_configs.txt")

        """
        Write to the ancils dir the data dated
        create new symlink to latest
        os.unlink model_configs.txt
        os.link model_configs.txt to the latest
        """

if __name__ == "__main__":

    main()
