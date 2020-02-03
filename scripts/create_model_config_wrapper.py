#!/usr/bin/env Python

import os
import datetime as dt
import create_model_configs
import argparse
import subprocess

ancils_dir = os.path.join(create_model_configs.cts.BASEDIR,"ancils")

parser = argparse.ArgumentParser(description='For testing file has been created')
parser.add_argument('--v', help='Test create_model_configs has worked and file exists', action="store_true")
args = parser.parse_args()

def remove_old_logs():
    """

    """
    three_days_old = dt.date.today() - dt.timedelta(days=3)
    three_days_ago = three_days_old.strftime('%Y%m%d')

    for f in os.listdir(ancils_dir):
        if not f.startswith(('model_configs_latest.txt', 'model_configs-2019-11-02.txt')):
            file_date = f.strip('.txt').split('_')[2].replace("-","")

            if not file_date.endswith('01'):
                if int(file_date) < int(three_days_ago):
                    #print("I will delete {}".format(os.path.join(ancils_dir, f)))
                    os.remove(os.path.join(ancils_dir, f))

def check_file_creation(today_filename):
    if os.path.exists(today_filename):
        print("Today's file {} has been created".format(today_filename))
    else:
        print("Today's file was not created")

def main():

    create_model_configs.main()

    if args.v:
        check_file_creation(os.path.join(ancils_dir, "model_configs_{}.txt".format(dt.datetime.today().isoformat().split('T')[0])))

    remove_old_logs()


if __name__ == "__main__":

    main()