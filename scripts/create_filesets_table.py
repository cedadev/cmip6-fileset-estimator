
import os
import json
import requests
import subprocess
import argparse
from utils import constants as cts
from fileset_appender import FilesetAppender

def get_list_of_experiments():
    """
    
    :return: [DICT] form 'experiment_mips': {'tier': u'2', 'mips': [u'AerChemMIP']}
    """

    cmip6_experiments_cvs = cts.cmip6_exp_id_CV
    resp = requests.get(cmip6_experiments_cvs)
    json_resp = resp.json()
    exp_details = json_resp['experiment_id']
    
    experiments = exp_details.keys()
    experiments = sorted(experiments)

    experiment_mips = {}
    for e in experiments:
        experiment_mips[e] = {'tier': exp_details[e]["tier"], 'mips': exp_details[e]["activity_id"]}

    return experiment_mips

def get_list_of_models_and_mips():
    """
    Get a list of all models from the CMIP6 CV (Calls to the the
    https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_source_id.json and
    collects the most recent version of the list of verified CMIP6 models.)

    :return: [dict] of model information
    """
    resp = requests.get(cts.cmip6_source_id_CV)
    json_resp = resp.json()
    models_details = json_resp['source_id']

    models = models_details.keys()
    models = sorted(models)
    
    models_mips = {}
    for m in models:
        models_mips[m] = models_details[m]["activity_participation"]

    return models_mips

def get_model_configs(cmip6_model):
    """
    Returns model config information from the model config file created by create_model_configs.py

    :param cmip6_model:
    :return: model_cfgs

    """
    model_configs_file = os.path.join(cts.BASEDIR, "ancils/model_configs_latest.txt")

    with open(model_configs_file) as r:
        cfgs = r.readlines()

    model_cfgs = {}
    for line in cfgs:
        if line.split(' : ')[0].strip() == cmip6_model:
            model = line.split(' : ')[0].strip()
            vals = line.split(' : ')[1].strip()
            cfgs = []
            for v in vals.split(' '):
                cfgs.append(v)
            model_cfgs[model] = cfgs
    return model_cfgs


