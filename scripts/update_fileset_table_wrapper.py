
import os
import subprocess
from utils import constants as cts
from create_filesets_table import get_list_of_models_and_mips

LATEST_MODEL_CFS = os.path.join(cts.BASEDIR, "ancils/model_configs_latest.txt")
SIMULATION_VOLS_DIR = os.path.join(cts.BASEDIR, "vols/simulation_level_fileset_vols")

def main():

    # Getting a list of a recent models and the mips that they are participating in
    model_mips = get_list_of_models_and_mips()

    # read in the latest model configurations table
    with open(LATEST_MODEL_CFS) as r:
        models = [ line.strip() for line in r ]

    for model in models:
        model_name = model.split(':')[0].strip()
        print(model_name)
        # Assert that every mip that this model is running has a corresponding simulation vol table
        mips_for_model = model_mips[model_name] # return a list of all the mips
        for mip in mips_for_model:
            simulation_fileset_vol_table_name = os.path.join(SIMULATION_VOLS_DIR, "cmip6_fileset_volumes_{}_{}.txt".format(model_name, mip))
            if not os.path.exists(simulation_fileset_vol_table_name):
                print("MISSING {}".format(simulation_fileset_vol_table_name))
                res = subprocess.call(["python", "create_filesets_table.py", "--model", model_name, "--mip", mip])


if __name__ == "__main__":

    main()