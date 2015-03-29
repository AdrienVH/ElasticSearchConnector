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

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QObject, SIGNAL
from PyQt4.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem
from elasticsearch_connector_dialog import ElasticSearchConnectorDialog
import resources_rc
import os.path

from qgis.core import QgsProject, QgsMapLayerRegistry, QgsVectorLayer, QgsFeature, QgsGeometry
from qgis.gui import QgsMessageBar
from connector import *
import ogr

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
		QObject.connect(self.dlg.connect, SIGNAL("clicked()"), self.onConnectClick)
		QObject.connect(self.dlg.addLayers, SIGNAL("clicked()"), self.onAddLayersClick)
		QObject.connect(self.dlg.closeDlg, SIGNAL("clicked()"), self.oncloseDlgClick)

	def onConnectClick(self):
		# On remplit le champ Serveur s'il était vide
		if self.dlg.url.text() == "":
			self.dlg.url.setText("localhost")
		# On prépare la liste
		listView = self.dlg.layerList
		model = QStandardItemModel(listView)
		try:
			# On ouvre une connexion à la base
			self.connector = EsConnector(self.dlg.url.text(), self.dlg.port.text())
			# On parcourt les index
			aliases = self.connector.makeGetCallToES("_aliases")
			for index in aliases:
				# On parcourt les types
				metadata = self.connector.makeGetCallToES(index)
				mappings = metadata[index]["mappings"]
				for type in mappings:
					# On parcourt les champs
					mapping = mappings[type]["properties"]
					for field in mapping:
						# Si le champ est de type geo_shape ou geo_point
						if mapping[field]["type"] == "geo_point" or mapping[field]["type"] == "geo_shape":
							# On mémorise ce champ
							self.connector.addGeoField({"index": index, "type": type, "field": field, "geotype": mapping[field]["type"]})
							# On affiche ce champ dans la liste
							item = QStandardItem('- Index "' + index + '" / Type "' + type + '" / Champ "' + field + '" (' + mapping[field]["type"] + ')')
							model.appendRow(item)
			# Si au moins un champ a été trouvé
			if model.rowCount() > 0:
				# On met à jour le contenu de la liste
				listView.setModel(model)
				# On active le bouton "Ajouter"
				self.dlg.addLayers.setEnabled(True)
			else:
				self.iface.messageBar().pushMessage("ElasticSearch Connector", 'Aucun champ "geo_shape" ou "geo_point" disponible' , level=QgsMessageBar.WARNING, duration=5)
			# On se déconnecte de la base
		except ESConnectorException, e:
			self.iface.messageBar().pushMessage("ElasticSearch Connector", str(e), level=QgsMessageBar.CRITICAL, duration=5)

	def onAddLayersClick(self):
		try:
			# On parcourt les champs géographiques recensés
			for geoField in self.connector.getGeoFields():
				index = geoField["index"]
				type = geoField["type"]
				field = geoField["field"]
				geotype = geoField["geotype"]
				# On préparer les tableaux
				features = {"MultiPoint": [], "MultiLineString": [], "MultiPolygon": []}
				# On parcourt les résultats
				hits = self.connector.getHits(index, type)
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
						name = "[@ " + self.connector.getUrl() + "] /" + index + "/" + type + "/" + field
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
			self.connector.clearGeoFields()
			self.iface.messageBar().pushMessage("ElasticSearch Connector", u"Les couches ont été ajoutées", level=QgsMessageBar.INFO, duration=5)
			# On ferme la popup
			self.oncloseDlgClick()
		except ESConnectorException, e:
			self.iface.messageBar().pushMessage("ElasticSearch Connector", str(e), level=QgsMessageBar.CRITICAL, duration=5)

	def oncloseDlgClick(self):
		self.connector.close()
		self.dlg.close()