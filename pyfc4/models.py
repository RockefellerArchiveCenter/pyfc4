# pyfc4

import copy
import datetime
import io
import json
import rdflib
from rdflib.compare import to_isomorphic, graph_diff
import rdflib_jsonld
import requests
from types import SimpleNamespace

# logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



class Repository(object):
	
	'''
	Class for Fedora Commons 4 (FC4), LDP server instance

	Args:
		root (str): Full URL of repository REST endpoint (e.g. http://localhost:8080/rest)
		username (str): username for authorization and roles
		password (str): password authorziation and roles
		context (dict): dictionary of namespace prefixes and namespace URIs that propagate to Resources 
		default_serialization (str): mimetype of default Accept and Content-Type headers

	Attributes:
		context (dict): Default dictionary of namespace prefixes and namespace URIs
	'''

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
			context = None,
			default_serialization = 'application/rdf+xml',
			txn_uri = None
		):

		self.root = root
		if not self.root.endswith('/'): # ensure trailing slash
			self.root += '/'
		self._root_persist = self.root
		self.username = username
		self.password = password
		self.default_serialization = default_serialization

		# API facade
		self.api = API(self)

		# if context provided, merge with defaults
		if context:
			logger.debug('context provided, merging with defaults')
			self.context.update(context)

		# transaction
		self.in_txn = False

		# if txn_uri is provided, attempt to retrieve and set transaction
		if txn_uri:
			self.get_txn(txn_uri)


	def parse_uri(self, uri, use_non_txn_root=False):
	
		'''
		parses and cleans up possible uri inputs, return instance of rdflib.term.URIRef

		Args:
			uri (rdflib.term.URIRef,str): input URI

		Returns:
			rdflib.term.URIRef
		'''

		# if use_non_txn_root, use original persisted root
		if use_non_txn_root:
			root = self._root_persist
		else:
			root = self.root

		# no uri provided, assume root
		if not uri:
			return rdflib.term.URIRef(root)

		# string uri provided
		elif type(uri) == str:

			# assume "short" uri, expand with repo root
			if type(uri) == str and not uri.startswith('http'):
				return rdflib.term.URIRef("%s%s" % (root, uri))

			# else, assume full uri
			else:
				return rdflib.term.URIRef(uri)

		# already cleaned and URIRef type
		else:
			return uri


	def get_resource(self, uri, response_format=None):

		'''
		return appropriate Resource-type instance
			- issue HEAD request, determine Resource type (BasicContainer, DirectContainer, IndirectContainer, or NonRDFSource (Binary))
			- issue GET request and retrieve resource metadata at uri/fcr:metadata

		Args:
			uri (rdflib.term.URIRef,str): input URI
			response_format (str): expects mimetype / Content-Type header such as 'application/rdf+xml', 'text/turtle', etc.

		Returns:
			Resource
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
			get_response = self.api.http_request(
				'GET',
				"%s/fcr:metadata" % uri,
				response_format=response_format)

			# fire request
			return resource_type(self,
				uri,
				data=get_response.content,
				headers=get_response.headers,
				status_code=get_response.status_code)

		else:
			raise Exception('error retrieving resource uri %s' % uri)


	def get_txn(self, txn_uri):

		'''
		Retrieve transaction, parse txn prefix from headers,
		and set self.root as txn URI.

		Args:
			txn_prefix (str, rdflib.term.URIRef): uri of the transaction. e.g. http://localhost:8080/rest/txn:123456789
		
		Return:
			None
		'''

		# parse uri
		txn_uri = self.parse_uri(txn_uri, use_non_txn_root=True)

		# request new transaction
		txn_response = self.api.http_request('GET',txn_uri, data=None, headers=None)

		# if 201, transaction was created
		if txn_response.status_code == 200:
			logger.debug("transactoin found: %s" % txn_uri)
			# set self.root with txn prefix
			if not txn_uri.endswith('/'): # ensure trailing slash
				txn_uri += '/'
			self.root = txn_uri
			# set in_txn flag 
			self.in_txn = txn_uri
			return True

		# if 410, transaction does not exist
		elif txn_response.status_code == 404:
			logger.debug("transaction does not exist: %s" % self.root)
			return False

		else:
			raise Exception('could not start transaction')


	def start_txn(self):

		'''
		Request new transaction, parse txn prefix from headers,
		and set self.root as txn URI.

		Args:
			None
		
		Return:
			None
		'''

		if not self.in_txn:
			# request new transaction
			txn_response = self.api.http_request('POST','%s/fcr:tx' % self.root, data=None, headers=None)

			# if 201, transaction was created
			if txn_response.status_code == 201:
				txn_uri = txn_response.headers['Location']
				logger.debug("initiating transaction: %s" % txn_uri)
				# set self.root with txn prefix
				if not txn_uri.endswith('/'): # ensure trailing slash
					txn_uri += '/'
				self.root = txn_uri 
				# set in_txn flag 
				self.in_txn = txn_uri
				return True

			else:
				raise Exception('could not start transaction')

		else:
			raise Exception('repository instance currently in transcation: %s' % self.in_txn)


	def continue_txn(self):

		'''
		Keep current transaction alive

		Args:
			None

		Return:
			None
		'''

		if self.in_txn:

			# keep transaction alive
			txn_response = self.api.http_request('POST','%s/fcr:tx' % self.root, data=None, headers=None)

			# if 204, transaction kept alive
			if txn_response.status_code == 204:
				logger.debug("continuing transaction: %s" % self.root)
				return  True

			# if 410, transaction does not exist
			elif txn_response.status_code == 410:
				logger.debug("transaction does not exist: %s" % self.root)
				return False

			else:
				raise Exception('could not continue transaction')

		else:
			raise Exception('repository instance not currently in a transcation')


	def commit_txn(self):

		'''
		Commit transaction, all changes saved, return self.root to originally instantiated root

		Args:
			None
		
		Return:
			(bool)
		'''

		if self.in_txn:
			# commit transaction
			txn_response = self.api.http_request('POST','%s/fcr:tx/fcr:commit' % self.root, data=None, headers=None)

			# if 204, transaction was committed
			if txn_response.status_code == 204:
				logger.debug("committing transaction: %s" % self.root)
				# set self.root with txn prefix
				self.root = self._root_persist
				# set in_txn flag 
				self.in_txn = False
				# return
				return True

			# if 410, transaction does not exist
			elif txn_response.status_code == 410:
				logger.debug("transaction does not exist: %s" % self.root)
				return False

			else:
				raise Exception('could not commit transaction')

		else:
			raise Exception('repository instance not currently in a transcation')


	def rollback_txn(self):

		'''
		Rollback transaction, no changes are made, return self.root to originally instantiated root

		Args:
			None
		
		Return:
			None
		'''

		if self.in_txn:
			# rollback transaction
			txn_response = self.api.http_request('POST','%s/fcr:tx/fcr:rollback' % self.root, data=None, headers=None)

			# if 204, transaction was committed
			if txn_response.status_code == 204:
				logger.debug("committing transaction: %s" % self.root)
				# set self.root with txn prefix
				self.root = self._root_persist
				# set in_txn flag 
				self.in_txn = False
				# return 
				return True

			# if 410, transaction does not exist
			elif txn_response.status_code == 410:
				logger.debug("transaction does not exist: %s" % self.root)
				return False

			else:
				raise Exception('could not commit transaction')

		else:
			raise Exception('repository instance not currently in a transcation')



class API(object):

	'''
	API for making requests and parsing responses from repository endpoint

	Args:
		repo (Repository): instance of Repository class
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
			is_rdf = True,
			stream = False
		):

		'''
		Primary route for all HTTP requests to repository.  Ability to set most parameters for requests library,
		with some additional convenience parameters as well.

		Args:
			verb (str): HTTP verb to use for request, e.g. PUT, POST, GET, HEAD, PATCH, etc.
			uri (rdflib.term.URIRef,str): input URI
			data (str,file): payload of data to send for request, may be overridden in preperation of request
			headers (dict): optional dictionary of headers passed directly to requests.request
			files (dict): optional dictionary of files passed directly to requests.request
			response_format (str): desired response format for resource's payload, e.g. 'application/rdf+xml', 'text/turtle', etc.
			is_rdf (bool): if True, set Accept header based on combination of response_format and headers
			stream (bool): passed directly to requests.request for stream parameter

		Returns:
			requests.models.Response
		'''

		# set content negotiated response format for RDFSources
		if is_rdf:
			'''
			Acceptable content negotiated response formats include:
				application/ld+json (discouraged, if not prohibited, as it drops prefixes used in repository)
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
					response_format = self.repo.default_serialization
				# if headers present, append
				if headers and 'Accept' not in headers.keys():
					headers['Accept'] = response_format
				# if headers are blank, init dictionary
				else:
					headers = {'Accept':response_format}

		# prepare uri for HTTP request
		if type(uri) == rdflib.term.URIRef:
			uri = uri.toPython()

		logger.debug("%s request for %s, format %s, headers %s" % 
			(verb, uri, response_format, headers))

		# manually prepare request
		session = requests.Session()
		request = requests.Request(verb, uri, data=data, headers=headers, files=files)
		prepped_request = session.prepare_request(request)
		response = session.send(prepped_request,
			stream=stream,
		)
		return response


	def parse_resource_type(self, response):

		'''
		parse resource type from self.http_request()

		Args:
			response (requests.models.Response): response object

		Returns:
			[NonRDFSource, BasicContainer, DirectContainer, IndirectContainer]
		'''
		
		# parse 'Link' header
		links = [
			link.split(";")[0]
			for link in response.headers['Link'].split(', ')
			if link.startswith('<http://www.w3.org/ns/ldp#')]
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



class SparqlUpdate(object):

	'''
	Class to handle the creation of Sparql updates via PATCH request.
	Accepts prefixes and graphs from resource, computes diff of graphs, and builds sparql query for update.

	Args:
		prefixes (types.SimpleNamespace): prefixes from resource at self.rdf.prefixes
		diffs (types.SimpleNamespace): diffs is comprised of three graphs that are derived from self._diff_graph(), at self.rdf.diffs 
	'''

	def __init__(self, prefixes, diffs):

		self.prefixes = prefixes
		self.diffs = diffs

		# prefixes and namespaces
		self.update_namespaces = set()
		self.update_prefixes = {}

	
	def _derive_namespaces(self):

		'''
		Small method to loop through three graphs in self.diffs, identify unique namespace URIs.
		Then, loop through provided dictionary of prefixes and pin one to another.

		Args:
			None: uses self.prefixes and self.diffs

		Returns:
			None: sets self.update_namespaces and self.update_prefixes
		'''

		# iterate through graphs and get unique namespace uris
		for graph in [self.diffs.overlap, self.diffs.removed, self.diffs.added]:
			for s,p,o in graph:
				ns_prefix, ns_uri, predicate = graph.compute_qname(p)
				self.update_namespaces.add(ns_uri)
		logger.debug(self.update_namespaces)

		# build unique prefixes dictionary
		for ns_uri in self.update_namespaces:
			for k in self.prefixes.__dict__:
				if str(ns_uri) == str(self.prefixes.__dict__[k]):
					logger.debug('adding prefix %s for uri %s to unique_prefixes' % (k,str(ns_uri)))
					self.update_prefixes[k] = self.prefixes.__dict__[k]


	def build_query(self):

		'''
		Using the three graphs derived from self._diff_graph(), build a sparql update query in the format:
		
		PREFIX foo: <http://foo.com>
		PREFIX bar: <http://bar.com>

		DELETE {...}
		INSERT {...}
		WHERE {...}

		Args:
			None: uses variables from self

		Returns:
			(str) sparql update query as string

		'''

		# derive namespaces to include prefixes in Sparql update query
		self._derive_namespaces()

		q = ''

		# add prefixes
		for ns_prefix, ns_uri in self.update_prefixes.items():
			q += "PREFIX %s: <%s>\n" % (ns_prefix, str(ns_uri))

		# deletes
		removed_serialized = self.diffs.removed.serialize(format='nt').decode('utf-8')
		q += '\nDELETE {\n%s}\n\n' % removed_serialized

		# inserts
		added_serialized = self.diffs.added.serialize(format='nt').decode('utf-8')
		q += '\nINSERT {\n%s}\n\n' % added_serialized

		# where (not yet implemented)
		q += 'WHERE {}'

		# debug
		logger.debug(q)

		return q



class Resource(object):

	'''
	Linked Data Platform Resource (LDPR)
	A HTTP resource whose state is represented in any way that conforms to the simple lifecycle patterns and conventions in section 4. Linked Data Platform Resources.
	https://www.w3.org/TR/ldp/

	In the LDP hierarchy, this class represents the most abstract entity of "Resource".

	Sub-classed by:
		NonRDFSource, Container

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		data (): passed from sub-classes
		headers (dict): passed from sub-classes
		status_code (int): passed from sub-classes
		rdf_prefixes_mixins (dict): optional rdf prefixes and namespaces
	'''
	
	def __init__(self,
		repo,
		uri=None,
		data=None,
		headers={},
		status_code=None,
		rdf_prefixes_mixins=None):

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

		'''
		return rdflib.term.URIRef URI as string

		Returns:
			(str)
		'''

		return self.uri.toPython()


	def check_exists(self):
		
		'''
		Check if resource exists, update self.exists, returns

		Returns:
			None: sets self.exists
		'''

		response = self.repo.api.http_request('HEAD', self.uri)
		self.status_code = response.status_code
		if self.status_code == 200:
			self.exists = True
		if self.status_code == 404:
			self.exists = False
		return self.exists


	def create(self, specify_uri=False, ignore_tombstone=False, serialization_format=None):

		'''
		Primary method to create resources.

		Args:
			specify_uri (bool): If True, uses PUT verb and sets the URI during creation.  If False, uses POST and gets repository minted URI
			ignore_tombstone (bool): If True, will attempt creation, if tombstone exists (409), will delete tombstone and retry
			serialization_format(str): Content-Type header / mimetype that will be used to serialize self.rdf.graph, and set headers for PUT/POST requests
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

			# otherwise, prep for RDF
			else:
				# determine serialization
				if not serialization_format:
					serialization_format = self.repo.default_serialization
				data = self.rdf.graph.serialize(format=serialization_format)
				self.headers['Content-Type'] = serialization_format
			
			# fire creation request
			response = self.repo.api.http_request(verb, self.uri, data=data, headers=self.headers)
			return self._handle_create(response, ignore_tombstone)
			

	def _handle_create(self, response, ignore_tombstone):

		'''
		Handles response from self.create()

		Args:
			response (requests.models.Response): response object from self.create()
			ignore_tombstone (bool): If True, will attempt creation, if tombstone exists (409), will delete tombstone and retry
		'''

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
			if ignore_tombstone:
				response = self.repo.api.http_request('DELETE', '%s/fcr:tombstone' % self.uri)
				if response.status_code == 204:
					logger.debug('tombstone removed, retrying create')
					self.create()
				else:
					raise Exception('Could not remove tombstone for %s' % self.uri)
			else:
				raise Exception('tombstone for %s detected, aborting' % self.uri)

		# 415, unsupported media type
		elif response.status_code == 415:
			raise Exception('unsupported media type')

		# unknown status code
		else:
			raise Exception('unknown error creating, status code: %s' % response.status_code)

		# if all goes well, return True
		return True


	def delete(self, remove_tombstone=True):

		'''
		Method to delete resources.

		Args:
			remove_tombstone (bool): If True, will remove tombstone at uri/fcr:tombstone when removing resource.

		Returns:
			(bool)
		'''

		response = self.repo.api.http_request('DELETE', self.uri)

		# update exists
		if response.status_code == 204:
			# removal successful, updating self
			self._empty_resource_attributes()

		if remove_tombstone:
			self.repo.api.http_request('DELETE', '%s/fcr:tombstone' % self.uri)

		return True


	def refresh(self):
		
		'''
		Performs GET request and refreshes RDF information for resource.

		Args:
			None

		Returns:
			None
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
				self._parse_graph()
			# cleanup
			del(updated_self)
		else:
			logger.debug('resource %s not found, dumping values')
			self._empty_resource_attributes()
			

	def _build_rdf(self, data=None):

		'''
		Parse incoming rdf as self.rdf.orig_graph, create copy at self.rdf.graph

		Args:
			data (): payload from GET request, expected RDF content in various serialization formats

		Returns:
			None
		'''

		# recreate rdf data
		self.rdf = SimpleNamespace()
		self.rdf.data = data
		self.rdf.prefixes = SimpleNamespace()
		# populate prefixes
		for prefix,uri in self.repo.context.items():
			setattr(self.rdf.prefixes, prefix, rdflib.Namespace(uri))
		# graph
		self._parse_graph()


	def _parse_graph(self):

		'''
		use Content-Type from headers to determine parsing method

		Args:
			None

		Return:
			None: sets self.rdf by parsing data from GET request, or setting blank graph of resource does not yet exist
		'''

		# if resource exists, parse self.rdf.data
		if self.exists:
			# handle edge case for content-types not recognized by rdflib parser
			if self.headers['Content-Type'].startswith('text/plain'):
				logger.debug('text/plain Content-Type detected, using application/n-triples for parser')
				parse_format = 'application/n-triples'
			else:
				parse_format = self.headers['Content-Type']

			# clean parse format for rdf parser (see: https://www.w3.org/2008/01/rdf-media-types)
			if ';charset' in parse_format:
				parse_format = parse_format.split(';')[0]
			
			# parse graph	
			self.rdf.graph = rdflib.Graph().parse(
				data=self.rdf.data.decode('utf-8'),
				format=parse_format)

		# else, create empty graph
		else:
			self.rdf.graph = rdflib.Graph()
			
		# bind any additional namespaces from repo instance, but do not override
		self.rdf.namespace_manager = rdflib.namespace.NamespaceManager(self.rdf.graph)
		for ns_prefix, ns_uri in self.rdf.prefixes.__dict__.items():
			self.rdf.namespace_manager.bind(ns_prefix, ns_uri, override=False)

		# conversely, add namespaces from parsed graph to self.rdf.prefixes
		for ns_prefix, ns_uri in self.rdf.graph.namespaces():
			setattr(self.rdf.prefixes, ns_prefix, rdflib.Namespace(ns_uri))

		# pin old graph to resource, create copy graph for modifications
		self.rdf._orig_graph = copy.deepcopy(self.rdf.graph)


	def _diff_graph(self):

		'''
		Uses rdflib.compare diff, https://github.com/RDFLib/rdflib/blob/master/rdflib/compare.py
		When a resource is retrieved, the graph retrieved and parsed at that time is saved to self.rdf._orig_graph,
		and all local modifications are made to self.rdf.graph.  This method compares the two graphs and returns the diff
		in the format of three graphs:

			overlap - triples shared by both
			removed - triples that exist ONLY in the original graph, self.rdf._orig_graph
			added - triples that exist ONLY in the modified graph, self.rdf.graph

		These are used for building a sparql update query for self.update.

		Args:
			None
		
		Returns:
			None: sets self.rdf.diffs and adds the three graphs mentioned, 'overlap', 'removed', and 'added'
		'''

		overlap, removed, added = graph_diff(
			to_isomorphic(self.rdf._orig_graph),
			to_isomorphic(self.rdf.graph))
		diffs = SimpleNamespace()
		diffs.overlap = overlap
		diffs.removed = removed
		diffs.added = added
		self.rdf.diffs = diffs


	def add_namespace(self, ns_prefix, ns_uri):

		'''
		preferred method is to instantiate with repository under 'context',
		but prefixes / namespaces can be added for a Resource instance

		adds to self.rdf.prefixes which will endure through create/update/refresh,
		and get added back to parsed graph namespaces

		Args:
			ns_prefix (str): prefix for namespace, e.g. 'dc', 'foaf'
			ns_uri (str): string of namespace / ontology. e.g. 'http://purl.org/dc/elements/1.1/', 'http://xmlns.com/foaf/0.1/'

		Returns:
			None: binds this new prefix:namespace combination to self.rdf.prefixes for use, and self.rdf.graph for serialization
		'''

		# add to prefixes
		setattr(self.rdf.prefixes, ns_prefix, rdflib.Namespace(ns_uri))

		# bind to graph
		self.rdf.namespace_manager.bind(ns_prefix, ns_uri, override=False)


	def _build_binary(self):

		'''
		builds binary attributes for resource

		Args:
			None

		Return:
			None: sets various attributes
		'''

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

		Args:
			None

		Return:
			None: empties selected resource attributes
		'''

		self.status_code = 404
		self.headers = {}
		self.exists = False

		# build RDF
		self.rdf = self._build_rdf()

		# if NonRDF recreate binary data
		if type(self) == NonRDFSource:
			self._build_binary()


	def _handle_object(self, object_input):

		'''
		Method to handle possible values passed for adding, removing, modifying triples.
		Detects type of input and sets appropriate http://www.w3.org/2001/XMLSchema# datatype

		Args:
			object_input (str,int,datetime,): many possible inputs

		Returns:
			(rdflib.term.Literal): with appropriate datatype attribute
		'''

		# if object is string, convert to rdflib.term.Literal with appropriate datatype
		if type(object_input) == str:
			return rdflib.term.Literal(object_input, datatype=rdflib.XSD.string)

		# integer
		elif type(object_input) == int:
			return rdflib.term.Literal(object_input, datatype=rdflib.XSD.int)

		# float
		elif type(object_input) == float:
			return rdflib.term.Literal(object_input, datatype=rdflib.XSD.float)

		# date
		elif type(object_input) == datetime.datetime:
			return rdflib.term.Literal(object_input, datatype=rdflib.XSD.date)

		else:
			return object_input


	def add_triple(self, p, o):

		'''
		add triple by providing p,o, assumes s = subject

		Args:
			p (rdflib.term.URIRef): predicate
			o (): object

		Returns:
			None: adds triple to self.rdf.graph
		'''

		self.rdf.graph.add((self.uri, p, self._handle_object(o)))


	def set_triple(self, p, o):
		
		'''
		Assuming the predicate or object matches a single triple, sets the other for that triple.

		Args:
			p (rdflib.term.URIRef): predicate
			o (): object

		Returns:
			None: modifies pre-existing triple in self.rdf.graph
		'''
		
		self.rdf.graph.set((self.uri, p, self._handle_object(o)))


	def remove_triple(self, p, o):

		'''
		remove triple by supplying p,o

		Args:
			p (rdflib.term.URIRef): predicate
			o (): object

		Returns:
			None: removes triple from self.rdf.graph
		'''

		self.rdf.graph.remove((self.uri, p, self._handle_object(o)))


	def triples(self, p=None, o=None):

		'''
		convenience method for self.rdf.graph.triples

		Args:
			p (rdflib.term.URIRef): predicate
			o (): object

		Returns:
			(generator)

		'''

		return self.rdf.graph.triples((self.uri, p, o))


	# update RDF, and for NonRDFSource, binaries
	def update(self, sparql_query_only=False):

		'''
		Method to update resources in repository.  Firing this method computes the difference in the local modified graph and the original one, 
		creates an instance of SparqlUpdate and builds a sparql query that represents these differences, and sends this as a PATCH request.

		If the resource is NonRDF (Binary), this also method also updates the binary data.

		Args:
			sparql_query_only (bool): If True, returns only the sparql query string and does not perform any actual updates

		Returns:
			(bool) 
		'''

		# run diff on graphs, send as PATCH request
		self._diff_graph()		
		sq = SparqlUpdate(self.rdf.prefixes, self.rdf.diffs)
		if sparql_query_only:
			return sq.build_query()
		response = self.repo.api.http_request(
			'PATCH',
			self.uri,
			data=sq.build_query(),
			headers={'Content-Type':'application/sparql-update'})

		# if NonRDFSource, update binary as well
		if type(self) == NonRDFSource:
			self._prep_binary_data()
			binary_data = self.binary.data
			binary_response = self.repo.api.http_request(
				'PUT',
				self.uri,
				data=binary_data,
				headers={'Content-Type':self.binary.mimetype})

		# if status_code == 204, resource changed, refresh graph
		if response.status_code == 204:
			self.refresh()
			return True



