#!/usr/bin/env python3

import os
import re
import json
import pandas as pd
import subprocess
import multiprocessing
from plyer import notification
from datetime import datetime
import time


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
        if ".json" not in filename:
            continue
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
    while True:
        try:
            # Send the Enter key every 5 seconds
            time.sleep(5)
            pipe.write("\n")
            pipe.flush()
        except BrokenPipeError:
            break  # The main process has completed, ignore the error
        except Exception as e:
            continue


def clear_aux_func(root_dir: os.PathLike):
    # Iterate through the files in the root directory
    for filename in os.listdir(root_dir):
        # Check if the file ends with '.aux'
        if filename.endswith(".aux"):
            # Get the full path to the file
            file_path = os.path.join(root_dir, filename)

            # Remove the file
            os.remove(file_path)


def generate_pdf(main_tex: os.PathLike, timeout: int = 100, clear_aux: bool = False):

    if clear_aux:
        dirname, _ = os.path.split(main_tex)
        clear_aux_func(dirname)

    with subprocess.Popen(
        ("pdflatex", "-shell-escape", main_tex),
        stdin=subprocess.PIPE,
        cwd=os.path.dirname(main_tex),
    ) as process:
        enter_manager = multiprocessing.Process(
            target=press_enter, args=(process.stdin,)
        )
        enter_manager.start()

        # Change the process.wait() to process.poll() with a timeout loop
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if process.poll() is not None:  # None means the process is still running
                break  # The process has finished
            time.sleep(5)  # Check the process status every 5 seconds

        # Clean up and create a notification if necessary
        enter_manager.terminate()

        exit_code = process.poll()

        if exit_code is None:
            process.terminate()
            process.wait()
            # a quick and dirty way to fix some stalls is to clear the `.aux` cache
            if not clear_aux:
                return generate_pdf(main_tex, timeout, True)

            msg = f"The PDF generation process has been terminated due to taking longer than {timeout/60} minutes."
            notification.notify(
                title="PDF Generation Stalled",
                message=msg,
                timeout=5,
            )
            raise Exception(msg)
        elif exit_code != 0:
            msg = f"The PDF generation process has finished with a non-zero error code: {exit_code}"
            notification.notify(
                title="PDF Generation Error",
                message=msg,
                timeout=5,
            )
            raise Exception(msg)


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


def proccess_data(log_dir: os.PathLike, output_path: os.PathLike):
    data = pd.DataFrame()
    datas = []
    for file in os.listdir(log_dir):
        if file.endswith(".json"):
            file_path = os.path.join(log_dir, file)
            with open(file_path) as f:
                datas.append(pd.DataFrame(json.load(f), index=[0]))

    data = pd.concat(datas, ignore_index=True)

    data.fillna(0, inplace=True)

    data["date"] = pd.to_datetime(data["time"])
    data["word_count"] = data["word_count"].astype(int)
    data["page_count"] = data["page_count"].astype(int)
    data["references"] = data["references"].astype(int)
    data["figures"] = data["figures"].astype(int)
    data["tables"] = data["tables"].astype(int)
    data["\\includegraphics["] = data["\\includegraphics["].astype(int)
    del data["time"]
    data = data.sort_values(by="date")
    data.index = data["date"]
    data.to_csv(output_path)
