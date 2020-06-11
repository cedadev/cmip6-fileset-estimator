#!/usr/bin/env Python

import os
import datetime as dt
import create_model_configs
import argparse
import subprocess

ANCILS_DIR = os.path.join(create_model_configs.cts.BASEDIR, "ancils")

def remove_old_logs():
    """
    This function removes old logs from the ancils dir. This is any text file older than 3 days. It keeps any file created
    on the first day of the month.

    :return: no return
    """
    three_days_old = dt.date.today() - dt.timedelta(days=2)
    three_days_ago = three_days_old.strftime('%Y%m%d')

    for f in os.listdir(ANCILS_DIR):
        if not f.startswith(('model_configs_latest.txt', 'model_configs-2019-11-02.txt')):
            file_date = f.strip('.txt').split('_')[2].replace("-","")

            if not file_date.endswith('01'):
                if int(file_date) < int(three_days_ago):
                    cmd1 = "git add {}".format(os.path.join(ANCILS_DIR, f))
                    subprocess.run(cmd1, shell=True)
                    cmd = "git rm -f {}".format(os.path.join(ANCILS_DIR, f))
                    subprocess.run(cmd, shell=True)

def check_file_creation(today_filename):
    """
    This function checks the file output from create_model_config script exists. This will only run if the '--v'
    argument is given on the command line. This is just a test.

    :param today_filename: str [filename]
    :return: print statement at terminal
    """

    if os.path.exists(today_filename):
        print("Today's file {} has been created".format(today_filename))
    else:
        print("Today's file was not created")

def main():

    parser = argparse.ArgumentParser(description='For testing file has been created')
    parser.add_argument('--v', help='Test create_model_configs has worked and file exists', action="store_true")
    args = parser.parse_args()
    #create_model_configs.main()

    if args.v:
        check_file_creation(os.path.join(ANCILS_DIR, "model_configs_{}.txt".format(dt.datetime.today().isoformat().split('T')[0])))

    remove_old_logs()


if __name__ == "__main__":

    main()