
import os
import json
import sys

date = sys.argv[1]

VOLSFILE = f"../allocations-data/cmip6_vols_{date}.json"
HIGHRESMIP_DATA_VOLS_FILE = f"../allocations-data/highresmip_fileset_allocations_{date}.csv"
MOHC_DATA_VOLS_FILE = f"../allocations-data/mohc_fileset_allocations_{date}.csv"
REPLICA_DATA_VOLS_FILE = f"../allocations-data/replica_fileset_allocations_{date}.csv"
SCALE = 1.0 / (1024. * 1024. * 1024. * 1024.)


def get_facets(path):

    facets = path.split("/")[5:]

    if len(facets) == 4:
        facets.append('')
        facets.append('')
        facets.append('')
    if len(facets) == 5:
        facets.append('')
        facets.append('')
    if len(facets) == 6:
        facets.append('')

    mip, inst, model, exp, ens, table, var = facets
    return mip, inst, model, exp, ens, table, var


def highres_and_mohc(path, mip, inst, model, exp, ens, table, var, allocation_tb, current_tb, percent_used, highres, mohc):
    replica = False
    if mip == "HighResMIP":
        if inst in ["AWI", "CMCC", "EC-Earth-Consortium", "ECMWF", "MOHC", "MPI-M"]:
            highres.writelines(f"{path}, {mip}, {inst}, {model}, {exp}, {ens}, {table}, {var}, {allocation_tb}, {current_tb}, {percent_used}\n")


        elif inst == "CNRM-CERFACS" and model in ["CNRM-CM6-1", "CNRM-CM6-1-HR"]:
            if exp in ["highresSST-present", "highresSST-present", "highres-future", "highres-future",
                       "spinup-1950", "hist-1950", "hist-1950", "control-1950",
                       "control-1950", "highres-future", "highres-future"]:
                if ens == "r1i1p1f2":
                    highres.writelines(f"{path}, {mip}, {inst}, {model}, {exp}, {ens}, {table}, {var}, "
                                       f"{allocation_tb}, {current_tb}, {percent_used}\n")
                else:
                    replica = True
            else:
                replica = True

        else:
            replica = True

    elif not mip == "HighResMIP" and inst == "MOHC":
        mohc.writelines(f"{path}, {mip}, {inst}, {model}, {exp}, {ens}, {table}, {var}, "
                        f"{allocation_tb}, {current_tb}, {percent_used}\n")

    elif mip == "AerChemMIP" and inst in ["NERC", "NIWA", "KMA"]:
        mohc.writelines(f"{path}, {mip}, {inst}, {model}, {exp}, {ens}, {table}, {var}, "
                        f"{allocation_tb}, {current_tb}, {percent_used}\n")

    else:
        replica = True

    return replica


def resize(allocation_tb, scale, replica_accumulated_saving):
    new_allocation = allocation_tb * scale
    saving = allocation_tb - new_allocation
    replica_accumulated_saving += saving

    return new_allocation, saving, replica_accumulated_saving


def main():

    f = open(VOLSFILE, "r")
    data = json.loads(f.read())
    fileset_list = data["fileset_list"]

    replica_accumulated_saving = 0.0

    with open(HIGHRESMIP_DATA_VOLS_FILE, "w") as highres, open(MOHC_DATA_VOLS_FILE, "w") as mohc, open(REPLICA_DATA_VOLS_FILE, "w") as replica_fh:

        highres.writelines('Path, MIP, Institute, Model, Experiment, Ensemble, Table, Variable, Allocation (TB), Current Usage (TB), Percent used\n')
        mohc.writelines('Path, MIP, Institute, Model, Experiment, Ensemble, Table, Variable, Allocation (TB), Current Usage (TB), Percent used\n')
        replica_fh.writelines('Path, Allocation (TB), Current Usage (TB), Percent used, New Allocation (TB), Saving (TB), Accumulated saving (TB)\n')

        for fs in fileset_list[1:]:

            path = fs["logical_path"]
            mip, inst, model, exp, ens, table, var = get_facets(path)
            allocation_tb = round(fs["allocation"] * SCALE, 2)
            current_tb = round(fs["current_size"] * SCALE, 2)

            if allocation_tb == 0:
                percent_used = 0.00
            else:
                percent_used = round(current_tb/allocation_tb * 100., 2)

            replica = highres_and_mohc(path, mip, inst, model, exp, ens, table, var,
                                       allocation_tb, current_tb, percent_used, highres, mohc)

            if replica:

                if allocation_tb >= 5.0:
                    if percent_used >= 90.:
                        scale = 1.0
                    elif percent_used >= 60.:
                        scale = 0.8
                    elif percent_used >= 40.:
                        scale = 0.7
                    elif percent_used >= 30.:
                        scale = 0.5
                    else:
                        scale = 0.4

                elif allocation_tb >= 1.0:
                    if percent_used >= 90.:
                        scale = 1.0
                    elif percent_used >= 50.:
                        scale = 0.8
                    elif percent_used >= 30.:
                        scale = 0.6
                    else:
                        scale = 0.5
                else:
                    if percent_used >= 90.:
                        scale = 1.0
                    elif percent_used >= 50.:
                        scale = 0.8
                    else:
                        scale = 0.6
                """
                low usage - not enough information to make a decision
                or fileset nearly full
                or low allocation 
                do nothing
                """
                if allocation_tb < 0.1 or current_tb < 0.01:
                    new_allocation = allocation_tb
                    saving = 0.0

                else:
                    new_allocation, saving, replica_accumulated_saving = resize(allocation_tb, scale, replica_accumulated_saving)


                replica_fh.writelines(f"{path}, {allocation_tb}, {current_tb}, {percent_used}, "
                                      f"{new_allocation}, {saving}, {replica_accumulated_saving}\n")

    highres.close(), mohc.close(), replica_fh.close()


if __name__ == "__main__":
    """
    Prefetch via copy and paste VOLS file from save in correct location with correct date
    https://cedaarchiveapp1.ceda.ac.uk/fileset/index/?search=%2Fbadc%2Fcmip6&json
    
    Run 
    conda activate ingest_py3
    
    Now use input date in correct format:
    python deallocate_filesets.py $(date +'%Y-%m-%d')
    
    """
    main()

