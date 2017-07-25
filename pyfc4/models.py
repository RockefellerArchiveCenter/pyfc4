# pyfc4


# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


import requests

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


	def __init__(self, root, username, password, context=None):

		self.root = root
		# ensure trailing slash
		if not self.root.endswith('/'):
			self.root += '/'
		self.username = username
		self.password = password

		# API facade
		self.api = API(self)

		# if context provided, merge with defaults
		if context:
			logger.debug('context provided, merging with defaults')
			self.context.update(context)


	def get_resource(self, uri):

		'''
		return appropriate Resource-type instance by reading headers
		'''
		response = self.api.get(uri)

		# item does not exist, return False
		if response.status_code == 404:
			return False

		# assume exists, parse headers for resource type and return instance
		else:

			# parse LDP resource type from headers
			resource_type = self.api.parse_resource_type(response)
			logger.debug('using resource type: %s' % resource_type)

			return resource_type(self, uri, response)



# API
class API(object):

	'''
	API for making requests and parsing responses from FC4 endpoint
	'''

	def __init__(self, repo):

		# repository instance
		self.repo = repo


	########################################################################
	# HTTP Verbs
	########################################################################

	# HEAD requests
	def head(self, uri, headers=None):

		logger.debug("HEAD %s" % uri)
		response = requests.head("%s%s" % (self.repo.root, uri), headers=headers)

		# return response
		return response


	# GET requests
	def get(self, uri, headers=None):

		logger.debug("GET %s" % uri)
		response = requests.get("%s%s" % (self.repo.root, uri), headers=headers)

		# return response
		return response


	# PUT requests
	def put(self, uri, data=None, headers=None):

		logger.debug("PUT %s" % uri)
		response = requests.put("%s%s" % (self.repo.root, uri), data=data, headers=headers)

		# return response
		return response


	# DELETE requests
	def delete(self, uri, data=None, headers=None):

		logger.debug("DELETE %s" % uri)
		response = requests.delete("%s%s" % (self.repo.root, uri), data=data, headers=headers)

		# return response
		return response


	########################################################################
	# helper methods
	########################################################################

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
	
	def __init__(self, repo, data=None, headers={}, status_code=None, raw_response=None):

		# resources are combination of data and headers
		self.data = data
		self.headers = headers
		self.status_code = status_code
		self.raw_response = raw_response

		# repository handle is pinned to resource instance here
		self.repo = repo


	def exists(self):
		
		'''
		Check if resource exists, returns bool
		'''

		response = self.repo.api.head(self.uri)
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
			self.repo.api.put(self.uri, self.data, self.headers)
		else:
			logger.debug('resource %s exists, aborting create' % self.uri)


	def delete(self, remove_tombstone=True):

		'''
		account for tombstone
		'''

		self.repo.api.delete(self.uri)

		if remove_tombstone:
			self.repo.api.delete("%s/fcr:tombstone" % self.uri)



# NonRDF Source
class NonRDFSource(Resource):

	'''
	Linked Data Platform Non-RDF Source (LDP-NR)
	An LDPR whose state is not represented in RDF. For example, these can be binary or text documents that do not have useful RDF representations.
	https://www.w3.org/TR/ldp/
	'''
	
	def __init__(self, repo, uri, data=None, headers={}, status_code=None, raw_response=None):

		self.uri = uri
		
		# fire parent Container init()
		super().__init__(repo, data=data, headers=headers, status_code=status_code, raw_response=raw_response)


# 'Binary' alias for NonRDFSource
Binary = NonRDFSource


# RDF Source
class RDFResource(Resource):

	'''
	Linked Data Platform RDF Source (LDP-RS)
	An LDPR whose state is fully represented in RDF, corresponding to an RDF graph. See also the term RDF Source from [rdf11-concepts].
	https://www.w3.org/TR/ldp/
	'''
	
	def __init__(self, repo, data=None, headers={}, status_code=None, raw_response=None):
		
		# fire parent Resource init()
		super().__init__(repo, data=data, headers=headers, status_code=status_code, raw_response=raw_response)



# Container
class Container(RDFResource):
	
	'''
	Linked Data Platform Container (LDPC)
	A LDP-RS representing a collection of linked documents (RDF Document [rdf11-concepts] or information resources [WEBARCH]) that responds to client requests for creation, modification, and/or enumeration of its linked members and documents, and that conforms to the simple lifecycle patterns and conventions in section 5. Linked Data Platform Containers.
	https://www.w3.org/TR/ldp/
	'''

	def __init__(self, repo, data=None, headers={}, status_code=None, raw_response=None):
		
		# fire parent RDFResource init()
		super().__init__(repo, data=data, headers=headers, status_code=status_code, raw_response=raw_response)


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
	
	def __init__(self, repo, uri, data=None, headers={}, status_code=None, raw_response=None):

		self.uri = uri
		self.data = data
		self.headers = headers
		self.status_code = status_code
		self.raw_response = raw_response
		
		# fire parent Container init()
		super().__init__(repo, data=data, headers=headers, status_code=status_code, raw_response=raw_response)



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


