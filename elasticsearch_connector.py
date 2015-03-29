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

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
import resources_rc
from elasticsearch_connector_dialog import ElasticSearchConnectorDialog
import os.path

import ogr
from qgis.core import QgsProject, QgsMapLayerRegistry, QgsVectorLayer, QgsFeature, QgsGeometry
from qgis.gui import QgsMessageBar
from connector import *

class ElasticSearchConnector:

	def __init__(self, iface):
		# Save reference to the QGIS interface
		self.iface = iface
		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)
		# initialize locale
		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(self.plugin_dir, 'i18n', 'ElasticSearchConnector_{}.qm'.format(locale))
		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)
			if qVersion() > '4.3.3':
				QCoreApplication.installTranslator(self.translator)
		# Create the dialog (after translation) and keep reference
		self.dlg = ElasticSearchConnectorDialog()
		# Declare instance attributes
		self.actions = []
		self.menu = self.tr(u'&ElasticSearch Connector')
		# TODO: We are going to let the user set this up in a future iteration
		self.toolbar = self.iface.addToolBar(u'ElasticSearchConnector')
		self.toolbar.setObjectName(u'ElasticSearchConnector')

	# noinspection PyMethodMayBeStatic
	def tr(self, message):
		# noinspection PyTypeChecker,PyArgumentList,PyCallByClass
		return QCoreApplication.translate('ElasticSearchConnector', message)

	def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
		"""Add a toolbar icon to the toolbar.
		:param icon_path: Path to the icon for this action. Can be a resource
			path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
		:type icon_path: str
		:param text: Text that should be shown in menu items for this action.
		:type text: str
		:param callback: Function to be called when the action is triggered.
		:type callback: function
		:param enabled_flag: A flag indicating if the action should be enabled
			by default. Defaults to True.
		:type enabled_flag: bool
		:param add_to_menu: Flag indicating whether the action should also
			be added to the menu. Defaults to True.
		:type add_to_menu: bool
		:param add_to_toolbar: Flag indicating whether the action should also
			be added to the toolbar. Defaults to True.
		:type add_to_toolbar: bool
		:param status_tip: Optional text to show in a popup when mouse pointer
			hovers over the action.
		:type status_tip: str
		:param parent: Parent widget for the new action. Defaults None.
		:type parent: QWidget
		:param whats_this: Optional text to show in the status bar when the
			mouse pointer hovers over the action.
		:returns: The action that was created. Note that the action is also
			added to self.actions list.
		:rtype: QAction
		"""
		icon = QIcon(icon_path)
		action = QAction(icon, text, parent)
		action.triggered.connect(callback)
		action.setEnabled(enabled_flag)
		if status_tip is not None:
			action.setStatusTip(status_tip)
		if whats_this is not None:
			action.setWhatsThis(whats_this)
		if add_to_toolbar:
			self.toolbar.addAction(action)
		if add_to_menu:
			self.iface.addPluginToMenu(self.menu, action)
		self.actions.append(action)
		return action

	def initGui(self):
		icon_path = ':/plugins/ElasticSearchConnector/icon.png'
		self.add_action(icon_path, text=self.tr(u'Scanner une base ElasticSearch'), callback=self.run, parent=self.iface.mainWindow())

	def unload(self):
		for action in self.actions:
			self.iface.removePluginMenu(self.tr(u'&ElasticSearch Connector'), action)
			self.iface.removeToolBarIcon(action)
		del self.toolbar

	def run(self):
		self.dlg.show()
		result = self.dlg.exec_()
		if result:
			try:
				connector = EsConnector(self.dlg.url.text(), self.dlg.port.text())
				"""
				1. SCAN DE LA BASE ES A LA RECHERCHE DES CHAMPS DE TYPE GEO_SHAPE OU GEO_POINT
				"""
				# On parcourt les index
				aliases = connector.makeGetCallToES("_aliases")
				for index in aliases:
					# On parcourt les types
					metadata = connector.makeGetCallToES(index)
					mappings = metadata[index]["mappings"]
					for type in mappings:
						# On parcourt les champs
						mapping = mappings[type]["properties"]
						for field in mapping:
							# Si le champ est de type geo_shape ou geo_point
							if mapping[field]["type"] == "geo_point" or mapping[field]["type"] == "geo_shape":
								connector.addGeoField({"index": index, "type": type, "field": field, "geotype": mapping[field]["type"]})
				"""
				2. RECUPERATION DES DOCUMENTS POUR CHACUN DES CHAMPS TROUVES
				"""
				# On parcourt les champs géographiques recensés
				for geoField in connector.getGeoFields():
					index = geoField["index"]
					type = geoField["type"]
					field = geoField["field"]
					geotype = geoField["geotype"]
					# On préparer les tableaux
					features = {"MultiPoint": [], "MultiLineString": [], "MultiPolygon": []}
					# On parcourt les résultats
					hits = connector.getHits(index, type)
					if len(hits) > 0:
						# Si on va récupérer des geo_point
						if geotype == "geo_point":
							for hit in hits:
								try:
									# On construit une feature et on l'ajoute au tableau
									geoPoint = hit["_source"][field]
									wkt = ""
									if isinstance(geoPoint, str) or isinstance(geoPoint, unicode):
										coordinates = geoPoint.split(",")
										wkt = "POINT("+ coordinates[1] +" " + coordinates[0] + ")"
									elif isinstance(geoPoint, dict):
										wkt = "POINT("+ geoPoint["lon"] +" " + geoPoint["lat"] + ")"
									elif isinstance(geoPoint, list):
										wkt = "POINT("+ geoPoint[1] +" " + geoPoint[0] + ")"
									feature = QgsFeature()
									feature.setGeometry(QgsGeometry.fromWkt(wkt))
									features["MultiPoint"].append(feature)
								except KeyError:
									pass
						# Si on va récupérer des geo_shape
						elif geotype == "geo_shape":
							for hit in hits:
								try:
									# On construit une feature et on l'ajoute au tableau
									geom = hit["_source"][field]
									geometry = ogr.CreateGeometryFromJson(json.dumps(geom))
									wkt = geometry.ExportToWkt()
									feature = QgsFeature()
									feature.setGeometry(QgsGeometry.fromWkt(wkt))
									geomtype = geom["type"].lower()
									if "point" in geomtype:
										features["MultiPoint"].append(feature)
									if "line" in geomtype:
										features["MultiLineString"].append(feature)
									if "polygon" in geomtype:
										features["MultiPolygon"].append(feature)
								except KeyError:
									pass
						# S'il y a au moins une géométrie exploitable qui a été récupérée dans ce champ
						if len(features["MultiPoint"]) + len(features["MultiLineString"]) + len(features["MultiPolygon"]) > 0:
							# On crée un groupe de couches
							name = "[ES@" + connector.getUrl() + "] /" + index + "/" + type + "/" + field
							group = QgsProject.instance().layerTreeRoot().addGroup(name)
							# On crée les couches vectorielles et on les ajoute à la carte
							for geomtype in features:
								if len(features[geomtype]) > 0:
									# On crée la couche vectorielle
									layer = QgsVectorLayer(geomtype + "?crs=EPSG:4326", geomtype[5:] + "s", "memory")
									provider = layer.dataProvider()
									# On ajoute le tableau de features à la couche
									provider.addFeatures(features[geomtype])
									layer.updateExtents()
									# On ajoute la couche au groupe
									QgsMapLayerRegistry.instance().addMapLayer(layer, False)
									group.addLayer(layer)
				connector.close()
				self.iface.messageBar().pushMessage(u"Opération réussie", u"La base ElasticSearch a été scannée", level=QgsMessageBar.INFO, duration=5)
			except ESConnectorException, e:
				self.iface.messageBar().pushMessage(u"Une erreur est survenue", str(e), level=QgsMessageBar.CRITICAL, duration=5)