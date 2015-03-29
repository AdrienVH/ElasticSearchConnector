#coding:utf-8

import json
import httplib

# Custom exception
class ESConnectorException(Exception):
	pass

# Main class
class EsConnector(object):

	# Constructor
	def __init__(self, url, port):
		self.url = url
		self.port = port
		self.address = self.url + ":" + self.port
		self.geoFields = []
		try:
			self.connection = httplib.HTTPConnection(self.address)
		except Exception:
			raise ESConnectorException("Impossible de se connecter a la base")

	def close(self):
		self.connection.close()

	def getUrl(self):
		return self.url

	# Make a GET call and try to return the deserialized JSON string response
	def makeGetCallToES(self, path):
		try:
			self.connection.request("GET", "/" + path)
			response = self.connection.getresponse()
			if response.status == 200:
				try:
					return json.loads(response.read())
				except ValueError:
					return []
			else:
				raise ESConnectorException("Impossible de se connecter a la base (HTTP " + response.status + ")")
		except Exception, e:
			raise ESConnectorException("Impossible de se connecter a la base")

	def getHits(self, index, type):
		results = self.makeGetCallToES(index + "/" + type + "/_search")
		if results["hits"]["total"] > 0:
			return results["hits"]["hits"]
		else:
			return []

	def getGeoFields(self):
		return self.geoFields

	def addGeoField(self, geoField):
		self.geoFields.append(geoField)

	def clearGeoFields(self):
		self.geoFields = []