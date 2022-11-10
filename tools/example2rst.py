# Python code
#
# See the accompanying LICENSE file.
#
# The purpose of this file is to produce rst output interspersed into
# the the text of the example code

# Imports
import string, sys, os, re


def indentof(l):
    return l[:len(l) - len(l.lstrip())]


def docapture(filename):
    code = []
    code.append(outputredirector)
    counter = 0
    for line in open(filename, "rt"):
        if line.strip() == "from __future__ import annotations":
            # only allowed at start and we have outputredirector header
            continue
        line = line[:-1]  # strip off newline
        if line.lstrip().startswith("#@@CAPTURE"):
            code.append(indentof(line) + "opto('.tmpop-%s-%d')" % (filename, counter))
            counter += 1
        elif line.lstrip().startswith("#@@ENDCAPTURE"):
            code.append(indentof(line) + "opnormal()")
        else:
            code.append(line)
    code = "\n".join(code)
    exec(code, {})


outputredirector = """
from __future__ import annotations
import sys
origsysstdout=None
def opto(fname):
  global origsysstdout
  origsysstdout=sys.stdout,fname
  sys.stdout=open(fname, "wt")
def opnormal():
  sys.stdout.close()
  sys.stdout=origsysstdout[0]
  sys.stdout.write(open(origsysstdout[1], "rt").read())
"""


def rstout(filename):
    op = []
    op.extend("""
.. Automatically generated by example2rst.py.  Edit that file
   not this one!

Example
=======

This code demonstrates usage of APSW.  It gives you a good overview of
all the things that can be done.  Also included is output so you can
see what gets printed when you run the code.

.. code-block:: python
""".split("\n"))
    counter = 0
    prefix = "    "
    for line in open(filename, "rt"):
        line = line.rstrip()
        if "@@CAPTURE" in line:
            continue
        if "@@ENDCAPTURE" not in line:
            if line.startswith("#") and "@@" in line:
                p = line.index("@@")
                name = line[p + 2:].strip()
                line = line[:p].rstrip()
                for i in range(-1, -99, -1):  # look backwards for first non-comment line
                    if not op[i].strip().startswith("#"):
                        op.insert(i, "")
                        op.insert(i, ".. _" + name + ":")
                        op.insert(i, "")
                        op.insert(i, ".. code-block:: python")
                        op.insert(i, "")
                        break
            op.append(prefix + line)
            continue
        op.append("")
        op.append(".. code-block:: output")
        op.append("")
        for line in open(".tmpop-%s-%d" % (filename, counter), "rt"):
            line = line.rstrip()
            op.append("   " + line)
        op.append("")
        op.append(".. code-block:: python")
        op.append("")
        os.remove(".tmpop-%s-%d" % (filename, counter))
        counter += 1

    ### Peephole optimizations

    while True:
        b4 = op
        # get rid of double blank lines
        op2 = []
        for i in range(len(op)):
            if i + 1 < len(op) and len(op[i].strip()) == 0 and len(op[i + 1].strip()) == 0:
                continue
            if len(op[i].strip()) == 0:  # make whitespace only lines be zero length
                op2.append("")
            else:
                op2.append(op[i])
        op = op2

        # if there is a code block followed by a label then drop the code block
        op2 = []
        for i in range(len(op)):
            if i + 2 < len(op) and op[i].startswith(".. code-block::") and op[i + 2].startswith(".. _"):
                continue
            op2.append(op[i])
        op = op2

        if op == b4:
            break

    return op


if __name__ == "__main__":
    docapture("example-code.py")
    op = rstout("example-code.py")
    open("doc/example.rst", "wt").write("\n".join(op) + "\n")
