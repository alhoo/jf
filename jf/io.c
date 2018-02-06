#include <Python.h> 
#include <cstdio>
#include <string>
#include <cerrno>
#include <cstdlib>
#include <iostream>
#include <vector>

using namespace std;

typedef struct {
    PyObject_HEAD
    Py_ssize_t seq_length, enum_index;
    PyObject *sequence;
    vector<char> alldata;
    long int item; // = -1
    long int pos;
    char state[4]; // = [0, 0, 0, 0]
} JSONLgenState;

static void
jsonlgen_dealloc(JSONLgenState *jfstate)
{
    /* We need XDECREF here because when the generator is exhausted,
     * jfstate->sequence is cleared with Py_CLEAR which sets it to NULL.
    */
    Py_XDECREF(jfstate->sequence);
    Py_TYPE(jfstate)->tp_free(jfstate);
}

static PyObject *
jsonlgen_next(JSONLgenState *jfstate)
{
    /* seq_length < 0 means that the generator is exhausted.
     * Returning NULL in this case is enough. The next() builtin will raise the
     * StopIteration error for us.
    */
    if (jfstate->enum_index < jfstate->seq_length) {
        PyObject *elem = PySequence_GetItem(jfstate->sequence,
                                            jfstate->enum_index);
        /* Exceptions from PySequence_GetItem are propagated to the caller
         * (elem will be NULL so we also return NULL).
        */
        if (elem) {
            string str(PyUnicode_AsUTF8(elem));
            for(auto c: str){
                cerr << "Got character: " << c << endl;
                pos++;
                jfstate->alldata.push_back(c);
                if (c == '\'){
                  state[1] = 1
                  continue
                }
                if (state[1]){
                  state[1] = 0;
                  continue
                }
                if (c == '"'){
                  if(state[2] < 2){
                    if (jfstate->item < 0){
                      jfstate->item = pos;
                    } else if(jfstate->state[2] == 0){
                      item = -pos;
                      PyObject *result = Py_BuildValue("lO", jfstate->enum_index, elem);
                    }
                  }

                }
            }
/**
def yield_json_and_json_lines(inp):
    """Yield  json and json lines"""
    alldata = ''
    item = -1
    state = [0, 0, 0, 0]
    pos = -1
    for line in inp:
        for char in line:
            pos = pos + 1
            alldata += char
            # print(char, state, char == '\\')
            if char == '\\':
                state[1] = 1
                continue
            if state[1] > 0:
                state[1] = 0
                continue
            if char == '"':
                if state[3] < 2:
                    if item < 0:
                        item = pos
                    elif state[2] == 0:
                        yield alldata[item:pos + 1]
                        item = -pos
                state[0] = 1 - state[0]
            if state[0] > 0:
                continue
            if char == '}':
                state[2] -= 1
                if state[2] == 0 and (not (item < 0) and alldata[item] == '{'):
                    yield alldata[item:pos + 1]
                    item = -pos
            elif char == '{':
                if item < 0:
                    item = pos
                state[2] += 1
            elif char == '[':
                state[3] += 1
                if state[3] > 1 and item < 0:
                    item = pos
            elif char == ']':
                state[3] -= 1
                if state[3] == 1 and (not (item < 0) and alldata[item] == '['):
                    yield json.loads(alldata[item:pos + 1])
                    item = -pos
    if item == -1 and item < pos:
        yield alldata[0:pos + 1]
**/


            PyObject *result = Py_BuildValue("lO", jfstate->enum_index, elem);
            jfstate->enum_index++;
            return result;
        }
    }

    /* The reference to the sequence is cleared in the first generator call
     * after its exhaustion (after the call that returned the last element).
     * Py_CLEAR will be harmless for subsequent calls since it's idempotent
     * on NULL.
    */
    Py_CLEAR(jfstate->sequence);
    return NULL;
}

static PyObject *
jsonlgen_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    PyObject *sequence;

    if (!PyArg_UnpackTuple(args, "gen", 1, 1, &sequence))
        return NULL;

    /* We expect an argument that supports the sequence protocol */
    if (!PySequence_Check(sequence)) {
        PyErr_SetString(PyExc_TypeError, "jsonlgen.gen() expects a sequence");
        return NULL;
    }

    Py_ssize_t len = PySequence_Length(sequence);
    if (len == -1)
        return NULL;

    /* Create a new JSONLgenState and initialize its state - pointing to the last
     * index in the sequence.
    */
    JSONLgenState *jfstate = (JSONLgenState *)type->tp_alloc(type, 0);
    if (!jfstate)
        return NULL;

    Py_INCREF(sequence);
    jfstate->sequence = sequence;
    jfstate->seq_length = len;
    jfstate->enum_index = 0;
    jfstate->item = -1 ;
    jfstate->pos = -1 ;

    return (PyObject *)jfstate;
}

PyTypeObject PyJSONLgen_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "gen",                       /* tp_name */
    sizeof(JSONLgenState),            /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor)jsonlgen_dealloc,     /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_reserved */
    0,                              /* tp_repr */
    0,                              /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    0,                              /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    0,                              /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    PyObject_SelfIter,              /* tp_iter */
    (iternextfunc)jsonlgen_next,      /* tp_iternext */
    0,                              /* tp_methods */
    0,                              /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    PyType_GenericAlloc,            /* tp_alloc */
    jsonlgen_new,                     /* tp_new */
};



static struct PyModuleDef jsonlmodule = {
  PyModuleDef_HEAD_INIT,
  "jsonlgen",                  /* m_name */
  "",                      /* m_doc */
  -1,                      /* m_size */
};

PyMODINIT_FUNC
PyInit_jsonlgen(void)
{
    PyObject *module = PyModule_Create(&jsonlmodule);
    if (!module)
        return NULL;

    if (PyType_Ready(&PyJSONLgen_Type) < 0)
        return NULL;
    Py_INCREF((PyObject *)&PyJSONLgen_Type);
    PyModule_AddObject(module, "gen", (PyObject *)&PyJSONLgen_Type);

    return module;
}



/**
def yield_json_and_json_lines(inp):
    """Yield  json and json lines"""
    alldata = ''
    item = -1
    state = [0, 0, 0, 0]
    pos = -1
    for line in inp:
        for char in line:
            pos = pos + 1
            alldata += char
            # print(char, state, char == '\\')
            if char == '\\':
                state[1] = 1
                continue
            if state[1] > 0:
                state[1] = 0
                continue
            if char == '"':
                if state[3] < 2:
                    if item < 0:
                        item = pos
                    elif state[2] == 0:
                        yield alldata[item:pos + 1]
                        item = -pos
                state[0] = 1 - state[0]
            if state[0] > 0:
                continue
            if char == '}':
                state[2] -= 1
                if state[2] == 0 and (not (item < 0) and alldata[item] == '{'):
                    yield alldata[item:pos + 1]
                    item = -pos
            elif char == '{':
                if item < 0:
                    item = pos
                state[2] += 1
            elif char == '[':
                state[3] += 1
                if state[3] > 1 and item < 0:
                    item = pos
            elif char == ']':
                state[3] -= 1
                if state[3] == 1 and (not (item < 0) and alldata[item] == '['):
                    yield json.loads(alldata[item:pos + 1])
                    item = -pos
    if item == -1 and item < pos:
        yield alldata[0:pos + 1]
**/
