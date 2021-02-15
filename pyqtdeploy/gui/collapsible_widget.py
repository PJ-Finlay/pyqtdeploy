# Copyright (c) 2020, Riverbank Computing Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QToolButton, QVBoxLayout, QWidget


class CollapsibleWidget(QWidget):
    """ A widget that can be expanded or collapsed (ie. made visible or hidden)
    by the user clicking on a button.
    """

    def __init__(self, title, collapsed=True, parent=None):
        """  Initialise the widget. """

        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        toggle = QToolButton(clicked=self._on_toggle_clicked)
        toggle.setStyleSheet("border: none;")
        toggle.setFont(QGuiApplication.font())
        toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toggle.setArrowType(Qt.RightArrow if collapsed else Qt.DownArrow)
        toggle.setText(title)
        toggle.setCheckable(True)
        toggle.setChecked(False)

        layout.addWidget(toggle)
        self.setLayout(layout)

        self._toggle = toggle
        self._content = None

    def _on_toggle_clicked(self, checked):
        """ Invoked when the user clicks to expand or collapse the widget. """

        if checked:
            self._toggle.setArrowType(Qt.DownArrow)
            self._content.show()
        else:
            self._toggle.setArrowType(Qt.RightArrow)
            self._content.hide()

    def setWidget(self, content):
        """ Set the widget to be expanded or collapsed. """

        layout = self.layout()

        if self._content is not None:
            layout.removeWidget(self._content)

        if content is not None:
            content.setVisible(self._toggle.arrowType() == Qt.DownArrow)
            layout.addWidget(content)

        self._content = content
