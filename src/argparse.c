
/* to speed this up gendocstrings can generate something like this
   that uses the string length as a hash

    switch(strlen(kwname))
    {
        case 7:
          if(0==strcmp(kwname, "hkjdshfkjd")) return 4;
          if(0==strcmp(kwname, "sdsdshfkjd")) return 2;
          return -1;

        case 2:
          if(0==strcmp(kwname, "ab")) return 1;
          return -1;

        default: return -1;
    }
*/
static int
ARG_WHICH_KEYWORD(PyObject *item, const char *kwlist[], size_t n_kwlist, const char **kwname)
{
    *kwname = PyUnicode_AsUTF8(item);
    size_t cmp;
    for (cmp = 0; cmp < n_kwlist; cmp++)
    {
        if (0 == strcmp(*kwname, kwlist[cmp]))
            return cmp;
    }
    return -1;
}

#define ARG_PROLOG(maxpos_args, kwname_list)                                              \
    static const char *kwlist[] = {kwname_list};                                          \
    const int maxpos = maxpos_args;                                                       \
    const char *unknown_keyword = NULL;                                                   \
    const int maxargs = Py_ARRAY_LENGTH(kwlist);                                          \
    PyObject *myargs[maxargs];                                                            \
    PyObject **useargs = (PyObject **)fast_args;                                          \
    size_t actual_nargs = PyVectorcall_NARGS(fast_nargs);                                 \
    if (actual_nargs > maxpos)                                                            \
        goto too_many_args;                                                               \
    if (fast_kwnames)                                                                     \
    {                                                                                     \
        useargs = myargs;                                                                 \
        memcpy(useargs, fast_args, sizeof(PyObject *) * actual_nargs);                    \
        memset(useargs + actual_nargs, 0, sizeof(PyObject *) * (maxargs - actual_nargs)); \
        for (int i = 0; i < PyTuple_GET_SIZE(fast_kwnames); i++)                          \
        {                                                                                 \
            PyObject *item = PyTuple_GET_ITEM(fast_kwnames, i);                           \
            int which = ARG_WHICH_KEYWORD(item, kwlist, maxargs, &unknown_keyword);       \
            if (which == -1)                                                              \
                goto unknown_keyword_arg;                                                 \
            if (useargs[which])                                                           \
                goto pos_and_keyword;                                                     \
            useargs[which] = fast_args[actual_nargs + i];                                 \
        }                                                                                 \
    }                                                                                     \
    int optind = 0;

#define ARG_MANDATORY                                       \
    if ((size_t)optind >= actual_nargs || !useargs[optind]) \
        goto missing_required;

#define ARG_OPTIONAL      \
    if (!useargs[optind]) \
        optind++;         \
    else

#define ARG_EPILOG(retval, usage)                                                                                                \
    if ((size_t)optind == actual_nargs)                                                                                          \
        goto success;                                                                                                            \
    /* unreachable exceeding actual_nargs here? */                                                                               \
    assert(0);                                                                                                                   \
    /* this wont be hit but is here to stop warnings about unused label */                                                       \
    goto missing_required;                                                                                                       \
    too_many_args:                                                                                                               \
    PyErr_Format(PyExc_TypeError, "Too many arguments %d (min %d max %d) provided to %s", actual_nargs, maxpos, maxargs, usage); \
    goto error_return;                                                                                                           \
    missing_required:                                                                                                            \
    PyErr_Format(PyExc_TypeError, "Parameter #%d %s of %s expected", optind + 1, kwlist[optind], usage);                         \
    goto error_return;                                                                                                           \
    unknown_keyword_arg:                                                                                                         \
    PyErr_Format(PyExc_TypeError, "'%s' is an invalid keyword argument for %s", unknown_keyword, usage);                         \
    goto error_return;                                                                                                           \
    pos_and_keyword:                                                                                                             \
    PyErr_Format(PyExc_TypeError, "argument '%s' given by name and position for %s", unknown_keyword, usage);                    \
    goto error_return;                                                                                                           \
    param_error:                                                                                                                 \
    /* ::TODO:: add note about kwlist[optind] */                                                                                 \
    goto error_return;                                                                                                           \
    error_return:                                                                                                                \
    assert(PyErr_Occurred());                                                                                                    \
    return retval;                                                                                                               \
    success:

