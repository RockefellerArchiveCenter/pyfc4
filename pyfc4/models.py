# pyfc4

# rdf
from rdflib import Graph, plugin
# from SPARQLWrapper import SPARQLWrapper
import json, rdflib_jsonld


import requests

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



# Repository
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


	def __init__(self, 
			root,
			username,
			password,
			context=None,
			default_response_format='application/ld+json'
		):

		self.root = root
		# ensure trailing slash
		if not self.root.endswith('/'):
			self.root += '/'
		self.username = username
		self.password = password
		self.default_response_format = default_response_format

		# API facade
		self.api = API(self)

		# if context provided, merge with defaults
		if context:
			logger.debug('context provided, merging with defaults')
			self.context.update(context)


	def get_resource(self, uri, response_format=None):

		'''
		return appropriate Resource-type instance
			- issue HEAD request, sniff out content-type to detect NonRDF
			- issue GET request 
		'''

		# HEAD request to detect resource type
		head_response = self.api.http_request('HEAD', uri)

		# item does not exist, return False
		if head_response.status_code == 404:
			return False

		# assume exists, parse headers for resource type and return instance
		else:

			# parse LDP resource type from headers
			resource_type = self.api.parse_resource_type(head_response)
			logger.debug('using resource type: %s' % resource_type)

			# RDFSource
			if resource_type != NonRDFSource:
				# retrieve RDFSource resource
				get_response = self.api.http_request('GET', uri, response_format=response_format)
			# NonRDFSource, retrieve with proper content negotiation
			else:
				get_response = self.api.http_request('GET', uri, response_format=head_response.headers['Content-Type'])

			return resource_type(self, uri, data=get_response.content, headers=get_response.headers, status_code=get_response.status_code)



# API
class API(object):

	'''
	API for making requests and parsing responses from FC4 endpoint
	'''

	def __init__(self, repo):

		# repository instance
		self.repo = repo


	def http_request(self, 
			verb,
			uri,
			data=None,
			headers=None,
			response_format=None
		):

		# set content negotiated response format
		'''
		Acceptable content negotiated response formats include:
			application/ld+json
			application/n-triples
			application/rdf+xml
			text/n3 (or text/rdf+n3)
			text/plain
			text/turtle (or application/x-turtle)
		'''
		# if no response_format has been requested to this point, use repository instance default
		if not response_format:
			response_format = self.repo.default_response_format

		# if not HEAD request
		if verb != 'HEAD':
			# if headers present, append
			if headers and 'Accept' not in headers.keys():
				headers['Accept'] = response_format
			else:
				headers = {'Accept':response_format}

		logger.debug("%s request for %s, format %s" % (verb, uri, response_format))

		# manually prepare request
		session = requests.Session()
		request = requests.Request(verb, "%s%s" % (self.repo.root, uri), data=data, headers=headers)
		prepped_request = session.prepare_request(request)
		response = session.send(prepped_request,
			stream=False,
		)
		return response


	def parse_resource_type(self, response):
		
		# parse 'Link' header
		links = [link.split(";")[0] for link in response.headers['Link'].split(', ') if link.startswith('<http://www.w3.org/ns/ldp#')]
		logger.debug('parsed Link headers: %s' % links)
		
		# with LDP types in hand, select appropriate resource type
		# NonRDF Source
		if '<http://www.w3.org/ns/ldp#NonRDFSource>' in links:
			return NonRDFSource
		# Basic Container
		elif '<http://www.w3.org/ns/ldp#BasicContainer>' in links:
			return BasicContainer
		# Direct Container
		elif '<http://www.w3.org/ns/ldp#DirectContainer>' in links:
			return DirectContainer
		# Indirect Container
		elif '<http://www.w3.org/ns/ldp#IndirectContainer>' in links:
			return IndirectContainer
		else:
			logger.debug('could not determine resource type from Link header, returning False')
			return False



