# pyfc4


# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


import requests


class Request(object):

	'''
	Class for issuing HTTP requests to FC4 repository
	'''

	def __init__(self, repo, headers=None):

		self.repo = repo


	def _parse_resource_type(self, response):
		
		# split header values for 'Link', splitting on comma and space
		links = [link.split("ldp#")[1].split(">;")[0] for link in response.headers['Link'].split(', ') if "ldp#" in link]
		logger.debug(links)
		
		# with LDP types in hand, select appropriate pyfc4 class
		'''
		A bit of a decision here, need to confirm
			- that most specific class is selected
			- can FC4 have multiple, specific classes?
		'''
		if 'NonRDFSource' in links:
			logger.debug('NonRDFSource detected')
		if 'BasicContainer' in links:
			logger.debug('BasicContainer detected')


	def get(self, uri):

		logger.debug("GET %s" % uri)
		response = requests.get("%s%s" % (self.repo.root, uri))
		logger.debug(response.headers)

		# parse LDP resource type from headers
		resource_type = self._parse_resource_type(response)

		# return appropriate pyfc4 resource type
		return response



class Repository(object):
	
	'''
	Class for Fedora Commons 4, LDP server instance
	'''

	# establish namespace context
	context = {
		'premis':'http://www.loc.gov/premis/rdf/v1#',
		'test':'info:fedora/test/',
		'rdfs':'http://www.w3.org/2000/01/rdf-schema#',
		'dbpedia':'http://dbpedia.org/ontology/',
		'xsi':'http://www.w3.org/2001/XMLSchema-instance',
		'xmlns':'http://www.w3.org/2000/xmlns/',
		'rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
		'fedora':'http://fedora.info/definitions/v4/repository#',
		'xml':'http://www.w3.org/XML/1998/namespace',
		'ebucore':'http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#',
		'ldp':'http://www.w3.org/ns/ldp#',
		'xs':'http://www.w3.org/2001/XMLSchema',
		'fedoraconfig':'http://fedora.info/definitions/v4/config#',
		'foaf':'http://xmlns.com/foaf/0.1/',
		'dc':'http://purl.org/dc/elements/1.1/'
	}


	def __init__(self, root, username, password, context=None):

		self.root = root
		# ensure trailing slash
		if not self.root.endswith('/'):
			self.root += '/'
		self.username = username
		self.password = password

		# if context provided, merge with defaults
		if context:
			logger.debug('context provided, merging with defaults')
			self.context.update(context)


	def get_resource(self, uri):

		'''
		return appropriate Resource-type instance by reading headers
		'''
		return Request(self).get(uri)


# Resource
class Resource(object):

	'''
	Linked Data Platform Resource (LDPR)
	A HTTP resource whose state is represented in any way that conforms to the simple lifecycle patterns and conventions in section 4. Linked Data Platform Resources.
	https://www.w3.org/TR/ldp/
	'''
	pass


# RDF Source
class RDFResource(Resource):

	'''
	Linked Data Platform RDF Source (LDP-RS)
	An LDPR whose state is fully represented in RDF, corresponding to an RDF graph. See also the term RDF Source from [rdf11-concepts].
	https://www.w3.org/TR/ldp/
	'''
	pass


# Container
class Container(RDFResource):
	
	'''
	Linked Data Platform Container (LDPC)
	A LDP-RS representing a collection of linked documents (RDF Document [rdf11-concepts] or information resources [WEBARCH]) that responds to client requests for creation, modification, and/or enumeration of its linked members and documents, and that conforms to the simple lifecycle patterns and conventions in section 5. Linked Data Platform Containers.
	https://www.w3.org/TR/ldp/
	'''
	pass


# Basic Container
class BasicContainer(Container):
	
	'''
	Linked Data Platform Basic Container (LDP-BC)
	An LDPC that defines a simple link to its contained documents (information resources) [WEBARCH].
	https://www.w3.org/TR/ldp/

	https://gist.github.com/hectorcorrea/dc20d743583488168703
		- "The important thing to notice is that by posting to a Basic Container, the LDP server automatically adds a triple with ldp:contains predicate pointing to the new resource created."
	'''
	pass


# Direct Container
class DirectContainer(Container):
	
	'''
	Linked Data Platform Direct Container (LDP-DC)
	An LDPC that adds the concept of membership, allowing the flexibility of choosing what form its membership triples take, and allows members to be any resources [WEBARCH], not only documents.
	https://www.w3.org/TR/ldp/

	When adding children, can also write relationships to another resource

	'''
	pass


# Indirect Container
class IndirectContainer(Container):
	
	'''
	Linked Data Platform Indirect Container (LDP-IC)
	An LDPC similar to a LDP-DC that is also capable of having members whose URIs are based on the content of its contained documents rather than the URIs assigned to those documents.
	https://www.w3.org/TR/ldp/
	'''
	pass


# NonRDF Source
class NonRDFSource(Resource):

	'''
	Linked Data Platform Non-RDF Source (LDP-NR)
	An LDPR whose state is not represented in RDF. For example, these can be binary or text documents that do not have useful RDF representations.
	https://www.w3.org/TR/ldp/
	'''
	pass