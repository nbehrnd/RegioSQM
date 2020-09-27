# name:    batch_regiosqm.py
# author:  nbehrnd@yahoo.com
# license: 2020, MIT
# date:    2020-09-24 (YYYY-MM-DD)
# edit:    2020-09-25 (YYYY-MM-DD)
#
"""Run multiple regiosqm analyses over multiple .csv in batches.

Intended for the CLI of Python3 in Linux, for multiple EAS_smiles.csv
in one folder, this script will moderate each step otherwise manually
executed step to predict the sites most susceptible to EAS:

+ prepare the scrutiny, which manually were the call of

  python regiosqm.py -g EAS_smiles.csv > EAS_conf.csv

  which equally triggers OpenBabel to generte the MOPAC input files

+ call MOPAC to work on the data by call of

  ls *.mop | parallel -j4 "/opt/mopac/MOPAC2016.exe {}"

  which for improvement of performance is parallelized (GNU parallel)

+ perform the initial analysis of MOPAC's results, i.e.

  python regiosqm.py -a EAS_smiles.csv EAS_conf.csv > EAS_results.csv

  creating both the handy tables of result, as well as the .svg

+ offer space cleaning by stashing all files about the current EAS
  group scrutinized into a zip-compressed archive

In short, it does what Al Sweigart called 'Automate the boring stuff
with Python' translating into launching a batch of analyses to run
without required further interaction till the next morning."""

import os
import subprocess as sub

register = []

for file in os.listdir("."):
    if str(file).endswith("_smiles.csv"):
        register.append(file)
register.sort()

for entry in register:
    try:
        # prepare the analysis:
        # pattern: python regiosqm.py -g input_smiles.csv > input_conf.csv
        print("work for EAS group: {}".format(entry))
        input_file = str(entry)
        conf_file = str(entry).split("_smiles.csv")[0] + str("_conf.csv")
        resultat = str(entry).split("_smiles.csv")[0] + str("_res.csv")

        print("generate input for regiosqm for EAS group: {}".format(entry))
        command_1 = str("python3 regiosqm.py -g {} > {}".format(
            input_file, conf_file))
        sub.call(command_1, shell=True)

        # run MOPAC:
        print("MOPAC works for EAS group: {}".format(entry))
        command_2 = str(
            'ls *.mop | parallel -j4 "/opt/mopac/MOPAC2016.exe {}"')
        sub.call(command_2, shell=True)

        # analyze MOPAC's results:
        print("Analysis of MOPAC's work for EAS group: {}".format(entry))
        command_3 = str("python3 regiosqm.py -a {} {} > {}".format(
            input_file, conf_file, resultat))
        sub.call(command_3, shell=True)

        # space cleaning, put the relevant data into a common folder:
        print("space cleaning / compression for EAS group: {}".format(entry))
        new_folder = str(entry).split("_smiles.csv")[0]
        os.mkdir(new_folder)

        command_4 = str(
            "mv *.arc *.den *.end *.mop *.out *.res *.sdf *.svg {}".format(
                new_folder))
        sub.call(command_4, shell=True)

        command_5 = str("mv {} {} {} {}".format(input_file, conf_file,
                                                resultat, new_folder))
        sub.call(command_5, shell=True)

        # space cleaning, compress this folder:
        archive_name = str(entry).split("_smiles.csv")[0] + str(".zip")
        command_6 = str("zip -r {} {}".format(archive_name, new_folder))
        sub.call(command_6, shell=True)

        # space cleaning: remove the intermediate folder
        command_7 = str("rm -r {}".format(new_folder))
        sub.call(command_7, shell=True)
    except:
        continue