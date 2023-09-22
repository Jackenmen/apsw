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
    PyObject *Mapping;
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
    PyObject *add_note;
    PyObject *close;
    PyObject *connection_hooks;
    PyObject *cursor;
    PyObject *error_offset;
    PyObject *excepthook;
    PyObject *execute;
    PyObject *executemany;
    PyObject *extendedresult;
    PyObject *final;
    PyObject *get;
    PyObject *inverse;
    PyObject *result;
    PyObject *step;
    PyObject *value;
    PyObject *xAccess;
    PyObject *xCheckReservedLock;
    PyObject *xClose;
    PyObject *xCurrentTime;
    PyObject *xCurrentTimeInt64;
    PyObject *xDelete;
    PyObject *xDeviceCharacteristics;
    PyObject *xDlClose;
    PyObject *xDlError;
    PyObject *xDlOpen;
    PyObject *xDlSym;
    PyObject *xFileControl;
    PyObject *xFileSize;
    PyObject *xFullPathname;
    PyObject *xGetLastError;
    PyObject *xGetSystemCall;
    PyObject *xLock;
    PyObject *xNextSystemCall;
    PyObject *xOpen;
    PyObject *xRandomness;
    PyObject *xRead;
    PyObject *xSectorSize;
    PyObject *xSetSystemCall;
    PyObject *xSleep;
    PyObject *xSync;
    PyObject *xTruncate;
    PyObject *xUnlock;
    PyObject *xWrite;
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
    Py_CLEAR(apst.Mapping);
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
    Py_CLEAR(apst.add_note);
    Py_CLEAR(apst.close);
    Py_CLEAR(apst.connection_hooks);
    Py_CLEAR(apst.cursor);
    Py_CLEAR(apst.error_offset);
    Py_CLEAR(apst.excepthook);
    Py_CLEAR(apst.execute);
    Py_CLEAR(apst.executemany);
    Py_CLEAR(apst.extendedresult);
    Py_CLEAR(apst.final);
    Py_CLEAR(apst.get);
    Py_CLEAR(apst.inverse);
    Py_CLEAR(apst.result);
    Py_CLEAR(apst.step);
    Py_CLEAR(apst.value);
    Py_CLEAR(apst.xAccess);
    Py_CLEAR(apst.xCheckReservedLock);
    Py_CLEAR(apst.xClose);
    Py_CLEAR(apst.xCurrentTime);
    Py_CLEAR(apst.xCurrentTimeInt64);
    Py_CLEAR(apst.xDelete);
    Py_CLEAR(apst.xDeviceCharacteristics);
    Py_CLEAR(apst.xDlClose);
    Py_CLEAR(apst.xDlError);
    Py_CLEAR(apst.xDlOpen);
    Py_CLEAR(apst.xDlSym);
    Py_CLEAR(apst.xFileControl);
    Py_CLEAR(apst.xFileSize);
    Py_CLEAR(apst.xFullPathname);
    Py_CLEAR(apst.xGetLastError);
    Py_CLEAR(apst.xGetSystemCall);
    Py_CLEAR(apst.xLock);
    Py_CLEAR(apst.xNextSystemCall);
    Py_CLEAR(apst.xOpen);
    Py_CLEAR(apst.xRandomness);
    Py_CLEAR(apst.xRead);
    Py_CLEAR(apst.xSectorSize);
    Py_CLEAR(apst.xSetSystemCall);
    Py_CLEAR(apst.xSleep);
    Py_CLEAR(apst.xSync);
    Py_CLEAR(apst.xTruncate);
    Py_CLEAR(apst.xUnlock);
    Py_CLEAR(apst.xWrite);
}

