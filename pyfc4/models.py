# pyfc4

import io
import json
import rdflib
import rdflib_jsonld
import requests
from types import SimpleNamespace

# logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



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

		# convenience root resource handle
		# self.root_resource = self.get_resource('')


	def parse_uri(self, uri):
	
		'''
		parses and cleans up possible uri inputs, return instance of rdflib.term.URIRef
		'''

		# no uri provided, assume root
		if not uri:
			return rdflib.term.URIRef(self.root)

		# string uri provided
		elif type(uri) == str:

			# assume "short" uri, expand with repo.root
			if type(uri) == str and not uri.startswith('http'):
				return rdflib.term.URIRef("%s%s" % (self.root, uri))

			# else, assume full uri
			else:
				return rdflib.term.URIRef(uri)

		# already cleaned and URIRef type
		else:
			return uri


	def get_resource(self, uri, response_format=None):

		'''
		return appropriate Resource-type instance
			- issue HEAD request, sniff out content-type to detect NonRDF
			- issue GET request 
		'''

		# handle uri
		uri = self.parse_uri(uri)

		# HEAD request to detect resource type
		head_response = self.api.http_request('HEAD', uri)

		# 404, item does not exist, return False
		if head_response.status_code == 404:
			logger.debug('resource uri %s not found, returning False' % uri)
			return False

		# assume exists, parse headers for resource type and return instance
		elif head_response.status_code == 200:

			# parse LDP resource type from headers
			resource_type = self.api.parse_resource_type(head_response)
			logger.debug('using resource type: %s' % resource_type)

			# fire GET request
			get_response = self.api.http_request('GET', "%s/fcr:metadata" % uri, response_format=response_format)

			# fire request
			return resource_type(self, uri, data=get_response.content, headers=get_response.headers, status_code=get_response.status_code)

		else:
			raise Exception('error retrieving resource uri %s' % uri)



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
			files=None,
			response_format=None,
			is_rdf = True
		):

		# set content negotiated response format for RDFSources
		if is_rdf:
			'''
			Acceptable content negotiated response formats include:
				application/ld+json
				application/n-triples
				application/rdf+xml
				text/n3 (or text/rdf+n3)
				text/plain
				text/turtle (or application/x-turtle)
			'''
			# set for GET requests only
			if verb == 'GET':
				# if no response_format has been requested to this point, use repository instance default
				if not response_format:
					response_format = self.repo.default_response_format
				# if headers present, append
				if headers and 'Accept' not in headers.keys():
					headers['Accept'] = response_format
				# if headers are blank, init dictionary
				else:
					headers = {'Accept':response_format}


		# prepare uri for HTTP request
		if type(uri) == rdflib.term.URIRef:
			uri = uri.toPython()

		logger.debug("%s request for %s, format %s, headers %s" % (verb, uri, response_format, headers))

		# manually prepare request
		session = requests.Session()
		request = requests.Request(verb, uri, data=data, headers=headers, files=files)
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



class RDFPrefixes(object):

	'''
	Small class for taking default contexts from the repository instance
	'''

	def __init__(self, repo, rdf_prefixes_mixins=None):

		# initiate rdflib namespaces
		for prefix,uri in repo.context.items():
			setattr(self, prefix, rdflib.Namespace(uri))

		# include mixins (overwrites repository instance entries where applicable)
		if rdf_prefixes_mixins:
			for prefix,uri in rdf_prefixes_mixins.items():
				setattr(self, prefix, rdflib.Namespace(uri))



