#!/usr/bin/env python

import subprocess
from pathlib import Path
import pandas

MODES = ["IW", "SM", "EW"]
PRODUCTS = ["SLC", "GRD"]
ORBITS = ["Ascending", "Descending"]
COMBINATIONS = [
    ("GRD", "IW", "Ascending"),
    ("GRD", "IW", "Descending"),
    ("GRD", "SM", "Ascending"),
    ("GRD", "SM", "Descending"),
    ("GRD", "EW", "Ascending"),
    ("GRD", "EW", "Descending"),
    ("SLC", "IW", "Ascending"),
    ("SLC", "IW", "Descending"),
    ("SLC", "SM", "Ascending"),
    ("SLC", "SM", "Descending")
]
START, END = ["2014-10-01", "2018-11-01"]
YEAR_MONTHS = pandas.date_range(start=START, end=END, freq='MS')

for i in range(1, len(YEAR_MONTHS)):
    start_date = YEAR_MONTHS[i-1].strftime('%Y-%m-%d')
    end_date = YEAR_MONTHS[i].strftime('%Y-%m-%d')
    outdir = Path("/home/sixy/data/SARA/MonthlyCoverageMaps").joinpath(YEAR_MONTHS[i-1].strftime('%Y-%m'))
    for combo in COMBINATIONS:
        cmd = [
            "cophub_overlaps",
            "--collection", "S1",
            "-q", "startDate={}".format(start_date),
            "-q", "completionDate={}".format(end_date),
            "-q", "productType={}".format(combo[0]),
            "-q", "sensorMode={}".format(combo[1]),
            "-q", "orbitDirection={}".format(combo[2]),
            "--outdir", outdir
        ]

        print("executing:")
        print(cmd)
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print("Failed to execute command:")
            print(cmd)