def call_data_request(model, model_configs, mip, experiment, mips, tier=1, priority=1, verbose=False):
    """
    "get_model_mip_exp_vol" routine links together the data volume calulation from the
    CMIP6 data request and the CMIP6 CVs, to produce an estimated data volume.

    :param model: A valid CMIP6 model that is the CMIP6 CV
    :param mip: A valid CMIP6 MIP name
    :param experiment: A valid CMIP6 experiment name
    :return: [Str] volume
    """
    if isinstance(mips, list):
        nmips = len(list(mips))
        mips = ','.join(mips).strip()
    else: nmips = 10


    if experiment in ['historical', 'piControl',
                      'ssp119', 'ssp126', 'ssp245', 'ssp370', 'ssp434',
                      'ssp460', 'ssp534-over', 'ssp585']:
        priority = 3
        if tier < 2:
            tier = 2

    nho, nlo, nha, nla, nlas, nls, nh1 = model_configs[model]
    model_config = "{nho},{nlo},{nha},{nla},{nlas},{nls},{nh1}".format(nho=int(nho), nlo=int(nlo), nha=int(nha),
                                                                       nla=int(nla), nlas=int(nlas), nls=int(nls),
                                                                       nh1=int(nh1))

    dreq_query = ['drq', '-e', experiment, '-m', mips, '-t', str(tier), '-p', str(priority), '--esm',
                  '--mcfg', model_config, '--printVars', '--printLinesMax', '10000', '--grdforce', 'native' ]
    if verbose:
        print(dreq_query)
    p = subprocess.Popen(dreq_query, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode('utf-8') # new line added for python3 due to changes in bytes
    lines = out.split('\n')

    table_vols, mipVol = parse_dreq_out(lines, mip, nmips)

    return table_vols, mipVol


def parse_dreq_out(lines, mip, nmips):
    """


    :param lines:
    :param mip: A valid CMIP6 MIP name
    :param nmips: Number of mips
    :return: table_vols
    :return: mipVol
    """

    table_vols = {}
    mipVol = {}
    if "----" in lines:
        logdir = os.path.join(cts.BASEDIR, "logs")
        if not os.path.isdir(logdir): os.makedirs(logdir)
        with open(os.path.join(logdir, 'dreq_errors.txt', 'a+')) as w:
            w.writelines(["{} {} {}\n".format(cmip6_mip, cmip6_model, experiment)])
        return {}, {mip: 0.0}

    if nmips == 1:
        for line in lines:
            if "TOTAL volume" in line:
                mipVol[mip] = float(line.split(' ')[-1].strip().strip('Tb'))
            elif "Frequency" in line or not line:
                continue
            else:
                table_vols = calc_table_variable_volumes(line, table_vols)

    else:
        for line in lines:
            if "*TOTAL:: TOTAL volume" in line:
                mipVol[mip] = float(line.split(' ')[-1].strip().strip('Tb'))
            elif "TOTAL volume" in line or "Frequency" in line or not line:
                continue
            else:
                table_vols = calc_table_variable_volumes(line, table_vols)

    return table_vols, mipVol


def calc_table_variable_volumes(line, table_vols):
    """

    :param line:
    :param table_vols:
    :return: table_vols

    """
    varVolDict = {}
    l = line.split('::')
    table_var = l[0].strip().split('.')
    table, var, vol = table_var[0], table_var[1], float(l[-1].strip().strip('Tb'))
    varVolDict[var] = vol

    if not table in table_vols.keys():
        table_vols[table] = [varVolDict]
    else:
        table_vols[table].append(varVolDict)

    return table_vols


def calc_table_vol(table_var_vol_dict):
    """

    :param table_var_vol_dict:
    :return: total_vols_by_table

    """

    total_vols_by_table = {}
    for cmor_table, varvol in table_var_vol_dict.items():
        table_sum = 0.
        for v in varvol:
            table_sum += list(v.values())[0]

        total_vols_by_table[cmor_table] = table_sum

    return total_vols_by_table


def get_mips_per_model(models_and_mips, cmip6_model):

    for model, mips in models_and_mips.items():

        if model == cmip6_model:
            return mips

    raise Exception('Model not in mips')

def exception_checker(cmip6_model, experiment):
    """


    """
    if cmip6_model == "AWI-CM-1-1-MR" and experiment == "piControl":
        return False
    elif experiment == "histSST-noLu":
        return False
    elif experiment in ["historical-cmip5", "piControl-cmip5", "piControl-spinup-cmip5", "faf-heat-NA0pct", "faf-antwater-stress", "faf-heat-NA50pct"]:
        return True
    elif cmip6_model == "EC-Earth3" and experiment == "historical":
        return True

def get_scale_factor(cmip6_model):
    """

    """
    if "UKESM" in cmip6_model or "HadGEM3" in cmip6_model:
        SCALE_FACTOR = 2.0
    else:
        SCALE_FACTOR = 1.0

    return SCALE_FACTOR

def log_granularity(ofile, appender, volume_type, format, threshold, fileset_depth_string):
    """

    """

    granularity = appender.get_granularity(ofile, format)
    if granularity and not granularity == threshold:
        if volume_type == table_vol or partial_table_fileset:
            raise Exception("GRANULARITY MATCH FAILED: table {} {}".format(experiment, table)) 
        elif volume_type == var:
            raise Exception("GRANULARITY MATCH FAILED: variable {} {} {}".format(experiment, table, var))
        else:
            raise Exception("GRANULARITY MATCH FAILED experiment {}".format(experiment))
    appender.write_fileset(fileset_depth_string, volume_type)


def get_volumes(models_and_mips, experiment_info, ofile, cmip6_model=None, cmip6_mip=None):

     # read in model congigurations (grid size) so that volume estimates are reflective of the model resolution
    model_cfgs = get_model_configs(cmip6_model)

    # For a given model
    mips = get_mips_per_model(models_and_mips, cmip6_model)

    # Instansiate the filesetappender
    if not os.path.exists(ofile):
        open(ofile, 'a').close()
    appender = FilesetAppender(ofile)

    for experiment, exp_details in experiment_info.items():
        exceptions = exception_checker(cmip6_model,experiment)
        if exceptions is True:
            continue
        else:
            tier = experiment_info[experiment]['tier']

            if cmip6_mip in exp_details['mips']:

                table_var_vols, simVol = call_data_request(cmip6_model, model_cfgs, cmip6_mip, experiment, mips, tier=int(tier))
                scale_factor = get_scale_factor(cmip6_model)

                total_simulation_vol = list(simVol.values())[0] * scale_factor # dictionary values now have to be a list to index

                if total_simulation_vol == 0.:
                    continue

                if total_simulation_vol < cts.MAX_FILESET_SIZE:
                    fileset_depth_string = "{}/{}/*/{}/{}/".format('CMIP6', cmip6_mip, cmip6_model, experiment)
                    log_granularity(ofile, appender, total_simulation_vol,experiment,5, fileset_depth_string)
                else:
                    single_ensmb_vol = list(simVol.values())[0] * cts.VERSION_SCALE_FACTOR
                    if single_ensmb_vol < cts.MAX_FILESET_SIZE:
                        fileset_depth_string_single = "{}/{}/*/{}/{}/*/".format('CMIP6', cmip6_mip, cmip6_model, experiment)
                        log_granularity(ofile, appender, single_ensmb_vol, ("{}/*".format(experiment)), 6, fileset_depth_string_single)
                    else:
                        tableVols = calc_table_vol(table_var_vols)
                        for table, vol in tableVols.items():
                            table_vol = vol * cts.VERSION_SCALE_FACTOR
                            if table_vol < cts.MAX_FILESET_SIZE:
                                fileset_depth_string_table = "{}/{}/*/{}/{}/*/{}/".format('CMIP6', cmip6_mip, cmip6_model, experiment, table)
                                log_granularity(ofile,appender, table_vol, ("{}/*/{}".format(experiment, table)), 7, fileset_depth_string_table)
                            else:
                                var_vols = table_var_vols[table]
                                partial_table_fileset = []
                                for item in var_vols:
                                    var = list(item.keys())[0] # keys need to be indexed as a list too
                                    vol = list(item.values())[0] * cts.VERSION_SCALE_FACTOR
                                    if vol > 1.0:
                                        fileset_depth_string_var = "{}/{}/*/{}/{}/*/{}/{}/".format('CMIP6', cmip6_mip, cmip6_model, experiment, table, var)
                                        log_granularity(ofile, appender, vol,("{}/*/{}/{}".format(experiment, table, var)),8,fileset_depth_string_var)

                                    else:
                                        partial_table_fileset.append(item)

                        if partial_table_fileset:
                            fileset_depth_string_partial = str("{}/{}/*/{}/{}/*/{}/".format('CMIP6', cmip6_mip,cmip6_model, experiment,table))
                            log_granularity(ofile,appender, partial_table_fileset,("{}/*/{}".format(experiment, table)),7,fileset_depth_string_partial)

                            partial_table_sum = 0.
                            for v in partial_table_fileset:
                                partial_table_sum += list(v.values())[0] * cts.VERSION_SCALE_FACTOR
                            if partial_table_sum > cts.MAX_FILESET_SIZE:
                                partial_table_sum = cts.MAX_FILESET_SIZE

                            appender.write_fileset(fileset_depth_string, partial_table_sum) #this ones is different to the others so cant go in function

                            #so I have managed to take out many lines and translate to python 3 but not reduce the indent

def run_main(cmip6_model=None, cmip6_mip=None):

    # Get a dictionary of models and which MIPS they are participating in
    models_and_mips = get_list_of_models_and_mips()
    #print(models_and_mips)

    # assert the given model is in the list, ensures no typos
    assert(cmip6_model in models_and_mips.keys())

    if not cmip6_mip in models_and_mips[cmip6_model]:
        models_and_mips[cmip6_model].append(cmip6_mip)

    # get a dictionary of all experiments with its tier and list of mips
    experiments_info = get_list_of_experiments()

    # Get the estimated volume for a given model
    volsdir = os.path.join(cts.BASEDIR, "vols", "simulation_level_fileset_vols")
    if not os.path.isdir(volsdir):
        os.makedirs(volsdir)

    output_file = os.path.join(volsdir, "cmip6_fileset_volumes_{}_{}.txt".format(cmip6_model, cmip6_mip))
    get_volumes(models_and_mips, experiments_info, output_file, cmip6_model=cmip6_model, cmip6_mip=cmip6_mip)


def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='A valid CMIP6 model')
    parser.add_argument('--mip', type=str, help='A valid CMIP6 mip')

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_main(cmip6_model=args.model, cmip6_mip=args.mip)

