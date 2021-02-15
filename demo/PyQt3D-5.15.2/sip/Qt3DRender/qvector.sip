// This is the SIP interface definition for the QVector based mapped types
// specific to Qt3DRender.
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


// Note that when we test the type of an object to see if it can be converted
// to a collection we only check if it is iterable.  We do not check the
// types of the contents - we assume we will be able to convert them when
// requested.  This allows us to raise exceptions specific to an individual
// object.  This approach doesn't work if there are overloads that can only be
// distinguished by the types of the template arguments.  Currently there are
// no such cases in PyQt5.  Note also that we don't consider strings to be
// iterables.


// We can't use the template because QTextureImageDataPtr is a typedef and the
// wrong generated type structure's name would be generated.
%MappedType QVector<Qt3DRender::QTextureImageDataPtr>
        /TypeHintIn="Iterable[QTextureImageData]",
        TypeHintOut="List[QTextureImageData]", TypeHintValue="[]"/
{
%TypeHeaderCode
#include <QTextureImageData>
%End

%ConvertFromTypeCode
    static const sipTypeDef *td = 0;

    if (!td)
        td = sipFindType("QSharedPointer<Qt3DRender::QTextureImageData>");

    PyObject *l = PyList_New(sipCpp->size());

    if (!l)
        return 0;

    for (int i = 0; i < sipCpp->size(); ++i)
    {
        Qt3DRender::QTextureImageDataPtr t = sipCpp->at(i);

        PyObject *tobj = sipConvertFromType(&t, td, sipTransferObj);

        if (!tobj)
        {
            Py_DECREF(l);

            return 0;
        }

        PyList_SetItem(l, i, tobj);
    }

    return l;
%End

%ConvertToTypeCode
    PyObject *iter = PyObject_GetIter(sipPy);

    if (!sipIsErr)
    {
        Py_XDECREF(iter);

        return (iter
#if PY_MAJOR_VERSION < 3
                && !PyString_Check(sipPy)
#endif
                && !PyUnicode_Check(sipPy));
    }

    static const sipTypeDef *td = 0;

    if (!td)
        td = sipFindType("QSharedPointer<Qt3DRender::QTextureImageData>");

    if (!iter)
    {
        *sipIsErr = 1;

        return 0;
    }

    QVector<Qt3DRender::QTextureImageDataPtr> *qv = new QVector<Qt3DRender::QTextureImageDataPtr>;
 
    for (Py_ssize_t i = 0; ; ++i)
    {
        PyErr_Clear();
        PyObject *itm = PyIter_Next(iter);

        if (!itm)
        {
            if (PyErr_Occurred())
            {
                delete qv;
                Py_DECREF(iter);
                *sipIsErr = 1;

                return 0;
            }

            break;
        }

        Qt3DRender::QTextureImageDataPtr *t = reinterpret_cast<Qt3DRender::QTextureImageDataPtr *>(
                sipForceConvertToType(itm, td, sipTransferObj, 0, 0,
                        sipIsErr));
 
        if (*sipIsErr)
        {
            PyErr_Format(PyExc_TypeError,
                    "index %zd has type '%s' but 'QTextureImageData' is expected",
                    i, sipPyTypeName(Py_TYPE(itm)));

            Py_DECREF(itm);
            delete qv;
            Py_DECREF(iter);

            return 0;
        }

        qv->append(*t);

        Py_DECREF(itm);
    }

    Py_DECREF(iter);
 
    *sipCppPtr = qv;
 
    return sipGetState(sipTransferObj);
%End
};