# Resource
class Resource(object):

	'''
	Linked Data Platform Resource (LDPR)
	A HTTP resource whose state is represented in any way that conforms to the simple lifecycle patterns and conventions in section 4. Linked Data Platform Resources.
	https://www.w3.org/TR/ldp/
	'''
	
	def __init__(self, repo, uri=None, data=None, headers={}, status_code=None, rdf_prefixes_mixins=None):

		# repository handle is pinned to resource instance here
		self.repo = repo

		# parse uri with parse_uri() from repo instance
		self.uri = self.repo.parse_uri(uri)
		
		# HTTP
		self.headers = headers
		self.status_code = status_code
		# if status_code provided, and 200, set exists attribute as True
		if self.status_code == 200:
			self.exists = True
		else:
			self.exists = False

		# RDF
		self._build_rdf(data=data)




	def __repr__(self):
		return '<%s Resource, uri: %s>' % (self.__class__.__name__, self.uri)


	def uri_as_string(self):
		return self.uri.toPython()


	def check_exists(self):
		
		'''
		Check if resource exists, update self.exists, returns
		'''

		response = self.repo.api.http_request('HEAD', self.uri)
		self.status_code = response.status_code
		if self.status_code == 200:
			self.exists = True
		if self.status_code == 404:
			self.exists = False
		return self.exists


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

		# clean parse format for rdf parser (see: https://www.w3.org/2008/01/rdf-media-types)
		if ';charset' in parse_format:
			parse_format = parse_format.split(';')[0]
		
		# parse and return graph	
		return rdflib.Graph().parse(data=self.rdf.data.decode('utf-8'), format=parse_format)


	def create(self, specify_uri=False, ignore_tombstone=False):

		'''
		when object is created, self.data and self.headers are passed with the requests
		'''

		# if resource claims existence, raise exception
		if self.exists:
			raise Exception('resource exists attribute True, aborting')

		# else, continue
		else:

			# determine verb based on specify_uri parameter
			if specify_uri:
				verb = 'PUT'
			else:
				verb = 'POST'
			
			logger.debug('creating resource %s with verb %s' % (self.uri, verb))

			# check if NonRDFSource, if so, run _prep_binary_data() and set data to self.binary.data
			if type(self) == NonRDFSource:
				self._prep_binary_data()
				data = self.binary.data
			# otherwise, set data as self.rdf.data
			else:
				data = self.rdf.data
			
			# fire creation request
			response = self.repo.api.http_request(verb, self.uri, data=data, headers=self.headers)
			return self._handle_create(response, ignore_tombstone)
			

	def _handle_create(self, response, ignore_tombstone):

			# 201, success, refresh
			if response.status_code == 201:
				# if not specifying uri, capture from response and append to object
				self.uri = self.repo.parse_uri(response.text)
				# creation successful, update resource
				self.refresh()

			# 404, assumed POST, target location does not exist
			elif response.status_code == 404:
				raise Exception('for this POST request, target location does not exist')

			# 409, conflict, resource likely exists
			elif response.status_code == 409:
				raise Exception('resource already exists')
			
			# 410, tombstone present
			elif response.status_code == 410:
				logger.debug('tombstone for %s detected, aborting' % self.uri)
				if ignore_tombstone:
					response = self.repo.api.http_request('DELETE', '%s/fcr:tombstone' % self.uri)
					if response.status_code == 204:
						logger.debug('tombstone removed, retrying create')
						self.create()
					else:
						raise Exception('Could not remove tombstone for %s' % self.uri)

			# 415, unsupported media type
			elif response.status_code == 415:
				raise Exception('unsupported media type')

			# unknown status code
			else:
				raise Exception('unknown error creating, status code: %s' % response.status_code)

			# if all goes well, return True
			return True


	def delete(self, remove_tombstone=True):

		response = self.repo.api.http_request('DELETE', self.uri)

		# update exists
		if response.status_code == 204:
			# removal successful, updating self
			self._empty_resource_attributes()

		if remove_tombstone:
			self.repo.api.http_request('DELETE', '%s/fcr:tombstone' % self.uri)


	def refresh(self):
		
		'''
		refreshes exists, status_code, data, and headers from repo for uri
		'''

		updated_self = self.repo.get_resource(self.uri)

		# if resource type of updated_self != self, raise exception
		if type(updated_self) != type(self):
			raise Exception('Instantiated %s, but repository reports this resource is %s, raising exception' % (type(updated_self), type(self)) )

		if updated_self:
			# update attributes
			self.status_code = updated_self.status_code
			self.rdf.data = updated_self.rdf.data
			self.headers = updated_self.headers
			self.exists = updated_self.exists
			# update graph if RDFSource
			if type(self) != NonRDFSource:
				self.rdf.graph = updated_self.rdf.graph
			# cleanup
			del(updated_self)
		else:
			logger.debug('resource %s not found, dumping values')
			self._empty_resource_attributes()
			

	def _build_rdf(self, data=None):

		# recreate rdf data
		self.rdf = SimpleNamespace()
		self.rdf.data = data
		self.rdf.prefixes = RDFPrefixes(self.repo)
		self.rdf.graph = None
		if self.exists:
			self.rdf.graph = self.parse_graph()


	def _build_binary(self):

		# binary data
		self.binary = SimpleNamespace()
		self.binary.delivery = None
		self.binary.data = None
		self.binary.stream = False
		self.binary.mimetype = None # convenience attribute that is written to headers['Content-Type'] for create/update
		self.binary.location = None


	def _empty_resource_attributes(self):

		'''
		small method to empty values if resource is removed or absent
		'''

		self.status_code = 404
		self.headers = {}
		self.exists = False

		# build RDF
		self.rdf = self._build_rdf()

		# if NonRDF recreate binary data
		if type(self) == NonRDFSource:
			self._build_binary()


	def add_triple(self, p, o):

		'''
		add triple by providing p,o, assumes s = subject
		'''

		self.rdf.graph.add(p, o)


	def set_triple(self):
		
		'''
		without knowing s,p, or o, set s,p, or o
		'''
		pass


	def remove_triple(self):

		'''
		remove triple by supplying s,p,o
		'''
		pass


	def modify_triple(self):

		'''
		modify s,p, or o for a triple
		'''
		pass


	# update RDF, and for NonRDFSource, binaries
	def update(self):

		# use PUT to overwrite RDF
		response = self.repo.api.http_request('PUT', '%s/fcr:metadata' % self.uri, data=self.rdf.graph.serialize(format='turtle'), headers={'Content-Type':'text/turtle'})

		# if status_code == 204, resource changed, refresh graph
		if response.status_code == 204:
			self.refresh()


	def patch(self, sparql_query):
		pass