# NonRDF Source
class NonRDFSource(Resource):

	'''
	Linked Data Platform Non-RDF Source (LDP-NR)
	An LDPR whose state is not represented in RDF. For example, these can be binary or text documents that do not have useful RDF representations.
	https://www.w3.org/TR/ldp/

	Inherits:
		Resource

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		data (): passed from sub-classes
		headers (dict): passed from sub-classes
		status_code (int): passed from sub-classes
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
		
		# like RDF, if exists, retrieve binary data
		if self.exists:

			# get mimetype
			self.binary.mimetype = self.rdf.graph.value(
				self.uri,
				self.rdf.prefixes.ebucore.hasMimeType).toPython()
			self.binary.data = self.repo.api.http_request(
				'GET',
				self.uri,
				data=None,
				headers={'Content-Type':self.binary.mimetype},
				is_rdf=False,
				stream=True).content


	def _prep_binary_data(self):

		'''
		method is used to check/prep data and headers for NonRDFSource create or update

		Args:
			None

		Returns:
			None: sets attributes in self.binary and headers
		'''

		logger.debug('preparing NonRDFSource data for create/update')

		# handle mimetype / Content-Type
		self._prep_binary_mimetype()

		# handle binary data
		self._prep_binary_content()
		

	def _prep_binary_mimetype(self):

		'''
		Sets Content-Type header based on headers and/or self.binary.mimetype values
		Implicitly favors Content-Type header if set

		Args:
			None

		Returns:
			None: sets attributes in self.binary and headers
		'''

		# neither present
		if not self.binary.mimetype and 'Content-Type' not in self.headers.keys():
			raise Exception('to create/update NonRDFSource, mimetype or Content-Type header is required')
		
		# mimetype, no Content-Type
		elif self.binary.mimetype and 'Content-Type' not in self.headers.keys():
			logger.debug('setting Content-Type header with provided mimetype: %s'
				% self.binary.mimetype)
			self.headers['Content-Type'] = self.binary.mimetype


	def _prep_binary_content(self):

		'''		
		Sets delivery method of either payload or header
		Favors Content-Location header if set

		Args:
			None

		Returns:
			None: sets attributes in self.binary and headers
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


