# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ElasticSearchConnector
                                 A QGIS plugin
 Permet de se connecter à une base ElasticSearch
                             -------------------
        begin                : 2015-03-24
        copyright            : (C) 2015 by Adrien VAN HAMME
        email                : adrien.van.hamme@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ElasticSearchConnector class from file ElasticSearchConnector.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .elasticsearch_connector import ElasticSearchConnector
    return ElasticSearchConnector(iface)
