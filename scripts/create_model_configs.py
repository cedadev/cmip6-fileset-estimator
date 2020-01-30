#!/usr/bin/env Python

import sys
import os
import shutil
import requests
import subprocess
import re
import datetime as dt

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
    """
        Returns the number of stratospheric levels based on the number of vertical
        levels in the model which is returned from the parse_jason function

        :param no_vert_levels_atmos: [str] returned from the parse_jason function
        :return: [str] no_strat_levels
        """
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
    This function uses regular expressions to search through the model description information
    to find out the lats and lons. These are used to calculate the number of horizontal grid
    cells in the ocean and the number of latitude values. If this information is not available
    then alternative searches are performed. Otherwise a default value is given

    :param description: The [model_component"], ["ocean"] and ["description] from a \
                        [dict] of model information returned by get_latest_models
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
    """
    This function uses regular expressions to search through the model description information
    to find out the number of ocean levels using the keywords 'levels' and 'vertical levels'.
    If no information is found a default value of '60' is given.

    :param description: The [model_component"], ["ocean"] and ["description] from a [dict] of model \
                        information returned by get_latest_models
    :return: nlo
    """

    if description == "none":
        return "0"
    elif re.search("levels", description):
        match = re.search("(?P<nlo>\d+)\s?(levels|vertical levels)", description)
        return match.groupdict()["nlo"]
    else:
        return "60"

def get_number_of_atmos_levels(description):
    """
    This function uses regular expressions to search through the model description
    information to find out the number of atmospheric levels using the keywords 'levels'
    and 'vertical levels'. The number of stratospheric levels is decided based on the
    atmospheric levels. If no information is found a default value is given.

    :param description: The [model_component"], ["atmos"] and ["description] from \
                        a [dict] of model information returned by get_latest_models
    :return: Tuple of nlevs, nlas
    """
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
    """
    Returns the number of horizontal grid cells in the atmosphere and latitude using
    regular expression searches into the input model description. If a combination of
    the two output values isn't found then a default value of '64800' is returned for nh.

    :param description: The [model_component"], ["atmos"] and ["description] from \
                        a [dict] of model information returned by get_latest_models
    :return: Tuple of nh, n_atmos_lats
      """
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
    """
    This function identifies the number of soil levels. If there is no soil level information then this will return '0'.
    Else a default value of '5' is given.

    :param description: The [model_component"], ["atmos"] and ["description] from a [dict] of model information returned
    by get_latest_models
    :return: [int] 0 or 5
    """
    if description == "none":
        return "0"
    else:
        return "5"


def get_nlats(model, n_ocean_lats, n_atmos_lats):
    """
    Returns the total number of latitude values based on the number of atmospheric latitude
    values and the number of ocean latitude values. If this is not provided......
    Else a default value of '200' is returned.

    :param model:
    :param n_ocean_lats: Number of ocean latitude values returned by get_horizontal_ocean_resolution
    :param n_atmos_lats: Number of atmospheric latitude values returned by get_horizontal_atmos_resolution
    :return: nlats
    """
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
            _ = int(res)
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

        filename = os.path.join(cts.BASEDIR, "ancils/model_configs_{}.txt".format(dt.datetime.today().isoformat().split('T')[0]) )
        with open(filename, "a+") as w:
            w.writelines("{} : {} {} {} {} {} {} {}\n".format(model, nho, nlo, nha, nla, nlas, nls, nlats))


        src = os.path.join(cts.BASEDIR, "ancils/model_configs_{}.txt".format(dt.datetime.today().isoformat().split('T')[0]))
        dst = os.path.join(cts.BASEDIR, "ancils/model_configs_latest.txt")

        os.remove(dst)
        shutil.copyfile(src, dst)


        """
        write a test to make sure new file exists in a function and print to screen that name function that
        take verbose as an option so 
        
        def fnName(file, verbose=False)
            
            if verbose: 
                print("I made a file {}".format(fname))
                
       
        NEXT
        Write in a wrapper to run this script and check that days text files exists as know the fileformat
        Then keep previous 3 days of txt files and the 1st of every month as backup - delete the rest
        Get wrapper into cron
        """


if __name__ == "__main__":

    main()