# NonRDF Source
class NonRDFSource(Resource):

	'''
	Linked Data Platform Non-RDF Source (LDP-NR)
	An LDPR whose state is not represented in RDF. For example, these can be binary or text documents that do not have useful RDF representations.
	https://www.w3.org/TR/ldp/
	'''
	
	def __init__(self, repo, uri=None, data=None, headers={}, status_code=None):

		self.mimetype = None

		# fire parent Resource init()
		super().__init__(repo, uri=uri, data=data, headers=headers, status_code=status_code)

		# binary data
		self.binary = SimpleNamespace()
		self.binary.delivery = None
		self.binary.data = None
		self.binary.stream = False
		self.binary.mimetype = None # convenience attribute that is written to headers['Content-Type'] for create/update
		self.binary.location = None


	def _prep_binary_data(self):

		'''
		method is used to check/prep data and headers for NonRDFSource create

		This approach from eulfedora might be helpful:
		# location of content trumps attached content
		https://github.com/emory-libraries/eulfedora/blob/master/eulfedora/models.py#L361-L367
		# sending attached content as payload (file-like object)
		https://github.com/emory-libraries/eulfedora/blob/64eaf999fbff39e809bf1d1da377a972c9685441/eulfedora/api.py#L373-L385

		Also consider external reference per FC4 spec (https://wiki.duraspace.org/display/FEDORA40/RESTful+HTTP+API+-+Containers#RESTfulHTTPAPI-Containers-BluePOSTCreatenewresourceswithinaLDPcontainer):
		Example (4): Creating a new binary resource at a specified path redirecting to external content
			curl -X PUT -H"Content-Type: message/external-body; access-type=URL; URL=\"http://www.example.com/file\"" "http://localhost:8080/rest/node/to/create"
		'''

		logger.debug('preparing NonRDFSource data for create/update')

		# handle mimetype / Content-Type
		self._prep_binary_mimetype()

		# handle binary data
		self._prep_binary_content()
		

	def _prep_binary_mimetype(self):

		'''
		implicitly favors Content-Type header if set
		'''

		# neither present
		if not self.binary.mimetype and 'Content-Type' not in self.headers.keys():
			raise Exception('to create/update NonRDFSource, mimetype or Content-Type header is required')
		
		# mimetype, no Content-Type
		elif self.binary.mimetype and 'Content-Type' not in self.headers.keys():
			logger.debug('setting Content-Type header with provided mimetype: %s' % self.binary.mimetype)
			self.headers['Content-Type'] = self.binary.mimetype


	def _prep_binary_content(self):

		'''		
		favors Content-Location header if set
		sets delivery method of either payload or header
		'''

		# nothing present
		if not self.binary.data and not self.binary.location and 'Content-Location' not in self.headers.keys():
			raise Exception('creating/updating NonRDFSource requires content from self.binary.data, self.binary.location, or the Content-Location header')

		elif 'Content-Location' in self.headers.keys():
			logger.debug('Content-Location header found, using')
			self.binary.delivery = 'header'
		
		# if Content-Location is not set, look for self.data_location then self.data
		elif 'Content-Location' not in self.headers.keys():

			# data_location set, trumps Content self.data
			if self.binary.location:
				# set appropriate header
				self.headers['Content-Location'] = self.binary.location
				self.binary.delivery = 'header'

			# data attribute is plain text, binary, or file-like object
			elif self.binary.data:

				# if file-like object, set flag for api.http_request
				if isinstance(self.binary.data, io.BufferedIOBase):
					logger.debug('detected file-like object')
					self.binary.delivery = 'payload'

				# else, just bytes
				else:
					logger.debug('detected bytes')
					self.binary.delivery = 'payload'


