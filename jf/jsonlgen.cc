#include <Python.h> 
#include <string>
#include <iostream>
#include <sstream>
#include <queue>
#include <vector>

#define DEBUG (0)

using namespace std;

typedef struct {
    PyObject_HEAD
    PyObject *iter;
    queue<string> items;
    vector<char> data;
    bool quote = 0;
    bool escape = 0;
    uint8_t obj = 0;
    uint8_t list = 0;
    int item = -1;
    int pos = -1;
} JSONLgenState;

static void
jsonlgen_dealloc(JSONLgenState *jfstate)
{
    Py_XDECREF(jfstate->iter);
    Py_TYPE(jfstate)->tp_free(jfstate);
}


void parsejsonl(string &str, JSONLgenState *s){
    for(char& c : str){
        s->pos++;
        s->data.push_back(c);
        if(DEBUG) cerr << c << " " << s->quote << s->escape << (int) s->obj << (int) s->list << " " << s->pos << " " << s->data.size() << endl;
        if (s->escape > 0){
            s->escape = 0;
        }
        else if(c == '\\'){
            s->escape = 1;
        }
        else if(c == '"'){
            if(s->list < 2){
                if(s->item < 0){
                    s->item = s->pos;
                } else if (s->obj == 0){
                    if(DEBUG) cerr << "yielding 1" << endl;
                    s->items.push(string(s->data.begin() + s->item, s->data.begin() + s->pos + 1));
                    s->data.erase(s->data.begin(), s->data.begin() + s->pos + 1);
                    s->pos = -1;
                    s->item = -1;
                }
            }
            s->quote = 1 - s->quote;
        }
        else if (s->quote > 0) ;
        else if (c == '}'){
            s->obj--;
            if (s->obj == 0 and (not (s->item < 0) and s->data[s->item] == '{')){
                if(DEBUG) cerr << "yielding 2" << endl;
                s->items.push(string(s->data.begin() + s->item, s->data.begin() + s->pos + 1));
                s->data.erase(s->data.begin(), s->data.begin() + s->pos + 1);
                s->pos = -1;
                s->item = -1;
            }
        }
        else if (c == '{'){
            s->obj++;
            if(s->item < 0) { s->item = s->pos; }
        }
        else if (c == '['){
            s->list++;
            if(s->list > 1 and s->item < 0) { s->item = s->pos; }
        }
        else if (c == ']') {
            s->list--;
            if (s->list == 1 and (not (s->item < 0) and s->data[s->item] == '[')){
                if(DEBUG) cerr << "yielding 3" << endl;
                s->items.push(string(s->data.begin() + s->item, s->data.begin() + s->pos + 1));
                s->data.erase(s->data.begin(), s->data.begin() + s->pos + 1);
                s->pos = -1;
                s->item = -1;
            }
        }
    }
}


static PyObject *
jsonlgen_next(JSONLgenState *jfstate)
{
    /* seq_length < 0 means that the generator is exhausted.
     * Returning NULL in this case is enough. The next() builtin will raise the
     * StopIteration error for us->
    */
    if ( !jfstate->items.empty() ) {
        string item = jfstate->items.front();
        if(DEBUG) cerr << "Items has " << jfstate->items.size() << " items. Yielding " << item << endl;
        PyObject *result = Py_BuildValue("s", item.c_str());
        jfstate->items.pop();
        return result;
    }
    PyObject *iterator = PyObject_GetIter(jfstate->iter);

    PyObject *elem;
    while((elem = PyIter_Next(iterator))) {
        /* Exceptions from PySequence_GetItem are propagated to the caller
         * (elem will be NULL so we also return NULL).
        */
        if (elem) {
            string str(PyUnicode_AsUTF8(elem));
            parsejsonl(str, jfstate);
            if ( !jfstate->items.empty() ) {
                string item = jfstate->items.front();
                if(DEBUG) cerr << "Items has " << jfstate->items.size() << " items. Yielding " << item << endl;
                PyObject *result = Py_BuildValue("s", item.c_str());
                jfstate->items.pop();
                return result;
            }
        }
        Py_DECREF(elem);
    }

    /* The reference to the sequence is cleared in the first generator call
     * after its exhaustion (after the call that returned the last element).
     * Py_CLEAR will be harmless for subsequent calls since it's idempotent
     * on NULL.
    */
    Py_DECREF(iterator);
    return NULL;
}

static PyObject *
jsonlgen_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    PyObject *iter;

    if (!PyArg_UnpackTuple(args, "gen", 1, 1, &iter))
        return NULL;

    /* We expect an argument that supports the sequence protocol */
    if (!PyIter_Check(iter)) {
        PyErr_SetString(PyExc_TypeError, "jsonlgen.gen() expects a iterable");
        return NULL;
    }

    /* Create a new JSONLgenState and initialize its state - pointing to the last
     * index in the sequence.
    */
    JSONLgenState *jfstate = (JSONLgenState *)type->tp_alloc(type, 0);
    if (!jfstate)
        return NULL;

    Py_INCREF(iter);
    jfstate->iter = iter;
    jfstate->item = -1 ;
    jfstate->pos = -1 ;
    jfstate->items = queue<string>();

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
