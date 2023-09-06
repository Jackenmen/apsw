#!/usr/bin/python

import sys
import subprocess

proto = """
static long long
APSW_FaultInjectControl(const char *faultfunction, const char *filename, const char *funcname, int linenum, const char *args);

"""

call_pattern = """
({
    __auto_type _res = 0 ? PySet_New(__VA_ARGS__) : 0;

    _res = (typeof (_res))APSW_FaultInjectControl("PySet_New", __FILE__, __func__, __LINE__, #__VA_ARGS__);

    if ((typeof (_res))0x1FACADE == _res)
       _res = PySet_New(__VA_ARGS__);
    else if ((typeof(_res))0x2FACADE == _res)
    {
        PySet_New(__VA_ARGS__);
        _res = (typeof (_res))18;
    }
    _res;
})
"""


def get_definition(name, use_name):
    t = call_pattern.replace("PySet_New", use_name)
    if name != use_name:
        # put back pretty name in string passed to APSW_FaultInjectControl
        t = t.replace(f'"{ use_name }"', f'"{ name }"')
    t = t.strip().split("\n")
    maxlen = max(len(l) for l in t)
    for i in range(len(t) - 1):
        t[i] += " " * (maxlen - len(t[i])) + " \\\n"
    return "".join(t)


def genfile(symbols):
    res = []
    res.append(f"""\
/*  DO NOT EDIT THIS FILE
    This file is generated by tools/genfaultinject.py
    Edit that not this */
#ifdef APSW_TESTFIXTURES

#ifndef APSW_FAULT_INJECT_INCLUDED
{ proto }
#define APSW_FAULT_INJECT_INCLUDED
#endif

#ifdef APSW_FAULT_CLEAR
""")
    for s in sorted(symbols):
        res.append(f"#undef { s }")
    res.append("\n#else\n")
    for s in sorted(symbols):
        if s in call_map:
            res.append(f"#undef {s}")
        res.append(f"#define {s}(...) \\\n{ get_definition( s, call_map.get(s, s)) }")
    res.append("#endif")
    res.append("#endif")
    return "\n".join(res)


returns = {
    # return a pointer, NULL on failure
    "pointer":
    """
            convert_value_to_pyobject convert_column_to_pyobject  allocfunccbinfo
            apsw_strdup convertutf8string MakeExistingException get_window_function_context

            PyModule_Create2 PyErr_NewExceptionWithDoc PySet_New
            PyUnicode_New  PyUnicode_AsUTF8 PyObject_GetAttr _PyObject_New PyUnicode_FromString
            PyObject_Str PyUnicode_AsUTF8AndSize PyTuple_New PyDict_New Py_BuildValue PyList_New
            PyWeakref_NewRef PyMem_Calloc PyLong_FromLong PyObject_GetIter
            PyObject_CallObject PyLong_AsInt PyUnicode_FromStringAndSize
            PySequence_GetItem PyLong_FromLongLong PySequence_GetSlice PyBytes_FromStringAndSize
            PyFloat_FromDouble  PyBool_FromLong PyCode_NewEmpty PyFloat_AsDouble
            PyIter_Next PyList_GetItem PyList_SetItem PyLong_FromVoidPtr PyMapping_GetItemString PyNumber_Float
            PyNumber_Long PySequence_Fast PySequence_List PySequence_SetItem
            PyFrame_New PyStructSequence_NewType PyStructSequence_New
            PyMem_Realloc PyUnicode_FromFormat
            PyObject_VectorcallMethod PyObject_Vectorcall
            """.split(),
    # numeric return
    "sqlite":
    """
            sqlite3_aggregate_context sqlite3_autovacuum_pages
            sqlite3_backup_finish sqlite3_backup_init
            sqlite3_backup_step sqlite3_bind_blob sqlite3_bind_blob64
            sqlite3_bind_double sqlite3_bind_int sqlite3_bind_int64
            sqlite3_bind_null sqlite3_bind_pointer sqlite3_bind_text
            sqlite3_bind_text64 sqlite3_bind_value
            sqlite3_bind_zeroblob sqlite3_bind_zeroblob64
            sqlite3_blob_open sqlite3_blob_read sqlite3_blob_reopen
            sqlite3_blob_write sqlite3_busy_handler
            sqlite3_busy_timeout
            sqlite3_clear_bindings sqlite3_close sqlite3_close_v2
            sqlite3_collation_needed sqlite3_column_name
            sqlite3_complete sqlite3_config sqlite3_create_collation
            sqlite3_create_collation_v2 sqlite3_create_function
            sqlite3_create_function_v2 sqlite3_create_module
            sqlite3_create_module_v2 sqlite3_create_window_function
            sqlite3_db_cacheflush sqlite3_db_config sqlite3_db_status
            sqlite3_declare_vtab sqlite3_deserialize
            sqlite3_drop_modules sqlite3_enable_load_extension
            sqlite3_enable_shared_cache sqlite3_exec
            sqlite3_expanded_sql sqlite3_initialize
            sqlite3_load_extension sqlite3_malloc sqlite3_malloc64
            sqlite3_mprintf sqlite3_normalized_sql sqlite3_open
            sqlite3_open_v2 sqlite3_overload_function
            sqlite3_prepare_v3 sqlite3_realloc
            sqlite3_realloc64 sqlite3_result_zeroblob64
            sqlite3_set_authorizer sqlite3_shutdown sqlite3_status64
            sqlite3_table_column_metadata sqlite3_threadsafe
            sqlite3_trace_v2 sqlite3_vfs_register
            sqlite3_vfs_unregister sqlite3_vtab_config
            sqlite3_vtab_in_next sqlite3_vtab_rhs_value
            sqlite3_wal_autocheckpoint sqlite3_wal_checkpoint_v2
            """.split(),
    # py functions that return a number to indicate failure
    "number":
    """
        PyType_Ready PyModule_AddObject PyModule_AddIntConstant PyLong_AsLong
        PyLong_AsLongLong PyObject_GetBuffer PyList_Append PyDict_SetItemString
        PyObject_SetAttr _PyBytes_Resize PyDict_SetItem PyList_SetSlice
        PyObject_IsTrue PySequence_Size PySet_Add PyObject_IsTrueStrict
        PyStructSequence_InitType2 PyList_Size

        PyBuffer_IsContiguous

        connection_trace_and_exec getfunctionargs
        """.split(),
        # PyBuffer_IsContiguous is on an error path although the
        # function itself can't error
}