# 'Binary' alias for NonRDFSource
Binary = NonRDFSource


# RDF Source
class RDFResource(Resource):

	'''
	Linked Data Platform RDF Source (LDP-RS)
	An LDPR whose state is fully represented in RDF, corresponding to an RDF graph. See also the term RDF Source from [rdf11-concepts].
	https://www.w3.org/TR/ldp/
	'''
	
	def __init__(self, repo, uri=None, data=None, headers={}, status_code=None):
		
		# fire parent Resource init()
		super().__init__(repo, uri=uri, data=data, headers=headers, status_code=status_code)



# Container
class Container(RDFResource):
	
	'''
	Linked Data Platform Container (LDPC)
	A LDP-RS representing a collection of linked documents (RDF Document [rdf11-concepts] or information resources [WEBARCH]) that responds to client requests for creation, modification, and/or enumeration of its linked members and documents, and that conforms to the simple lifecycle patterns and conventions in section 5. Linked Data Platform Containers.
	https://www.w3.org/TR/ldp/
	'''

	def __init__(self, repo, uri=None, data=None, headers={}, status_code=None):
		
		# fire parent RDFResource init()
		super().__init__(repo, uri=uri, data=data, headers=headers, status_code=status_code)


	def children(self, as_resources=False):

		'''
		method to return children of this resource
		'''

		children = [o for s,p,o in self.rdf.graph.triples((None, self.rdf.prefixes.ldp.contains, None))]

		# if as_resources, issue GET requests for children and return
		if as_resources:
			logger.debug('retrieving children as resources')
			children = [ self.repo.get_resource(child) for child in children ]

		return children


	def parents(self, as_resources=False):

		'''
		method to return parent of this resource
		'''

		parents = [o for s,p,o in self.rdf.graph.triples((None, self.rdf.prefixes.fedora.hasParent, None))]

		# if as_resources, issue GET requests for children and return
		if as_resources:
			logger.debug('retrieving parent as resource')
			parents = [ self.repo.get_resource(parent) for parent in parents ]

		return parents



# Basic Container
class BasicContainer(Container):
	
	'''
	Linked Data Platform Basic Container (LDP-BC)
	An LDPC that defines a simple link to its contained documents (information resources) [WEBARCH].
	https://www.w3.org/TR/ldp/

	https://gist.github.com/hectorcorrea/dc20d743583488168703
		- "The important thing to notice is that by posting to a Basic Container, the LDP server automatically adds a triple with ldp:contains predicate pointing to the new resource created."
	'''
	
	def __init__(self, repo, uri=None, data=None, headers={}, status_code=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, data=data, headers=headers, status_code=status_code)



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