# Resource
class Resource(object):

	'''
	Linked Data Platform Resource (LDPR)
	A HTTP resource whose state is represented in any way that conforms to the simple lifecycle patterns and conventions in section 4. Linked Data Platform Resources.
	https://www.w3.org/TR/ldp/
	'''
	
	def __init__(self, repo, data=None, headers={}, status_code=None):

		# resources are combination of data and headers
		self.data = data
		self.headers = headers
		self.status_code = status_code

		# repository handle is pinned to resource instance here
		self.repo = repo


	def exists(self):
		
		'''
		Check if resource exists, returns bool
		'''

		response = self.repo.api.http_request('HEAD', self.uri)
		if response.status_code == 200:
			return True
		if response.status_code == 404:
			return False


	def create(self):

		'''
		when object is created, self.data and self.headers are passed with the requests
			- when creating NonRDFSource (Binary) type resources, this resource must include 
			content for self.data and a header value for self.headers['Content-Type']
		'''

		# if resource does not, create
		if not self.exists():
			self.repo.api.http_request('PUT', self.uri, self.data, self.headers)
		else:
			logger.debug('resource %s exists, aborting create' % self.uri)


	def delete(self, remove_tombstone=True):

		'''
		account for tombstone
		'''

		self.repo.api.http_request('DELETE', self.uri)

		if remove_tombstone:
			self.repo.api.http_request('DELETE', '%s/fcr:tombstone' % self.uri)



# NonRDF Source
class NonRDFSource(Resource):

	'''
	Linked Data Platform Non-RDF Source (LDP-NR)
	An LDPR whose state is not represented in RDF. For example, these can be binary or text documents that do not have useful RDF representations.
	https://www.w3.org/TR/ldp/
	'''
	
	def __init__(self, repo, uri, data=None, headers={}, status_code=None):

		self.uri = uri
		
		# fire parent Container init()
		super().__init__(repo, data=data, headers=headers, status_code=status_code)


# 'Binary' alias for NonRDFSource
Binary = NonRDFSource


# RDF Source
class RDFResource(Resource):

	'''
	Linked Data Platform RDF Source (LDP-RS)
	An LDPR whose state is fully represented in RDF, corresponding to an RDF graph. See also the term RDF Source from [rdf11-concepts].
	https://www.w3.org/TR/ldp/
	'''
	
	def __init__(self, repo, data=None, headers={}, status_code=None):
		
		# fire parent Resource init()
		super().__init__(repo, data=data, headers=headers, status_code=status_code)

		# parse RDF
		self.graph = self.parse_graph()


	def parse_graph(self):

		'''
		use Content-Type from headers to determine parsing method
		'''

		# handle edge case for content-types not recognized by rdflib parser
		if self.headers['Content-Type'].startswith('text/plain'):
			logger.debug('text/plain Content-Type detected, using application/n-triples for parser')
			parse_format = 'application/n-triples'
		else:
			parse_format = self.headers['Content-Type']

		# clean parse format for rdf parser
		# https://www.w3.org/2008/01/rdf-media-types
		if ';charset' in parse_format:
			parse_format = parse_format.split(';')[0]
		
		# parse and return graph	
		return Graph().parse(data=self.data.decode('utf-8'), format=parse_format)



# Container
class Container(RDFResource):
	
	'''
	Linked Data Platform Container (LDPC)
	A LDP-RS representing a collection of linked documents (RDF Document [rdf11-concepts] or information resources [WEBARCH]) that responds to client requests for creation, modification, and/or enumeration of its linked members and documents, and that conforms to the simple lifecycle patterns and conventions in section 5. Linked Data Platform Containers.
	https://www.w3.org/TR/ldp/
	'''

	def __init__(self, repo, data=None, headers={}, status_code=None):
		
		# fire parent RDFResource init()
		super().__init__(repo, data=data, headers=headers, status_code=status_code)


	def children(self):

		'''
		method to return children of this resource
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
	
	def __init__(self, repo, uri, data=None, headers={}, status_code=None):

		self.uri = uri
		self.data = data
		self.headers = headers
		self.status_code = status_code
		
		# fire parent Container init()
		super().__init__(repo, data=data, headers=headers, status_code=status_code)



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


