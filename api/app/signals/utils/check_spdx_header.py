# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
"""
This script will scan all python files in the repository and checks if the SPDX header is present.
"""
import glob
import mmap
import os


def find_in_file(search_string, filepath):
    with open(filepath) as f:
        s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return s.find(bytes(search_string, 'utf-8')) != -1


def search_in_directory(search_string, path, recursive=True, verbosity=0):
    if verbosity >= 1:
        print(f'Search "{search_string}" in all python files in the "{os.path.abspath(path)}" '
              f'{"(recursively)" if recursive else ""}')

    verbosity = verbosity if verbosity in range(3) else 0

    not_found_in_files = []
    files = glob.glob(r'' + path + "**/*.py", recursive=recursive)
    for file in files:
        filepath = os.path.abspath(file)
        if not find_in_file(search_string, filepath):
            not_found_in_files.append(filepath)

    if verbosity >= 1:
        print(f'Total number of files checked: {len(files)}')
        print(f'Total number of files checked OK: {len(files)-len(not_found_in_files)}')
        if not_found_in_files:
            print(f'Total number of files NOT containing the search string: {len(not_found_in_files)}')

    if not_found_in_files:
        for not_found_in_file in not_found_in_files:
            print(f'- {not_found_in_file}')


if __name__ == '__main__':
    ROOT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../../../')
    search_in_directory(search_string='# SPDX-License-Identifier: MPL-2.0', path=ROOT_DIR, recursive=True, verbosity=0)
