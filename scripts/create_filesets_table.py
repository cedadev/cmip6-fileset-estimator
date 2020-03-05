
import os
import json
import requests
import subprocess
import argparse
from utils import constants as cts
from fileset_appender import FilesetAppender

def get_list_of_experiments():
    """
    
    :return: [DICT] form 'experiment_id': {'tier': u'2', 'mips': [u'AerChemMIP']}
    """

    cmip6_experiments_cvs = cts.cmip6_source_id_CV
    resp = requests.get(cmip6_experiments_cvs)
    json_resp = resp.json()
    exp_details = json_resp['experiment_id']
    experiments = exp_details.keys()
    experiments.sort()

    experiment_mips = {}
    for e in experiments:
        experiment_mips[e] = {'tier': exp_details[e]["tier"], 'mips': exp_details[e]["activity_id"]}

    return experiment_mips


def get_list_of_models_and_mips():
    """
    Get a list of all models from the CMIP6 CV (Calls to the the
    https://github.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_source_id.json and
    collects the most recent version of the list of verified CMIP6 models.)

    :return: [dict] of model information
    """
    resp = requests.get(cts.cmip6_source_id_CV)
    json_resp = resp.json()
    models_details = json_resp['source_id']

    models = models_details.keys()
    models.sort()

    models_mips = {}
    for m in models:
        models_mips[m] = models_details[m]["activity_participation"]

    return models_mips


def get_model_configs(cmip6_model):

    model_configs_file = os.path.join(cts.BASEDIR, "ancils/model_configs.txt") # this doesn't exist

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


