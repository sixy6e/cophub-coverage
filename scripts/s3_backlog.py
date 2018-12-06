#!/usr/bin/env python

import subprocess
from pathlib import Path
import pandas

START, END = ["2016-04-01", "2018-11-01"]
YEAR_MONTHS = pandas.date_range(start=START, end=END, freq='MS')

for i in range(1, len(YEAR_MONTHS)):
    start_date = YEAR_MONTHS[i-1].strftime('%Y-%m-%d')
    end_date = YEAR_MONTHS[i].strftime('%Y-%m-%d')
    outdir = Path("/home/sixy/data/SARA/MonthlyCoverageMaps").joinpath(YEAR_MONTHS[i-1].strftime('%Y-%m'))

    for product in ["OL_1_EFR___", "OL_2_LFR___", "OL_2_WFR___"]:
        cmd = [
            "cophub_overlaps",
            "--collection", "S3",
            "-q", "startDate={}".format(start_date),
            "-q", "completionDate={}".format(end_date),
            "-q", "productType={}".format(product),
            "--outdir", outdir
        ]

        print("executing:")
        print(cmd)
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print("Failed to execute command:")
            print(cmd)
