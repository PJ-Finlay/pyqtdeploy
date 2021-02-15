// This is the SIP interface definition for the QSharedPointer based mapped
// types specific to PyQt3D.
//
// Copyright (c) 2020 Riverbank Computing Limited <info@riverbankcomputing.com>
// 
// This file is part of PyQt3D.
// 
// This file may be used under the terms of the GNU General Public License
// version 3.0 as published by the Free Software Foundation and appearing in
// the file LICENSE included in the packaging of this file.  Please review the
// following information to ensure the GNU General Public License version 3.0
// requirements will be met: http://www.gnu.org/copyleft/gpl.html.
// 
// If you do not wish to use this file under the terms of the GPL version 3.0
// then you may purchase a commercial license.  For more information contact
// info@riverbankcomputing.com.
// 
// This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
// WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.


template<_TYPE_>
%MappedType QSharedPointer<_TYPE_> /TypeHint="_TYPE_", TypeHintValue="None"/
{
%TypeHeaderCode
#include <qsharedpointer.h>
%End

%ConvertFromTypeCode
    PyObject *py = sipConvertFromType(sipCpp->data(), sipType__TYPE_,
            sipTransferObj);

    if (!py)
        return 0;

    // We need our own copy of the shared pointer so we can copy it when asked
    // to convert the Python object back to C++.
    QSharedPointer<_TYPE_> *qsp = new QSharedPointer<_TYPE_>(*sipCpp);

    if (!qt3d_SaveQsp<_TYPE_>(py, qsp))
    {
        Py_DECREF(py);
        delete qsp;
        return 0;
    }

    return py;
%End

%ConvertToTypeCode
    if (!sipIsErr)
        return sipCanConvertToType(sipPy, sipType__TYPE_,
                SIP_NOT_NONE | SIP_NO_CONVERTORS);

    // If there is a user object then just copy the shared pointer it wraps.
    PyObject *user = sipGetUserObject((sipSimpleWrapper *)sipPy);

    QSharedPointer<_TYPE_> *qsp;

    if (user)
    {
#if defined(SIP_USE_PYCAPSULE)
        qsp = reinterpret_cast<QSharedPointer<_TYPE_> *>(
                PyCapsule_GetPointer(user, 0));
#else
        qsp = reinterpret_cast<QSharedPointer<_TYPE_> *>(
                PyCObject_AsVoidPtr(user));
#endif

        qsp = new QSharedPointer<_TYPE_>(*qsp);
    }
    else
    {
        // Create a new shared pointer and save it in the user object.
        _TYPE_ *cpp = reinterpret_cast<_TYPE_ *>(
                sipConvertToType(sipPy, sipType__TYPE_, sipTransferObj,
                        SIP_NOT_NONE | SIP_NO_CONVERTORS, 0, sipIsErr));

        if (*sipIsErr)
            return 0;

        qsp = new QSharedPointer<_TYPE_>(cpp);

        if (!qt3d_SaveQsp<_TYPE_>(sipPy, qsp))
        {
            delete qsp;
            *sipIsErr = 1;
            return 0;
        }
    }

    *sipCppPtr = qsp;

    return sipGetState(sipTransferObj);
%End
};


%ExportedHeaderCode

#include <qsharedpointer.h>


// The dtor for the saved QSharedPointer.
#if defined(SIP_USE_PYCAPSULE)
template<class T>
void qt3d_QspDtor(PyObject *capsule)
{
    delete reinterpret_cast<QSharedPointer<T> *>(
            PyCapsule_GetPointer(capsule, 0));
}
#else
template<class T>
void qt3d_QspDtor(void *shared)
{
    delete reinterpret_cast<QSharedPointer<T> *>(array);
}
#endif


template<class T>
bool qt3d_SaveQsp(PyObject *py, QSharedPointer<T> *qsp)
{
    // Wrap the copy in a Python object.
#if defined(SIP_USE_PYCAPSULE)
    PyObject *qsp_obj = PyCapsule_New(qsp, 0, qt3d_QspDtor<T>);
#else
    PyObject *qsp_obj = PyCObject_FromVoidPtr(qsp, qt3d_QspDto<T>r);
#endif

    if (!qsp_obj)
        return false;

    sipSetUserObject((sipSimpleWrapper *)py, qsp_obj);

    return true;
}

%End