def call_data_request(model, model_configs, mip, experiment, mips, tier=1, priority=1):
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
        if tier < 2: tier = 2

    # priority = 3
    # tier = 3

    nho, nlo, nha, nla, nlas, nls, nh1 = model_configs[model]
    model_config = "{nho},{nlo},{nha},{nla},{nlas},{nls},{nh1}".format(nho=int(nho), nlo=int(nlo), nha=int(nha),
                                                                       nla=int(nla), nlas=int(nlas), nls=int(nls),
                                                                       nh1=int(nh1))
    # priority=3
    # tier=3
    dreq_query = ['drq', '-e', experiment, '-m', mips, '-t', str(tier), '-p', str(priority), '--esm',
                  '--mcfg', model_config, '--printVars', '--printLinesMax', '10000', '--grdforce', 'native' ]
    print(dreq_query)
    p = subprocess.Popen(dreq_query, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    lines = out.split('\n')

    table_vols, mipVol = parse_dreq_out(lines, mip, nmips)

    return table_vols, mipVol


def parse_dreq_out(lines, mip, nmips):


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

    total_vols_by_table = {}
    for cmor_table, varvol in table_var_vol_dict.iteritems():
        table_sum = 0.
        for v in varvol:
            table_sum += v.values()[0]

        total_vols_by_table[cmor_table] = table_sum

    return total_vols_by_table


def get_mips_per_model(models_and_mips, cmip6_model):

    for model, mips in models_and_mips.iteritems():

        if model == cmip6_model:
            return mips

    raise Exception('Model not in mips')


def get_volumes(models_and_mips, experiment_info, ofile, cmip6_model=None, cmip6_mip=None):

     # read in model congigurations (grid size) so that volume estimates are reflective of the model resolution
    model_cfgs = get_model_configs(cmip6_model)

    # For a given model
    mips = get_mips_per_model(models_and_mips, cmip6_model)

    # Instansiate the filesetappender
    if not os.path.exists(ofile):
        open(ofile, 'a').close()
    appender = FilesetAppender(ofile)

    for experiment, exp_details in experiment_info.iteritems():
      if cmip6_model == "AWI-CM-1-1-MR" and experiment == "piControl":
          pass
      elif experiment == "histSST-noLu":
          pass

      elif experiment == "historical-cmip5" or experiment == "piControl-cmip5" or experiment == "piControl-spinup-cmip5":
          continue

      elif cmip6_model == "EC-Earth3" and experiment == "historical":
          continue


      else:
        # set tier of experiment
        tier = experiment_info[experiment]['tier']

        if cmip6_mip in exp_details['mips']:

            table_var_vols, simVol = call_data_request(cmip6_model, model_cfgs, cmip6_mip, experiment, mips, tier=tier)

            if "UKESM" in cmip6_model or "HadGEM3" in cmip6_model:
                SCALE_FACTOR = 2.0 #cts.ENSEMBLE_SCALE_FACTOR * cts.VERSION_SCALE_FACTOR
            else:
                SCALE_FACTOR = 1.0 #cts.VERSION_SCALE_FACTOR

            total_simulation_vol = simVol.values()[0] * SCALE_FACTOR
            # total_simulation_vol = simVol.values()[0]
            if total_simulation_vol == 0.:
                continue

            if total_simulation_vol < cts.MAX_FILESET_SIZE:
                granularity = appender.get_granularity(ofile, experiment)
                if granularity and not granularity == 5:
                    raise Exception("GRANULARITY MATCH FAILED experiemnt {}".format(experiment))
                fileset_depth_string = "{}/{}/*/{}/{}/".format('CMIP6', cmip6_mip, cmip6_model, experiment)
                appender.write_fileset(fileset_depth_string, total_simulation_vol)

            else:
                single_ensmb_vol = simVol.values()[0] * cts.VERSION_SCALE_FACTOR
                if single_ensmb_vol < cts.MAX_FILESET_SIZE:
                    granularity = appender.get_granularity(ofile, "{}/*".format(experiment))
                    if granularity and not granularity == 6:
                        raise Exception("GRANULARITY MATCH FAILED ensemble: {}".format(experiment))
                    fileset_depth_string = "{}/{}/*/{}/{}/*/".format('CMIP6', cmip6_mip, cmip6_model, experiment)
                    appender.write_fileset(fileset_depth_string, single_ensmb_vol)

                else:
                    tableVols = calc_table_vol(table_var_vols)
                    for table, vol in tableVols.iteritems():
                        table_vol = vol * cts.VERSION_SCALE_FACTOR


                        if table_vol < cts.MAX_FILESET_SIZE:

                            granularity = appender.get_granularity(ofile, "{}/*/{}".format(experiment, table))
                            if granularity and not granularity == 7:
                                raise Exception("GRANULARITY MATCH FAILED: table {} {}".format(experiment, table))
                            fileset_depth_string = "{}/{}/*/{}/{}/*/{}/".format('CMIP6', cmip6_mip, cmip6_model, experiment, table)
                            appender.write_fileset(fileset_depth_string, table_vol)
                        else:

                            var_vols = table_var_vols[table]
                            partial_table_fileset = []

                            for item in var_vols:
                                var = item.keys()[0]
                                vol = item.values()[0] * cts.VERSION_SCALE_FACTOR
                                if vol > 1.0:
                                    # print experiment, table, var, vol, granularity
                                    granularity = appender.get_granularity(ofile, "{}/*/{}/{}".format(experiment, table, var))
                                    if granularity and not granularity == 8:
                                        raise Exception(
                                            "GRANULARITY MATCH FAILED: variable {} {} {}".format(experiment, table, var ))

                                    fileset_depth_string = "{}/{}/*/{}/{}/*/{}/{}/".format('CMIP6', cmip6_mip,
                                                                                           cmip6_model,
                                                                                           experiment, table,
                                                                                           var)
                                    appender.write_fileset(fileset_depth_string, vol)

                                else:
                                    partial_table_fileset.append(item)

                            if partial_table_fileset:
                                granularity = appender.get_granularity(ofile, "{}/*/{}".format(experiment, table))
                                if granularity and not granularity == 7:
                                    raise Exception("GRANULARITY MATCH FAILED : table {} {}".format(experiment, table))

                                partial_table_sum = 0.
                                for v in partial_table_fileset:
                                    partial_table_sum += v.values()[0] * cts.VERSION_SCALE_FACTOR
                                if partial_table_sum > cts.MAX_FILESET_SIZE:
                                   partial_table_sum = cts.MAX_FILESET_SIZE
                                fileset_depth_string = "{}/{}/*/{}/{}/*/{}/".format('CMIP6', cmip6_mip,
                                                                                    cmip6_model, experiment,
                                                                                    table)
                                appender.write_fileset(fileset_depth_string, partial_table_sum)


def run_main(cmip6_model=None, cmip6_mip=None):

    # Get a dictionary of models and which MIPS they are participating in
    models_and_mips = get_list_of_models_and_mips()

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