#define ARG_pyobject(varname)                                                                \
    if (useargs[optind])                                                                     \
    {                                                                                        \
        varname = useargs[optind];                                                           \
        optind++;                                                                            \
    }                                                                                        \
    else /* this won't be hit, and is here to ensure the label is used to avoid a warning */ \
        goto param_error;

#define ARG_pointer(varname)                     \
    varname = PyLong_AsVoidPtr(useargs[optind]); \
    if (PyErr_Occurred())                        \
        goto param_error;                        \
    optind++;

#define ARG_str(varname)                         \
    varname = PyUnicode_AsUTF8(useargs[optind]); \
    if (!varname)                                \
        goto param_error;                        \
    optind++;

#define ARG_PyUnicode(varname)                                                                \
    if (PyUnicode_Check(useargs[optind]))                                                     \
    {                                                                                         \
        varname = useargs[optind];                                                            \
        optind++;                                                                             \
    }                                                                                         \
    else                                                                                      \
    {                                                                                         \
        PyErr_Format(PyExc_TypeError, "Expected a str not %s", Py_TypeName(useargs[optind])); \
        goto param_error;                                                                     \
    }

#define ARG_optional_str(varname)   \
    if (Py_IsNone(useargs[optind])) \
    {                               \
        varname = NULL;             \
        optind++;                   \
    }                               \
    else                            \
        ARG_str(varname);

#define ARG_Callable(varname)                                                                      \
    if (PyCallable_Check(useargs[optind]))                                                         \
    {                                                                                              \
        varname = useargs[optind];                                                                 \
        optind++;                                                                                  \
    }                                                                                              \
    else                                                                                           \
    {                                                                                              \
        PyErr_Format(PyExc_TypeError, "Expected a callable not %s", Py_TypeName(useargs[optind])); \
        goto param_error;                                                                          \
    }

#define ARG_optional_Callable(varname) \
    if (Py_IsNone(useargs[optind]))    \
    {                                  \
        varname = NULL;                \
        optind++;                      \
    }                                  \
    else                               \
        ARG_Callable(varname);

#define ARG_bool(varname)                             \
    varname = PyObject_IsTrueStrict(useargs[optind]); \
    if (varname == -1)                                \
        goto param_error;                             \
    optind++;

#define ARG_int(varname)                     \
    varname = PyLong_AsInt(useargs[optind]); \
    if (varname == -1 && PyErr_Occurred())   \
        goto param_error;                    \
    optind++;

#define ARG_int64(varname)                        \
    varname = PyLong_AsLongLong(useargs[optind]); \
    if (varname == -1 && PyErr_Occurred())        \
        goto param_error;                         \
    optind++;

#define ARG_TYPE_CHECK(varname, type, cast)                                                                   \
    switch (PyObject_IsInstance(useargs[optind], type))                                                       \
    {                                                                                                         \
    case 1:                                                                                                   \
        varname = (cast)useargs[optind];                                                                      \
        optind++;                                                                                             \
        break;                                                                                                \
    case 0:                                                                                                   \
        PyErr_Format(PyExc_TypeError, "Expected %s not %s", Py_TypeName(type), Py_TypeName(useargs[optind])); \
        /* fallthru */                                                                                        \
    case -1:                                                                                                  \
        goto param_error;                                                                                     \
    }

#define ARG_Connection(varname) ARG_TYPE_CHECK(varname, (PyObject *)&ConnectionType, Connection *)

/* PySequence_Check is too strict and rejects things that are
    accepted by PySequence_Fast like sets and generators,
    so everything is accepted */
