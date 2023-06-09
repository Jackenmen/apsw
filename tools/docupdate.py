# python
#
# See the accompanying LICENSE file.
#
# various automagic documentation updates

import sys
import os
import textwrap
import re

# get the download file names correct

version = sys.argv[1]
url = "  <https://github.com/rogerbinns/apsw/releases/download/" + version + "/%s>`__"
version_no_r = version.split("-r")[0]

download = open("doc/install.rst", "rt").read()

op = []
incomment = False
for line in open("doc/install.rst", "rt"):
    line = line.rstrip()
    if line == ".. downloads-begin":
        op.append(line)
        incomment = True
        op.append("")
        op.append("* `apsw-%s.zip" % (version, ))
        op.append(url % ("apsw-%s.zip" % version))
        op.append("  (Source, includes this HTML Help)")
        op.append("")
        op.append("* `apsw-%s-sigs.zip " % (version, ))
        op.append(url % ("apsw-%s-sigs.zip" % version))
        op.append("  GPG signatures for all files")
        op.append("")
        continue
    if line == ".. downloads-end":
        incomment = False
    if incomment:
        continue
    if line.lstrip().startswith("$ gpg --verify apsw"):
        line = line[:line.index("$")] + "$ gpg --verify apsw-%s.zip.asc" % (version, )
    op.append(line)

op = "\n".join(op)
if op != download:
    open("doc/install.rst", "wt").write(op)

# put usage and description for speedtest into benchmark

import apsw.speedtest

benchmark = open("doc/benchmarking.rst", "rt").read()

op = []
incomment = False
for line in open("doc/benchmarking.rst", "rt"):
    line = line.rstrip()
    if line == ".. speedtest-begin":
        op.append(line)
        incomment = True
        op.append("")
        op.append(".. code-block:: text")
        op.append("")
        op.append("    $ python3 -m apsw.speedtest --help")
        cols = os.environ.get("COLUMNS", None)
        os.environ["COLUMNS"] = "80"
        for line in apsw.speedtest.parser.format_help().split("\n"):
            op.append("    " + line)
        if cols is None:
            del os.environ["COLUMNS"]
        else:
            os.environ["COLUMNS"] = cols
        op.append("")
        op.append("    $ python3 -m apsw.speedtest --tests-detail")
        for line in apsw.speedtest.tests_detail.split("\n"):
            op.append("    " + line)
        op.append("")
        continue
    if line == ".. speedtest-end":
        incomment = False
    if incomment:
        continue
    op.append(line)

op = "\n".join(op)
if op != benchmark:
    open("doc/benchmarking.rst", "wt").write(op)

# shell stuff

import apsw, io, apsw.shell

shell = apsw.shell.Shell()
incomment = False
op = []
for line in open("doc/shell.rst", "rt"):
    line = line.rstrip()
    if line == ".. help-begin:":
        op.append(line)
        incomment = True
        op.append("")

        s = io.StringIO()

        def tw(*args):
            return 80

        def backtickify(s):
            s = s.group(0)
            if s in {"SQL", "APSW", "TCL", "C", "HTML", "JSON", "CSV", "TSV"}:
                return s
            if s == "'3'": # example in command_parameter
                return "``'3'``"
            if s.startswith("'") and s.endswith("'"):
                s = s.strip("'")
                return f"``{ s }``"
            if all(c.upper() == c and not c.isdigit() for c in s):
                return f"``{ s }``"
            return s

        shell.stderr = s
        shell._terminal_width = tw
        shell.command_help([])

        for k, v in shell._help_info.items():
            op.append(f".. _shell-cmd-{ k }:")
            op.append(".. index::")
            op.append("    single: " + v[0].lstrip(".").split()[0] + " (Shell command)")
            op.append("")
            op.append(v[0].lstrip("."))
            op.append("-" * len(v[0].lstrip(".")))
            op.append("")
            op.append("*" + v[1] + "*")
            op.append("")
            if v[2]:
                for i, para in enumerate(v[2]):
                    if not para:
                        op.append("")
                    else:
                        para = para.replace("\\", "\\\\")
                        if para.lstrip() == para:
                            para = re.sub(r"'?[\w%]+'?", backtickify, para)
                        if para.endswith(":"):
                            c = i + 1
                            while not v[2][c]:
                                c += 1
                            if v[2][c].lstrip() != v[2][c]:
                                para += ":"
                        op.extend(textwrap.wrap(para, width=80))
                op.append("")

        continue
    if line == ".. usage-begin:":
        op.append(line)
        incomment = True
        op.append("")
        op.append(".. code-block:: text")
        op.append("")
        op.extend(["  " + x for x in shell.usage().split("\n")])
        op.append("")
        continue
    if line == ".. help-end:":
        incomment = False
    if line == ".. usage-end:":
        incomment = False
    if incomment:
        continue
    op.append(line)

op = "\n".join(op)
if op != open("doc/shell.rst", "rt").read():
    open("doc/shell.rst", "wt").write(op)
