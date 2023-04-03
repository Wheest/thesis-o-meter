#!/usr/bin/env python3
import os
import argparse
import subprocess
import git
from datetime import datetime
import json
import collections

from file_utils import data_has_changed, generate_pdf, get_page_count, proccess_data
from tex_file_processor import process_project


def get_word_count(main_tex: os.PathLike) -> int:
    ps = subprocess.Popen(
        ("detex", main_tex), stdout=subprocess.PIPE, cwd=os.path.dirname(main_tex)
    )
    output = subprocess.check_output(("wc", "--w"), stdin=ps.stdout)
    ps.wait()
    return int(output)


def git_pull(git_dir: os.PathLike):
    g = git.cmd.Git(git_dir)
    g.pull()


def main(args):

    if not os.path.isdir(args.git_dir):
        raise ValueError(f"Could not find project git dir `{args.git_dir}`")

    main_tex_file = os.path.join(args.git_dir, args.main_tex)
    if not os.path.isfile(main_tex_file):
        raise ValueError(f"Could not find main TeX file `{main_tex_file}`")

    # Update to latest version
    git_pull(args.git_dir)

    # generate the PDF that we will parse some of our data from
    generate_pdf(main_tex_file)

    # Collect and store data from PDF
    data = collections.defaultdict(int)
    data["time"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    data["word_count"] = get_word_count(main_tex_file)
    main_pdf_file = main_tex_file.replace(".tex", ".pdf")
    data["page_count"] = get_page_count(main_pdf_file)

    # get info from our tex files
    unqiue_queries = ["\\cite{"]
    commands = [
        "\\begin{figure*}",
        "\\begin{figure}",
        "\\includegraphics[",
        "\\begin{table}",
        "\\begin{table*}",
    ]
    counts = process_project(main_tex_file, unqiue_queries, commands)

    # combine values with meaningful names
    for (x, y) in [
        ("references", "\\cite{"),
        ("figures", "\\begin{figure*}"),
        ("figures", "\\begin{figure}"),
        ("tables", "\\begin{table*}"),
        ("tables", "\\begin{table}"),
    ]:
        data[x] += counts[y]
        del counts[y]

    for k, v in counts.items():
        data[k] = v

    # Check if we need to save the data to file
    os.makedirs(args.log_dir, exist_ok=True)
    if not data_has_changed(data, args.log_dir):
        return

    # Create logfile, if data has changed
    with open(
        os.path.join(args.log_dir, data["time"].replace(" ", "-") + ".json"), "w"
    ) as f:
        json.dump(data, f, indent=2)

    # Update CSV that can be used for plotting
    proccess_data(args.log_dir, os.path.join(args.log_dir, "thesis_data.csv"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get the word count for a TeX project")
    parser.add_argument(
        "--git_dir",
        required=True,
        type=str,
        help="Path to main TeX file of project",
    )
    parser.add_argument(
        "--main_tex",
        required=True,
        type=str,
        help="Path to main TeX file of project",
    )
    parser.add_argument(
        "--log_dir",
        type=str,
        required=True,
        help="Location to store logged data",
    )
    args = parser.parse_args()
    main(args)