#define ARG_optional_Bindings(varname) \
    if (Py_IsNone(useargs[optind]))    \
        varname = NULL;                \
    else                               \
        varname = useargs[optind];     \
    optind++;

#define ARG_optional_str_URIFilename(varname)                                                                                                     \
    if (Py_IsNone(useargs[optind]) || PyUnicode_Check(useargs[optind]) || PyObject_IsInstance(useargs[optind], (PyObject *)&APSWURIFilenameType)) \
    {                                                                                                                                             \
        varname = useargs[optind];                                                                                                                \
        optind++;                                                                                                                                 \
    }                                                                                                                                             \
    else                                                                                                                                          \
    {                                                                                                                                             \
        PyErr_Format(PyExc_TypeError, "Expected None | str | apsw.URIFilename, not %s", Py_TypeName(useargs[optind]));                            \
        goto param_error;                                                                                                                         \
    }

#define ARG_List_int_int(varname)                                                                                                        \
    if (!PyList_Check(useargs[optind]) || PyList_Size(useargs[optind]) != 2)                                                             \
    {                                                                                                                                    \
        PyErr_Format(PyExc_TypeError, "Expected a two item list of int");                                                                \
        goto param_error;                                                                                                                \
    }                                                                                                                                    \
    for (int i = 0; i < 2; i++)                                                                                                          \
    {                                                                                                                                    \
        PyObject *list_item = PyList_GetItem(useargs[optind], i);                                                                        \
        if (!list_item)                                                                                                                  \
            goto param_error;                                                                                                            \
        if (!PyLong_Check(list_item))                                                                                                    \
        {                                                                                                                                \
            PyErr_Format(PyExc_TypeError, "Function argument list[int,int] expected int for item %d not %s", i, Py_TypeName(list_item)); \
            goto param_error;                                                                                                            \
        }                                                                                                                                \
    }                                                                                                                                    \
    varname = useargs[optind];                                                                                                           \
    optind++;

#define ARG_optional_set(varname)                                                                    \
    if (Py_IsNone(useargs[optind]))                                                                  \
        varname = NULL;                                                                              \
    else if (PySet_Check(useargs[optind]))                                                           \
        varname = useargs[optind];                                                                   \
    else                                                                                             \
    {                                                                                                \
        PyErr_Format(PyExc_TypeError, "Expected None or set, not %s", Py_TypeName(useargs[optind])); \
        goto param_error;                                                                            \
    }                                                                                                \
    optind++;

#define ARG_py_buffer(varname)                                                                                                               \
    if (!PyObject_CheckBuffer(useargs[optind]))                                                                                              \
    {                                                                                                                                        \
        PyErr_Format(PyExc_TypeError, "Expected bytes or similar type that supports buffer protocol, not %s", Py_TypeName(useargs[optind])); \
        goto param_error;                                                                                                                    \
    }                                                                                                                                        \
    varname = useargs[optind];                                                                                                               \
    optind++;

typedef struct
{
    PyObject **result;
    const char *message;
} argcheck_Optional_Callable_param;

static int
argcheck_Optional_Callable(PyObject *object, void *vparam)
{
    argcheck_Optional_Callable_param *param = (argcheck_Optional_Callable_param *)vparam;
    if (Py_IsNone(object))
        *param->result = NULL;
    else if (PyCallable_Check(object))
        *param->result = object;
    else
    {
        PyErr_Format(PyExc_TypeError, "Function argument expected a Callable or None: %s", param->message);
        return 0;
    }
    return 1;
}

/* Standard PyArg_Parse considers anything truthy to be True such as
   non-empty strings, tuples etc.  This is a footgun for args eg:

      method("False")  # considered to be method(True)

   This converter only accepts bool / int (or subclasses)
*/
typedef struct
{
    int *result;
    const char *message;
} argcheck_bool_param;

