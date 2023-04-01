#!/usr/bin/env python3

import os
from typing import List, Set, Dict
import collections


def find_occurrences(
    main_file: os.PathLike,
    queries: List[str],
    commands: List[str],
    root_dir: os.PathLike,
):
    """Recursively find all files in a project
    assuming they are included using the \input command,
    and find unique occurrences of a list of potential commands (e.g. \cite)
    as well as the counts of commands (e.g. \begin{figure})
    """
    # dirname, fname = os.path.split(main_file)
    with open(os.path.join(root_dir, main_file), "r") as f:
        lines = f.readlines()
    instances = []
    occurrences = collections.defaultdict(set)
    command_counts = collections.defaultdict(int)

    for line in lines:
        # check if we have a new input file
        if line.startswith("%"):
            continue
        if line.startswith("\\input{"):
            x = line.split("{")[1].split("}")[0]
            x = x.translate(x.maketrans("", "", "\"'"))  # remove any inverted commas
            if ".tex" not in x:
                x += ".tex"
            instances.append(x)

        # check our queries
        for q in queries:
            l = line
            while l.find(q) != -1:

                start = l.find(q) + len(q)
                end = l.find("}", start)
                occurrences[q].add(l[start:end])
                l = l[end:]

        # check our command counts
        for c in commands:
            command_counts[c] += line.count(c)

    # find subfiles:
    sub_files = []
    for f in instances:

        sf, occ, cmd = find_occurrences(
            os.path.join(root_dir, f), queries, commands, root_dir
        )
        sub_files += sf
        for k, vs in occ.items():
            occurrences[k].update(vs)
        for k, v in cmd.items():
            command_counts[k] += v

    instances += sub_files
    return instances, occurrences, command_counts


def count_occurrences(occurrences: Dict[str, Set[str]]):
    counts = collections.defaultdict(int)
    for k, vs in occurrences.items():
        for v in vs:
            if v == "":
                continue
            counts[k] += 1
    return counts


def process_project(
    main_file: os.PathLike, unique_queries: List[str], commands: List[str]
):

    """Given a main tex file, find the counts of various commands in the project

    :param main_file: path to the main tex file
    :param unique_queries: list of strings of commands we want to find the
                number of unique instances of (e.g. \cite)
    :param commands: list of strings of commands we want to find the number of occurences of
    :returns:

    """
    root_dir, _ = os.path.split(main_file)
    x, occs, cmds = find_occurrences(main_file, unique_queries, commands, root_dir)
    counts = count_occurrences(occs)
    for k, v in counts.items():
        cmds[k] = v
    return cmds


if __name__ == "__main__":
    main_tex = "/home/pez/phd/dlis/dlis-paper-git/00-main.tex"
    queries = ["\\cite{"]
    commands = ["\\begin{figure*}", "\\begin{figure}", "\\includegraphics["]
    x, occs, cmds = find_occurrences(main_tex, queries, commands)
    x = list(set(x))

    print(x)
    print(occs)
    counts = count_occurrences(occs)
    print(counts)
    print(cmds)