/* returns zero on success, -1 on error */
static int
init_apsw_strings()
{
    if ((0 == (apst.Begin = PyUnicode_FromString("Begin"))) || (0 == (apst.BestIndex = PyUnicode_FromString("BestIndex"))) || (0 == (apst.BestIndexObject = PyUnicode_FromString("BestIndexObject"))) || (0 == (apst.Close = PyUnicode_FromString("Close"))) || (0 == (apst.Column = PyUnicode_FromString("Column"))) || (0 == (apst.ColumnNoChange = PyUnicode_FromString("ColumnNoChange"))) || (0 == (apst.Commit = PyUnicode_FromString("Commit"))) || (0 == (apst.Connect = PyUnicode_FromString("Connect"))) || (0 == (apst.Create = PyUnicode_FromString("Create"))) || (0 == (apst.Destroy = PyUnicode_FromString("Destroy"))) || (0 == (apst.Disconnect = PyUnicode_FromString("Disconnect"))) || (0 == (apst.Eof = PyUnicode_FromString("Eof"))) || (0 == (apst.Filter = PyUnicode_FromString("Filter"))) || (0 == (apst.FindFunction = PyUnicode_FromString("FindFunction"))) || (0 == (apst.Mapping = PyUnicode_FromString("Mapping"))) || (0 == (apst.Next = PyUnicode_FromString("Next"))) || (0 == (apst.Open = PyUnicode_FromString("Open"))) || (0 == (apst.Release = PyUnicode_FromString("Release"))) || (0 == (apst.Rename = PyUnicode_FromString("Rename"))) || (0 == (apst.Rollback = PyUnicode_FromString("Rollback"))) || (0 == (apst.RollbackTo = PyUnicode_FromString("RollbackTo"))) || (0 == (apst.Rowid = PyUnicode_FromString("Rowid"))) || (0 == (apst.Savepoint = PyUnicode_FromString("Savepoint"))) || (0 == (apst.ShadowName = PyUnicode_FromString("ShadowName"))) || (0 == (apst.Sync = PyUnicode_FromString("Sync"))) || (0 == (apst.UpdateChangeRow = PyUnicode_FromString("UpdateChangeRow"))) || (0 == (apst.UpdateDeleteRow = PyUnicode_FromString("UpdateDeleteRow"))) || (0 == (apst.UpdateInsertRow = PyUnicode_FromString("UpdateInsertRow"))) || (0 == (apst.add_note = PyUnicode_FromString("add_note"))) || (0 == (apst.close = PyUnicode_FromString("close"))) || (0 == (apst.connection_hooks = PyUnicode_FromString("connection_hooks"))) || (0 == (apst.cursor = PyUnicode_FromString("cursor"))) || (0 == (apst.error_offset = PyUnicode_FromString("error_offset"))) || (0 == (apst.excepthook = PyUnicode_FromString("excepthook"))) || (0 == (apst.execute = PyUnicode_FromString("execute"))) || (0 == (apst.executemany = PyUnicode_FromString("executemany"))) || (0 == (apst.extendedresult = PyUnicode_FromString("extendedresult"))) || (0 == (apst.final = PyUnicode_FromString("final"))) || (0 == (apst.get = PyUnicode_FromString("get"))) || (0 == (apst.inverse = PyUnicode_FromString("inverse"))) || (0 == (apst.result = PyUnicode_FromString("result"))) || (0 == (apst.step = PyUnicode_FromString("step"))) || (0 == (apst.value = PyUnicode_FromString("value"))) || (0 == (apst.xAccess = PyUnicode_FromString("xAccess"))) || (0 == (apst.xCheckReservedLock = PyUnicode_FromString("xCheckReservedLock"))) || (0 == (apst.xClose = PyUnicode_FromString("xClose"))) || (0 == (apst.xCurrentTime = PyUnicode_FromString("xCurrentTime"))) || (0 == (apst.xCurrentTimeInt64 = PyUnicode_FromString("xCurrentTimeInt64"))) || (0 == (apst.xDelete = PyUnicode_FromString("xDelete"))) || (0 == (apst.xDeviceCharacteristics = PyUnicode_FromString("xDeviceCharacteristics"))) || (0 == (apst.xDlClose = PyUnicode_FromString("xDlClose"))) || (0 == (apst.xDlError = PyUnicode_FromString("xDlError"))) || (0 == (apst.xDlOpen = PyUnicode_FromString("xDlOpen"))) || (0 == (apst.xDlSym = PyUnicode_FromString("xDlSym"))) || (0 == (apst.xFileControl = PyUnicode_FromString("xFileControl"))) || (0 == (apst.xFileSize = PyUnicode_FromString("xFileSize"))) || (0 == (apst.xFullPathname = PyUnicode_FromString("xFullPathname"))) || (0 == (apst.xGetLastError = PyUnicode_FromString("xGetLastError"))) || (0 == (apst.xGetSystemCall = PyUnicode_FromString("xGetSystemCall"))) || (0 == (apst.xLock = PyUnicode_FromString("xLock"))) || (0 == (apst.xNextSystemCall = PyUnicode_FromString("xNextSystemCall"))) || (0 == (apst.xOpen = PyUnicode_FromString("xOpen"))) || (0 == (apst.xRandomness = PyUnicode_FromString("xRandomness"))) || (0 == (apst.xRead = PyUnicode_FromString("xRead"))) || (0 == (apst.xSectorSize = PyUnicode_FromString("xSectorSize"))) || (0 == (apst.xSetSystemCall = PyUnicode_FromString("xSetSystemCall"))) || (0 == (apst.xSleep = PyUnicode_FromString("xSleep"))) || (0 == (apst.xSync = PyUnicode_FromString("xSync"))) || (0 == (apst.xTruncate = PyUnicode_FromString("xTruncate"))) || (0 == (apst.xUnlock = PyUnicode_FromString("xUnlock"))) || (0 == (apst.xWrite = PyUnicode_FromString("xWrite"))))
    {
        fini_apsw_strings();
        return -1;
    }
    return 0;
}