static int
argcheck_bool(PyObject *object, void *vparam)
{
    argcheck_bool_param *param = (argcheck_bool_param *)vparam;

    int val = PyObject_IsTrueStrict(object);
    switch (val)
    {
    case -1:
        assert(PyErr_Occurred());
        CHAIN_EXC(
            PyErr_Format(PyExc_TypeError, "Function argument expected a bool: %s", param->message););
        return 0;
    default:
        assert(val == 0 || val == 1);
        *param->result = val;
        return 1;
    }
}

typedef struct
{
    PyObject **result;
    const char *message;
} argcheck_Optional_set_param;

static int
argcheck_Optional_set(PyObject *object, void *vparam)
{
    argcheck_Optional_set_param *param = (argcheck_Optional_set_param *)vparam;
    if (Py_IsNone(object))
    {
        *param->result = NULL;
        return 1;
    }
    if (!PySet_Check(object))
    {
        PyErr_Format(PyExc_TypeError, "Function argument expected a set: %s", param->message);
        return 0;
    }
    *param->result = object;
    return 1;
}

typedef struct
{
    PyObject **result;
    const char *message;
} argcheck_List_int_int_param;

/* Doing this here avoids cleanup in the calling function */
static int
argcheck_List_int_int(PyObject *object, void *vparam)
{
    int i;
    argcheck_List_int_int_param *param = (argcheck_List_int_int_param *)vparam;

    if (!PyList_Check(object))
    {
        PyErr_Format(PyExc_TypeError, "Function argument expected a list: %s", param->message);
        return 0;
    }

    if (PyList_Size(object) != 2)
    {
        if (!PyErr_Occurred())
            PyErr_Format(PyExc_ValueError, "Function argument expected a two item list: %s", param->message);
        return 0;
    }

    for (i = 0; i < 2; i++)
    {
        PyObject *list_item = PyList_GetItem(object, i);
        if (!list_item)
            return 0;
        if (!PyLong_Check(list_item))
        {
            PyErr_Format(PyExc_TypeError, "Function argument list[int,int] expected int for item %d: %s", i, param->message);
            return 0;
        }
    }
    *param->result = object;
    return 1;
}

static PyTypeObject APSWURIFilenameType;

typedef struct
{
    PyObject **result;
    const char *message;
} argcheck_Optional_str_URIFilename_param;

static int
argcheck_Optional_str_URIFilename(PyObject *object, void *vparam)
{
    argcheck_Optional_str_URIFilename_param *param = (argcheck_Optional_str_URIFilename_param *)vparam;

    if (Py_IsNone(object) || PyUnicode_Check(object) || PyObject_IsInstance(object, (PyObject *)&APSWURIFilenameType))
    {
        *param->result = object;
        return 1;
    }
    PyErr_Format(PyExc_TypeError, "Function argument expect None | str | apsw.URIFilename: %s", param->message);
    return 0;
}

typedef struct
{
    void **result;
    const char *message;
} argcheck_pointer_param;

static int
argcheck_pointer(PyObject *object, void *vparam)
{
    argcheck_pointer_param *param = (argcheck_pointer_param *)vparam;
    if (!PyLong_Check(object))
    {
        PyErr_Format(PyExc_TypeError, "Function argument expected int (to be used as a pointer): %s", param->message);
        return 0;
    }
    *param->result = PyLong_AsVoidPtr(object);
    return PyErr_Occurred() ? 0 : 1;
}

typedef struct
{
    PyObject **result;
    const char *message;
} argcheck_Optional_Bindings_param;

static int
argcheck_Optional_Bindings(PyObject *object, void *vparam)
{
    argcheck_Optional_Bindings_param *param = (argcheck_Optional_Bindings_param *)vparam;
    if (Py_IsNone(object))
    {
        *param->result = NULL;
        return 1;
    }
    /* PySequence_Check is too strict and rejects things that are
        accepted by PySequence_Fast like sets and generators,
        so everything is accepted */
    *param->result = object;
    return 1;
}