%MappedType QVector<Qt3DRender::QRenderTargetOutput::AttachmentPoint>
        /TypeHintIn="Iterable[QRenderTargetOutput.AttachmentPoint]",
        TypeHintOut="List[QRenderTargetOutput.AttachmentPoint]",
        TypeHintValue="[]"/
{
%TypeHeaderCode
#include <QRenderTargetOutput>
%End

%ConvertFromTypeCode
    PyObject *l = PyList_New(sipCpp->size());

    if (!l)
        return 0;

    for (int i = 0; i < sipCpp->size(); ++i)
    {
        PyObject *eobj = sipConvertFromEnum(sipCpp->at(i),
                sipType_Qt3DRender_QRenderTargetOutput_AttachmentPoint);

        if (!eobj)
        {
            Py_DECREF(l);

            return 0;
        }

        PyList_SetItem(l, i, eobj);
    }

    return l;
%End

%ConvertToTypeCode
    PyObject *iter = PyObject_GetIter(sipPy);

    if (!sipIsErr)
    {
        Py_XDECREF(iter);

        return (iter
#if PY_MAJOR_VERSION < 3
                && !PyString_Check(sipPy)
#endif
                && !PyUnicode_Check(sipPy));
    }

    if (!iter)
    {
        *sipIsErr = 1;

        return 0;
    }

    QVector<Qt3DRender::QRenderTargetOutput::AttachmentPoint> *ql = new QVector<Qt3DRender::QRenderTargetOutput::AttachmentPoint>;

    for (Py_ssize_t i = 0; ; ++i)
    {
        PyErr_Clear();
        PyObject *itm = PyIter_Next(iter);

        if (!itm)
        {
            if (PyErr_Occurred())
            {
                delete ql;
                Py_DECREF(iter);
                *sipIsErr = 1;

                return 0;
            }

            break;
        }

        int v = sipConvertToEnum(itm, sipType_Qt3DRender_QRenderTargetOutput_AttachmentPoint);

        if (PyErr_Occurred())
        {
            PyErr_Format(PyExc_TypeError,
                    "index %zd has type '%s' but 'QRenderTargetOutput.AttachmentPoint' is expected",
                    i, sipPyTypeName(Py_TYPE(itm)));

            Py_DECREF(itm);
            delete ql;
            Py_DECREF(iter);
            *sipIsErr = 1;

            return 0;
        }

        ql->append(
                static_cast<Qt3DRender::QRenderTargetOutput::AttachmentPoint>(
                        v));

        Py_DECREF(itm);
    }

    Py_DECREF(iter);

    *sipCppPtr = ql;

    return sipGetState(sipTransferObj);
%End
};


%MappedType QVector<Qt3DRender::QSortPolicy::SortType>
        /TypeHintIn="Iterable[QSortPolicy.SortType]",
        TypeHintOut="List[QSortPolicy.SortType]", TypeHintValue="[]"/
{
%TypeHeaderCode
#include <QSortPolicy>
%End

%ConvertFromTypeCode
    PyObject *l = PyList_New(sipCpp->size());

    if (!l)
        return 0;

    for (int i = 0; i < sipCpp->size(); ++i)
    {
        PyObject *eobj = sipConvertFromEnum(sipCpp->at(i),
                sipType_Qt3DRender_QSortPolicy_SortType);

        if (!eobj)
        {
            Py_DECREF(l);

            return 0;
        }

        PyList_SetItem(l, i, eobj);
    }

    return l;
%End

%ConvertToTypeCode
    PyObject *iter = PyObject_GetIter(sipPy);

    if (!sipIsErr)
    {
        Py_XDECREF(iter);

        return (iter
#if PY_MAJOR_VERSION < 3
                && !PyString_Check(sipPy)
#endif
                && !PyUnicode_Check(sipPy));
    }

    if (!iter)
    {
        *sipIsErr = 1;

        return 0;
    }

    QVector<Qt3DRender::QSortPolicy::SortType> *ql = new QVector<Qt3DRender::QSortPolicy::SortType>;

    for (Py_ssize_t i = 0; ; ++i)
    {
        PyErr_Clear();
        PyObject *itm = PyIter_Next(iter);

        if (!itm)
        {
            if (PyErr_Occurred())
            {
                delete ql;
                Py_DECREF(iter);
                *sipIsErr = 1;

                return 0;
            }

            break;
        }

        int v = sipConvertToEnum(itm, sipType_Qt3DRender_QSortPolicy_SortType);

        if (PyErr_Occurred())
        {
            PyErr_Format(PyExc_TypeError,
                    "index %zd has type '%s' but 'QSortPolicy.SortType' is expected",
                    i, sipPyTypeName(Py_TYPE(itm)));

            Py_DECREF(itm);
            delete ql;
            Py_DECREF(iter);
            *sipIsErr = 1;

            return 0;
        }

        ql->append(static_cast<Qt3DRender::QSortPolicy::SortType>(v));

        Py_DECREF(itm);
    }

    Py_DECREF(iter);

    *sipCppPtr = ql;

    return sipGetState(sipTransferObj);
%End
};
