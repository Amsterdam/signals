# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import re
import sys
from pathlib import Path

HEADER_PATTERN = re.compile(r'^# SPDX-License-Identifier: MPL-2\.0(\n|\r\n)^# Copyright \(C\)', re.MULTILINE)


def check(root):
    fails = []
    for path in Path(root).rglob('*.py'):
        with open(path, 'r') as f:
            if not HEADER_PATTERN.match(f.read()):
                fails.append(path)

    if fails:
        print(f'The following {len(fails)} files have no SPDX header:\n')
        for path in fails:
            print(path)
        sys.exit(1)

if __name__ == '__main__':
    check(sys.argv[1])
