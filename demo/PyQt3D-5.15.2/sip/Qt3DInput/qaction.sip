// qaction.sip generated by MetaSIP
//
// This file is part of the Qt3DInput Python extension module.
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


namespace Qt3DInput
{
%TypeHeaderCode
#include <qaction.h>
%End

    class QAction : Qt3DCore::QNode
    {
%TypeHeaderCode
#include <qaction.h>
%End

    public:
        explicit QAction(Qt3DCore::QNode *parent /TransferThis/ = 0);
        virtual ~QAction();
        bool isActive() const;
        void addInput(Qt3DInput::QAbstractActionInput *input /GetWrapper/);
%MethodCode
            // This takes ownership only if it doesn't already have a parent.
            if (!a0->parent())
                sipTransferTo(a0Wrapper, sipSelf);
            
            sipCpp->addInput(a0);
%End

        void removeInput(Qt3DInput::QAbstractActionInput *input);
        QVector<Qt3DInput::QAbstractActionInput *> inputs() const;

    signals:
        void activeChanged(bool isActive);

    protected:
        virtual void sceneChangeEvent(const Qt3DCore::QSceneChangePtr &change);
    };
};
