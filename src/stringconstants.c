/*
    Generated by genstrings.py

    Edit that - do not edit this file
*/

static struct _apsw_string_table
{
    PyObject *Begin;
    PyObject *BestIndex;
    PyObject *BestIndexObject;
    PyObject *Close;
    PyObject *Column;
    PyObject *ColumnNoChange;
    PyObject *Commit;
    PyObject *Connect;
    PyObject *Create;
    PyObject *Destroy;
    PyObject *Disconnect;
    PyObject *Eof;
    PyObject *Filter;
    PyObject *FindFunction;
    PyObject *Next;
    PyObject *Open;
    PyObject *Release;
    PyObject *Rename;
    PyObject *Rollback;
    PyObject *RollbackTo;
    PyObject *Rowid;
    PyObject *Savepoint;
    PyObject *ShadowName;
    PyObject *Sync;
    PyObject *UpdateChangeRow;
    PyObject *UpdateDeleteRow;
    PyObject *UpdateInsertRow;
    PyObject *xAccess;
    PyObject *xDelete;
    PyObject *xFullPathname;
    PyObject *xOpen;
} apst = {0};

static void
fini_apsw_strings(void)
{
    Py_CLEAR(apst.Begin);
    Py_CLEAR(apst.BestIndex);
    Py_CLEAR(apst.BestIndexObject);
    Py_CLEAR(apst.Close);
    Py_CLEAR(apst.Column);
    Py_CLEAR(apst.ColumnNoChange);
    Py_CLEAR(apst.Commit);
    Py_CLEAR(apst.Connect);
    Py_CLEAR(apst.Create);
    Py_CLEAR(apst.Destroy);
    Py_CLEAR(apst.Disconnect);
    Py_CLEAR(apst.Eof);
    Py_CLEAR(apst.Filter);
    Py_CLEAR(apst.FindFunction);
    Py_CLEAR(apst.Next);
    Py_CLEAR(apst.Open);
    Py_CLEAR(apst.Release);
    Py_CLEAR(apst.Rename);
    Py_CLEAR(apst.Rollback);
    Py_CLEAR(apst.RollbackTo);
    Py_CLEAR(apst.Rowid);
    Py_CLEAR(apst.Savepoint);
    Py_CLEAR(apst.ShadowName);
    Py_CLEAR(apst.Sync);
    Py_CLEAR(apst.UpdateChangeRow);
    Py_CLEAR(apst.UpdateDeleteRow);
    Py_CLEAR(apst.UpdateInsertRow);
    Py_CLEAR(apst.xAccess);
    Py_CLEAR(apst.xDelete);
    Py_CLEAR(apst.xFullPathname);
    Py_CLEAR(apst.xOpen);
}

/* returns zero on success, -1 on error */
static int
init_apsw_strings()
{
    if ((0 == (apst.Begin = PyUnicode_FromString("Begin"))) || (0 == (apst.BestIndex = PyUnicode_FromString("BestIndex"))) || (0 == (apst.BestIndexObject = PyUnicode_FromString("BestIndexObject"))) || (0 == (apst.Close = PyUnicode_FromString("Close"))) || (0 == (apst.Column = PyUnicode_FromString("Column"))) || (0 == (apst.ColumnNoChange = PyUnicode_FromString("ColumnNoChange"))) || (0 == (apst.Commit = PyUnicode_FromString("Commit"))) || (0 == (apst.Connect = PyUnicode_FromString("Connect"))) || (0 == (apst.Create = PyUnicode_FromString("Create"))) || (0 == (apst.Destroy = PyUnicode_FromString("Destroy"))) || (0 == (apst.Disconnect = PyUnicode_FromString("Disconnect"))) || (0 == (apst.Eof = PyUnicode_FromString("Eof"))) || (0 == (apst.Filter = PyUnicode_FromString("Filter"))) || (0 == (apst.FindFunction = PyUnicode_FromString("FindFunction"))) || (0 == (apst.Next = PyUnicode_FromString("Next"))) || (0 == (apst.Open = PyUnicode_FromString("Open"))) || (0 == (apst.Release = PyUnicode_FromString("Release"))) || (0 == (apst.Rename = PyUnicode_FromString("Rename"))) || (0 == (apst.Rollback = PyUnicode_FromString("Rollback"))) || (0 == (apst.RollbackTo = PyUnicode_FromString("RollbackTo"))) || (0 == (apst.Rowid = PyUnicode_FromString("Rowid"))) || (0 == (apst.Savepoint = PyUnicode_FromString("Savepoint"))) || (0 == (apst.ShadowName = PyUnicode_FromString("ShadowName"))) || (0 == (apst.Sync = PyUnicode_FromString("Sync"))) || (0 == (apst.UpdateChangeRow = PyUnicode_FromString("UpdateChangeRow"))) || (0 == (apst.UpdateDeleteRow = PyUnicode_FromString("UpdateDeleteRow"))) || (0 == (apst.UpdateInsertRow = PyUnicode_FromString("UpdateInsertRow"))) || (0 == (apst.xAccess = PyUnicode_FromString("xAccess"))) || (0 == (apst.xDelete = PyUnicode_FromString("xDelete"))) || (0 == (apst.xFullPathname = PyUnicode_FromString("xFullPathname"))) || (0 == (apst.xOpen = PyUnicode_FromString("xOpen"))))
    {
        fini_apsw_strings();
        return -1;
    }
    return 0;
}
