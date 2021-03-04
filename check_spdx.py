from pathlib import Path
import re
import sys

HEADER_PATTERN = re.compile(r'^# SPDX-License-Identifier: MPL-2\.0\n^# Copyright \(C\)', re.MULTILINE)


def check(root):
    fails = []
    for path in Path(root).rglob('*.py'):
        with open(path, 'r') as f:
            if not (match := HEADER_PATTERN.match(f.read())):
                fails.append(path)

    if fails:
        print(f'# The following {len(fails)} files have no SPDX header')
        for path in fails:
            print(path)


if __name__ == '__main__':
    check(sys.argv[1])