# 'Binary' is an alias for NonRDFSource
Binary = NonRDFSource


# RDF Source
class RDFResource(Resource):

	'''
	Linked Data Platform RDF Source (LDP-RS)
	An LDPR whose state is fully represented in RDF, corresponding to an RDF graph. See also the term RDF Source from [rdf11-concepts].
	https://www.w3.org/TR/ldp/

	Sub-classed by:
		Container

	Inherits:
		Resource

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		data (): passed from sub-classes
		headers (dict): passed from sub-classes
		status_code (int): passed from sub-classes
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

	Sub-classed by:
		BasicContainer, IndirectContainer, DirectContainer

	Inherits:
		RDFResource

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		data (): passed from sub-classes
		headers (dict): passed from sub-classes
		status_code (int): passed from sub-classes
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

	Inherits:
		Container

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		data (): passed from sub-classes
		headers (dict): passed from sub-classes
		status_code (int): passed from sub-classes
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

	Inherits:
		Container

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		data (): passed from sub-classes
		headers (dict): passed from sub-classes
		status_code (int): passed from sub-classes
		membershipResource (rdflib.term.URIRef): resource that will accumlate triples as children are added
		hasMemberRelation (rdflib.term.URIRef): predicate that will be used when pointing from URI in ldp:membershipResource to children
	'''
	
	def __init__(self,
		repo,
		uri=None,
		data=None,
		headers={},
		status_code=None,
		membershipResource=None,
		hasMemberRelation=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, data=data, headers=headers, status_code=status_code)

		# if resource does not yet exist, set rdf:type
		self.add_triple(self.rdf.prefixes.rdf.type, self.rdf.prefixes.ldp.DirectContainer)

		# if membershipResource or hasMemberRelation args are set, set triples
		if membershipResource:
			self.add_triple(self.rdf.prefixes.ldp.membershipResource, membershipResource)
		if hasMemberRelation:
			self.add_triple(self.rdf.prefixes.ldp.hasMemberRelation, hasMemberRelation)



