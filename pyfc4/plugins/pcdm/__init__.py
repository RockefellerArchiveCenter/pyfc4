# pyfc4 plugin: pcdm

import rdflib

from pyfc4.plugins.pcdm import models, examples


# logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def custom_resource_type_parser(repo, uri, get_response):

	logger.debug("PCDM plugin, custom resource type parser firing")

	# parse graph
	resource_graph = repo.api.parse_rdf_payload(get_response.content, get_response.headers)

	# get rdf:types, using get_response.url as the uri
	rdf_types = list(resource_graph.objects(
		uri,
		rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')))
	logger.debug('found following rdf:types: %s' % rdf_types)

	# look for pcdm:*
	if rdflib.term.URIRef('http://pcdm.org/models#Collection') in rdf_types:
		return models.PCDMCollection
	elif rdflib.term.URIRef('http://pcdm.org/models#Object') in rdf_types:
		return models.PCDMObject
	elif rdflib.term.URIRef('http://pcdm.org/models#File') in rdf_types:
		return models.PCDMFile
	else:
		logger.debug('PCDM resource type not detected')
		return False

