import os
import subprocess
import datetime
from shutil import copyfile
import glob

today = datetime.datetime.today().strftime("%Y-%m-%d")
FILESETS_FILE = os.path.join("../vols/volume_tables", "cmip6_fileset_volumes_{}.txt".format(today))
FILESETS_FILE_LATEST = "../vols/cmip6_fileset_volumes_latest.txt"
CREPP_FILE = "/gws/nopw/j04/cmip6_prep_vol1/cmip6_data_vols/cmip6_filesets_volume_lookup.txt"
MAX_FILESET_SIZE = 50.


def shadows(a, b):
    a_bits = a.split('/')
    b_bits = b.split('/')

    for i, bit in enumerate(a_bits):
        if bit == '*':
            b_bits[i] = '*'

    a1 = '/'.join(a_bits)
    b1 = '/'.join(b_bits)

    return b1.startswith(a1)


def read_fileset_vols(file):
    """
    Read in the fileset volumes from the given file and returns the paths

    :param file:
    :return: [list] of paths
    """
    with open(file) as r:
        filesets = r.readlines()

    paths = []
    for fs in filesets:
        fs_parts = fs.strip().split(' ')
        #print(fs_parts)
        path, vol = fs_parts[0], float(fs_parts[1].strip())
        paths.append(path)
        if vol > MAX_FILESET_SIZE:
            print("Max fileset size {} exceeded {}:{}".format(MAX_FILESET_SIZE, path, vol))

    return paths


def find_all_simulations(flist, sim):
    """
    Finds all simulations in the list given.

    :param flist:
    :param sim:
    :return: [list]
    """
    if not flist:
        return None
    else:
        matches = []
        for fs in flist:
            if fs.startswith(sim):
                matches.append(fs)

        return matches

def check_fileset_consistency(filesets):
    """
    Checking the fileset is consistent in a way that CREPP understands before creating them.

    :param filesets:
    :return:
    """
    fileset_paths = read_fileset_vols(filesets)
    simulations = set()
    for path in fileset_paths:
        simulation = '/'.join(path.split('/')[:5])
        simulations.add(simulation)

    for sim in list(simulations):
        all_matching_sims = find_all_simulations(fileset_paths, sim)

        for i, fs in enumerate(all_matching_sims[:-2]):
            # check no shadows
            if shadows(all_matching_sims[i], all_matching_sims[i + 1]):
                raise Exception('Shadows {}'.format(all_matching_sims[i], all_matching_sims[i + 1]))

def remove_old_vol_logs():
    """
    This function removes old logs from the vols/volume_tables/ dir. This is any text file older than today's date.
    It keeps any file created on the first day of the month.

    :return:
    """
    today = datetime.date.today()
    todays_date = today.strftime('%Y%m%d')

    for f in os.listdir("../vols/volume_tables/"):
        if not f.startswith(('cmip6_fileset_volumes_2019','cmip6_fileset_volumes_2020-01', 'cmip6_fileset_volumes_2020-02', 'cmip6_fileset_volumes_2020-03', 'cmip6_fileset_volumes_2020-04-07' )):
            file_date = f.strip('.txt').split('_')[3].replace("-","")
            if not file_date.endswith('01'):
                if int(file_date) < int(todays_date):
                    cmd1 = "git add {}".format(os.path.join("../vols/volume_tables/",f))
                    subprocess.run(cmd1, shell=True)
                    cmd = "git rm -f {}".format(os.path.join("../vols/volume_tables/",f))
                    subprocess.run(cmd, shell=True)

def main():

    # Create concatenated single file table
    p1 = subprocess.Popen("cat ../vols/simulation_level_fileset_vols/*.txt > {}".format(FILESETS_FILE), shell=True)
    p1.wait()
    if not os.path.exists(FILESETS_FILE):
        raise Exception("{} does not exist".format(FILESETS_FILE))

    # Check the list of filesets is consistent in a way that CREPP understands
    check_fileset_consistency(FILESETS_FILE)

    # move checked list into new location
    os.unlink(FILESETS_FILE_LATEST)
    os.symlink(FILESETS_FILE, FILESETS_FILE_LATEST)
    copyfile(FILESETS_FILE, CREPP_FILE)

    remove_old_vol_logs()

if __name__ == "__main__":
    main()