# Indirect Container
class IndirectContainer(Container):
	
	'''
	Linked Data Platform Indirect Container (LDP-IC)
	An LDPC similar to a LDP-DC that is also capable of having members whose URIs are based on the content of its contained documents rather than the URIs assigned to those documents.
	https://www.w3.org/TR/ldp/

	Inherits:
		Container

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		data (): passed from sub-classes
		headers (dict): passed from sub-classes
		status_code (int): passed from sub-classes
		membershipResource (rdflib.term): resource that will accumlate triples as children are added
		hasMemberRelation (rdflib.term): predicate that will be used when pointing from URI in ldp:membershipResource to ldp:insertedContentRelation
		insertedContentRelation (rdflib.term): destination for ldp:hasMemberRelation from ldp:membershipResource
	'''

	def __init__(self,
		repo,
		uri=None,
		data=None,
		headers={},
		status_code=None,
		membershipResource=None,
		hasMemberRelation=None,
		insertedContentRelation=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, data=data, headers=headers, status_code=status_code)
	
		# if resource does not yet exist, set rdf:type
		self.add_triple(self.rdf.prefixes.rdf.type, self.rdf.prefixes.ldp.IndirectContainer)

		# if membershipResource, hasMemberRelation, or insertedContentRelation args are set, set triples
		if membershipResource:
			self.add_triple(self.rdf.prefixes.ldp.membershipResource, membershipResource)
		if hasMemberRelation:
			self.add_triple(self.rdf.prefixes.ldp.hasMemberRelation, hasMemberRelation)
		if insertedContentRelation:
			self.add_triple(self.rdf.prefixes.ldp.insertedContentRelation, insertedContentRelation)


