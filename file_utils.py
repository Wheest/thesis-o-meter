#!/usr/bin/env python3

import os
import re
import json
import subprocess
import multiprocessing
from datetime import datetime


def get_timestamp(filename):
    # extract timestamp from filename
    # filename is of the form:
    # 2023-02-03-18:36:22.json
    # return timestamp as a datetime object
    timestamp = filename.split(".")[0]
    return datetime.strptime(timestamp, "%Y-%m-%d-%H:%M:%S")


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


def press_enter(pipe):
    """Covers the case that PDF latex wants us to press enter
    for whatever reason.
    """
    try:
        while True:
            # Send the Enter key every 5 seconds
            time.sleep(5)
            pipe.write("\n")
            pipe.flush()
    except BrokenPipeError:
        pass  # The main process has completed, ignore the error


def generate_pdf(main_tex: os.PathLike):
    with subprocess.Popen(
        ("pdflatex", main_tex),
        stdin=subprocess.PIPE,
        cwd=os.path.dirname(main_tex),
    ) as process:
        enter_manager = multiprocessing.Process(
            target=press_enter, args=(process.stdin,)
        )
        enter_manager.start()
        process.wait()
        enter_manager.terminate()


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
