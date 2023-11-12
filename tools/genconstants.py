#!/usr/bin/env python3

from __future__ import annotations

import sys
import tempfile
import urllib.request
import pathlib

import apsw
import apsw.ext
import apsw.shell

title_to_mapping = {
    "Allowed return values from sqlite3_txn_state()": "txn_state",
    "Authorizer Action Codes": "authorizer_function",
    "Authorizer Return Codes": "authorizer_return_codes",
    "Checkpoint Mode Values": "wal_checkpoint",
    "Compile-Time Library Version Numbers": None,
    "Configuration Options": "config",
    "Conflict resolution modes": "conflict_resolution_modes",
    "Constants Defining Special Destructor Behavior": None,
    "Database Connection Configuration Options": "db_config",
    "Device Characteristics": "device_characteristics",
    "Extended Result Codes": "extended_result_codes",
    "File Locking Levels": "locking_level",
    "Flags For File Open Operations": "open_flags",
    "Flags for sqlite3_deserialize()": None,
    "Flags for sqlite3_serialize": None,
    "Flags for the xAccess VFS method": "access",
    "Flags for the xShmLock VFS method": "xshmlock_flags",
    "Function Flags": "function_flags",
    "Fundamental Datatypes": None,
    "Maximum xShmLock index": None,
    "Mutex Types": None,
    "Prepare Flags": "prepare_flags",
    "Prepared Statement Scan Status": None,
    "Prepared Statement Scan Status Opcodes": None,
    "Result Codes": "result_codes",
    "Run-Time Limit Categories": "limits",
    "SQL Trace Event Codes": "trace_codes",
    "Standard File Control Opcodes": "file_control",
    "Status Parameters": "status",
    "Status Parameters for database connections": "db_status",
    "Status Parameters for prepared statements": "statement_status",
    "Synchronization Type Flags": "sync",
    "Testing Interface Operation Codes": None,
    "Text Encodings": None,
    "Virtual Table Configuration Options": "virtual_table_configuration_options",
    "Virtual Table Constraint Operator Codes": "bestindex_constraints",
    "Virtual Table Scan Flags": "virtual_table_scan_flags",
    "Win32 Directory Types": None,
    "FTS5 Token Flag": "fts5_token_flags",
    "FTS5 Tokenize Reason": "fts5_tokenize_reason",
}

base_sqlite_url = "https://sqlite.org/"
with tempfile.NamedTemporaryFile() as f:
    f.write(urllib.request.urlopen(base_sqlite_url + "toc.db").read())
    f.flush()

    db = apsw.Connection(f.name)
    db.execute(pathlib.Path(__file__).with_name("tocupdate.sql").read_text())
    db.row_trace = apsw.ext.DataClassRowFactory(dataclass_kwargs={"frozen": True})

    constants: dict[str, list[str]] = {}

    cur_mapping_title = None

    for row in db.execute("select * from toc where type='constant' order by title, name"):
        if row.title != cur_mapping_title:
            constants[row.title] = []
            cur_mapping_title = row.title
        assert row.name not in constants[row.title]
        constants[row.title].append(row.name)

unknown = {title for title in constants if title not in title_to_mapping}
if unknown:
    sys.exit(f"Unknown title mapping { unknown }")

header = """\
/*
    Generated by genconstants.py from SQLite's toc.db

    Deal with those - do not edit this file
*/

/* returns zero on success, -1 on error */
static int
add_apsw_constants(PyObject *module)
{
    PyObject *the_dict;

    assert(!PyErr_Occurred());
"""
trailer = """
    assert(!PyErr_Occurred());
    return 0;
}
"""

per_item = """\
    if (!the_dict)
    {
        assert(PyErr_Occurred());
        return -1;
    }
    if (PyModule_AddObject(module, "mapping_NAME", the_dict))
    {
        assert(PyErr_Occurred());
        Py_DECREF(the_dict);
        return -1;
    }
"""

op: list[str] = [header]

top_level: set[str] = set()

for title, cons in constants.items():
    if not title_to_mapping[title]:
        continue
    op.append(f"    /* { title } */")
    op.append('    the_dict = Py_BuildValue(')
    op.append('        "{' + "siis" * len(cons) + '}",')
    for c in cons:
        top_level.add(c)
        op.append(f'        "{ c }", { c }, { c }, "{ c }",')
    op[-1] = op[-1].rstrip(",") + ");"
    op.append(per_item.replace("NAME", title_to_mapping[title]))

op.append("    if (")
for i, c in enumerate(sorted(top_level)):
    sor = "|| " if i else ""
    op.append(f'        { sor }PyModule_AddIntConstant(module, "{ c }", { c })')
op[-1] += ")"
op.append("        return -1;")

op.append(trailer)

print("\n".join(op))