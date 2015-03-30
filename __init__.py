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

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
	#
	from .elasticsearch_connector import ElasticSearchConnector
	return ElasticSearchConnector(iface)