# some calls like Py_BuildValue are #defined to _Py_BuildValue_SizeT
# so deal with that here
call_map = {
    "Py_BuildValue": "_Py_BuildValue_SizeT",
    "PyArg_ParseTuple": "_PyArg_ParseTuple_SizeT",
    "Py_VaBuildValue": "_Py_VaBuildValue_SizeT",
}

# double check no dupes
for k, v in returns.items():
    if len(set(v)) != len(v):
        seen = set()
        for val in v:
            if val in seen:
                print(f"Duplicate item { val } in { k }")
                sys.exit(1)
            else:
                seen.add(val)

# these don't provide meaning for fault injection
no_error = set("""PyBuffer_Release PyDict_GetItem PyMem_Free PyDict_GetItemString PyErr_Clear
    PyErr_Display PyErr_Fetch PyErr_Format PyErr_NoMemory PyErr_NormalizeException
    PyErr_Occurred PyErr_Print PyErr_Restore PyErr_SetObject PyEval_RestoreThread
    PyEval_SaveThread PyGILState_Ensure PyGILState_Release PyOS_snprintf
    PyObject_CheckBuffer PyObject_ClearWeakRefs PyObject_GC_UnTrack PyObject_HasAttr
    PyThreadState_Get PyThread_get_thread_ident PyTraceBack_Here
    PyType_IsSubtype PyUnicode_CopyCharacters PyWeakref_GetObject _Py_Dealloc
    _Py_HashBytes _Py_NegativeRefcount _Py_RefTotal PyThreadState_GetFrame
""".split())

# these could error but are only used in a small number of places where
# errors are already dealt with
no_error.update("""PyArg_ParseTuple PyBytes_AsString PyErr_GivenExceptionMatches PyFrame_GetBack
    PyImport_ImportModule PyLong_AsLongAndOverflow PyLong_AsVoidPtr
    PyObject_IsInstance PySys_GetObject PyErr_ExceptionMatches
    PyErr_SetString PyStructSequence_SetItem PyObject_Print Py_EnterRecursiveCall
    Py_GetRecursionLimit Py_LeaveRecursiveCall Py_SetRecursionLimit _PyErr_ChainExceptions

""".split())


def check_dll(fname, all):
    not_seen = set()
    for line in subprocess.run(["nm", "-u", fname], text=True, capture_output=True, check=True).stdout.split("\n"):
        if not line.strip().startswith("U") or "@" in line or "Py" not in line:
            continue
        _, sym = line.split()
        if sym in all:
            assert sym not in no_error, f"{ sym } in all and no_error"

        if sym in call_map.values():
            for k, v in call_map.items():
                if sym == v:
                    sym = k
                    break
            else:
                1 / 0

        if (sym in all or sym in no_error or sym.endswith("_Check") or sym.endswith("_Type") or sym.endswith("Struct")
                or sym.startswith("PyExc_")):
            continue

        not_seen.add(sym)

    print(sorted(not_seen))
    print(len(not_seen), "items")


if __name__ == '__main__':
    all = set()
    for v in returns.values():
        all.update(v)
    if sys.argv[1].endswith(".h"):
        r = genfile(all)
        open(sys.argv[1], "wt").write(r)
    else:
        check_dll(sys.argv[1], all)