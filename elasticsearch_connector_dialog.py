#coding:utf-8

"""
ElasticSearchConnector
Ce plugin QGIS 2.x permet d'afficher les géométries stockées dans une base ElasticSearch.

begin     : 2015-03-24
copyright : (C) 2015 by Adrien VAN HAMME
email     : adrien.van.hamme@gmail.com
"""

"""/********************************************************************
* This program is free software; you can redistribute it and/or modify *
* it under the terms of the GNU General Public License as published by *
* the Free Software Foundation; either version 2 of the License, or    *
* (at your option) any later version.                                  *
********************************************************************/"""

import os

from PyQt4 import QtGui, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'elasticsearch_connector_dialog_base.ui'))


class ElasticSearchConnectorDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ElasticSearchConnectorDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
