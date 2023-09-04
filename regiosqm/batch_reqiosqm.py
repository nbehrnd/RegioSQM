#!/usr/bin/python3

# name:    batch_regiosqm.py
# author:  nbehrnd@yahoo.com
# license: 2020-2021, MIT
# date:    2020-09-24 (YYYY-MM-DD)
# edit:    <2023-09-04 Mon>
#
"""This is a moderator script to interact with regiosqm.py."""

# modules of Python's standard library:
import argparse
import datetime
import os
import shutil
import subprocess as sub
from platform import python_version
import zipfile

# non-standard libraries:
import openbabel
import numpy
import rdkit

import regiosqm


def get_args():
    """Provide a minimal menu to the CLI."""
    parser = argparse.ArgumentParser(
        description='Moderator script for regiosqm.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-a',
        '--all',
        action='store_true',
        help='Process all _smiles.csv files in the current folder.')

    group.add_argument(
        '-s',
        '--smiles',
        default="",
        help='Process only one manually given single SMILES string.')

    group.add_argument('files',
                       metavar='FILE(S)',
                       nargs='*',
                       default=[],
                       help='Manual input of .smi file(s) to process.')

    return parser.parse_args()


def specific_smiles(entry=""):
    """Enable the submission of a specific SMILES string."""
    register = []
    start_file = str("special_smiles.csv")

    try:
        with open(start_file, mode="w", encoding="utf8") as newfile:
            retain = str(f"special\t{entry}")
            newfile.write(retain)
        register.append(start_file)
    except OSError:
        print(f"Error writing file '{start_file}'.  Exit.")

    return register


def input_collector():
    """Process all suitable input files."""
    register = []
    for file in os.listdir("."):
        if file.endswith("_smiles.csv"):
            register.append(file)

    register.sort(key=str.lower)
    return register


def prepare_scrutiny(entry="", input_file="", conf_file=""):
    """Set up initial .sdf, then .mop MOPAC input files."""
    print(f"Set up scrutiny for EAS group '{entry}'")

    prep = str(f"python3 regiosqm.py -g {input_file} > {conf_file}")
    work = sub.Popen(prep, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT)
    work.wait()


def engage_mopac(entry=""):
    """Engage MOPAC on four CPUs"""
    print(f"Now, MOPAC is working on {entry} data.")
    compute = str('ls *.mop | parallel -j4 "mopac {}"')
    work = sub.Popen(compute, shell=True)
    work.wait()


def analyze_mopac_results(entry="", input_file="", conf_file="", result=""):
    """Inspect MOPAC's results, write tables and .svg."""
    print(f"Analysis of MOPAC's work for EAS group '{entry}'")
    analyze = str(f"python3 regiosqm.py -a {input_file} {conf_file} > {result}")

    work = sub.Popen(analyze, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT)
    work.wait()


def characterize_scrutiny(entry="", input_file=""):
    """Characterize the setup of the scrutiny.

    Any change of the tools used may affect which site(s) is / are
    predicted as the more likely to react during an electrophilic
    aromatic substitution.  Thus, the versions of the script's tools
    are permanently recorded."""

    parameter_log = ''.join([entry, "_parameter.log"])

    # Retrieve the version of MOPAC from a MOPAC .out file.
    for file in os.listdir("."):
        if file.endswith(".arc"):
            reference_file = str(file)
            break

    with open(reference_file, mode="r", encoding="utf8") as source:
        content = source.readlines()
        mopac_version_line = str(content[4])
        mopac_version_info = mopac_version_line.strip()

    # Write the report about the present scrutiny.
    try:
        with open(parameter_log, mode="w", encoding="utf8") as newfile:
            newfile.write("Parameters of the scrutiny:\n\n")

            newfile.write(f"input set: {input_file}\n")

            today = datetime.date.today()
            newfile.write(f"date:      {today} (YYYY-MM-DD)\n")

            newfile.write(f"Python:    {python_version()}\n")
            newfile.write(f"RegioSQM:  {regiosqm.__version__}\n")

            newfile.write(f"OpenBabel: {openbabel.__version__}\n")
            newfile.write(f"RDKit:     {rdkit.__version__}\n")
            newfile.write(f"numpy:     {numpy.__version__}\n")

            newfile.write(f"MOPAC:     {mopac_version_info[6:]}\n")

            newfile.write("\nEND")

        print(f"File '{parameter_log}' reports the setup of the analysis.")
    except OSError:
        print(f"Unable to report the analysis' setup to file '{parameter_log}'.")


def space_cleaning(entry="", input_file="", conf_file="", result=""):
    """Archive all relevant data in a .zip file."""
    deposit = str(entry).split("_smiles")[0]
    os.mkdir(deposit)

    parameter_log = ''.join([deposit, "_parameter.log"])

    move_by_extension = [
        ".arc", ".den", ".end", ".mop", ".out", ".res", ".sdf", ".svg"
    ]
    move_per_run = [input_file, conf_file, result, parameter_log]
    to_move = move_by_extension + move_per_run
    for element in to_move:
        for file in os.listdir("."):
            if file.endswith(element):
                shutil.move(file, deposit)

    zip_filename = "".join([deposit, ".zip"])
    backup_zip = zipfile.ZipFile(zip_filename, "w")
    for folders, subfolders, filenames in os.walk(deposit):
        backup_zip.write(deposit)
        for filename in filenames:
            backup_zip.write(os.path.join(deposit, filename))

    shutil.rmtree(deposit)
    print(f"Analysis of EAS group '{deposit}' is completed.\n")


def main():
    """Joining the functions together"""
    args = get_args()
    if args.smiles:
        smiles = args.smiles
        smi_files = specific_smiles(smiles)
    elif args.all:
        smi_files = input_collector()
    else:
        # Ensure each group of SMILES is submitted once
        smi_files = list(set(args.files))
    smi_files.sort(key=str.lower)
    for smi_file in smi_files:

        entry = str(smi_file).split("_smiles.csv")[0]
        input_file = str(smi_file)
        conf_file = str(smi_file).split("_smiles.csv")[0] + str("_conf.csv")
        result = str(smi_file).split("_smiles.csv")[0] + str("_results.csv")

        try:
            prepare_scrutiny(entry, input_file, conf_file)
            engage_mopac(entry)

            analyze_mopac_results(entry, input_file, conf_file, result)

            characterize_scrutiny(entry, input_file)
            space_cleaning(smi_file, input_file, conf_file, result)
        except OSError:
            continue


if __name__ == "__main__":
    main()
