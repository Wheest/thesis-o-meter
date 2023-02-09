#!/usr/bin/env python3

import os
import re
import json
import subprocess
from datetime import datetime


def get_timestamp(filename):
    # extract timestamp from filename
    # filename is of the form:
    # 2023-02-03 18:36:22.json
    # return timestamp as a datetime object
    timestamp = filename.split(".")[0]
    return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")


def get_most_recent_file(directory) -> str:
    # get the most recent file in the directory
    # return the filename
    files = os.listdir(directory)
    most_recent_file = None
    most_recent_timestamp = None
    for filename in files:
        timestamp = get_timestamp(filename)
        if most_recent_timestamp is None or timestamp > most_recent_timestamp:
            most_recent_timestamp = timestamp
            most_recent_file = filename
    return most_recent_file


def data_has_changed(data, log_dir: os.PathLike):
    prev = get_most_recent_file(log_dir)
    if prev is None:
        return True

    with open(os.path.join(log_dir, prev)) as f:
        old_data = json.load(f)

    for k, v in data.items():
        if k == "time":
            continue
        if k not in old_data:
            return True
        if old_data[k] != v:
            return True
    return False


def generate_pdf(main_tex: os.PathLike):
    # generate the PDF
    ps = subprocess.Popen(
        ("pdflatex", main_tex), stdout=subprocess.PIPE, cwd=os.path.dirname(main_tex)
    )
    ps.wait()


def get_page_count(main_pdf: os.PathLike) -> int:
    output = subprocess.check_output(
        ("pdfinfo", main_pdf), cwd=os.path.dirname(main_pdf)
    ).decode("utf-8")
    assert "Pages:" in output, f"Output of page count invalid: {output}"
    info = output.split("\n")

    for i in info:
        if "Pages:" in i:
            p = int(i.split()[1])

    return p
