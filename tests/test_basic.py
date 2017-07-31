
from pyfc4.models import *

import datetime
import inspect
import pytest
import rdflib
import time

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



# target location for testing container
testing_container_uri = 'testing'

# instantiate repository
repo = Repository('http://localhost:8080/rest','ghukill','password', context={'foo':'http://foo.com'})



########################################################
# SETUP
########################################################
class TestSetup(object):

	def test_create_testing_container(self):

		# attempt delete
		try:
			response = repo.api.http_request('DELETE', '%s' % testing_container_uri)
		except:
			logger.debug("uri %s not found to remove" % testing_container_uri)
		try:
			response = repo.api.http_request('DELETE', '%s/fcr:tombstone' % testing_container_uri)
		except:
			logger.debug("uri %s tombstone not found to remove" % testing_container_uri)

		tc = BasicContainer(repo, testing_container_uri)
		tc.create(specify_uri=True)
		assert tc.exists


########################################################
# TESTS
########################################################

class TestBasicCRUDPUT(object):

	
	# create foo (basic container)
	def test_create_bc(self):

		foo = BasicContainer(repo, '%s/foo' % testing_container_uri)
		foo.create(specify_uri=True)
		assert foo.exists


	# get foo via repo.get_resource()
	def test_get_bc(self):

		foo = repo.get_resource('%s/foo' % testing_container_uri)
		assert foo.exists


	# test RDF parsing of different Content-Types
	def test_graph_parse(self):

		# collect graphs
		graphs = []
		# loop through Content-Types, save parsed graphs
		content_types = [
			'application/ld+json',
			'application/n-triples',
			'application/rdf+xml',
			'text/n3',
			'text/plain',
			'text/turtle'
		]
		for content_type in content_types:
			logger.debug("testing parsing of Content-Type: %s" % content_type)
			foo = repo.get_resource('%s/foo' % testing_container_uri, response_format=content_type)
			# test that graph was parsed correctly
			assert type(foo.rdf.graph) == rdflib.graph.Graph


	# create child container foo/bar (basic container)
	def test_create_child_bc(self):

		bar = BasicContainer(repo, '%s/foo/bar' % testing_container_uri)
		bar.create(specify_uri=True)
		assert bar.exists


	# get foo/bar
	def test_get_child_bc(self):

		bar = repo.get_resource('%s/foo/bar' % testing_container_uri)
		assert bar.exists


	# create foo/baz (NonRDF / binary), from foo
	def test_create_child_binary(self):

		baz = Binary(repo, '%s/foo/baz' % testing_container_uri)
		baz.binary.data = 'this is a test, this is only a test'
		baz.binary.mimetype = 'text/plain'
		baz.create(specify_uri=True)
		assert baz.exists


	# get foo/baz
	def test_get_child_binary(self):

		baz = repo.get_resource('%s/foo/baz' % testing_container_uri)
		assert baz.exists


	# create BasicContainer with NonRDFSource attributes, expect exception
	def create_resource_type_mismatch(self):
		
		'''
		When creating a resource, the resource runs .refresh(), which returns the
		resource type that the repo purports it is.  If this does not match the original
		resource type of the object that was used to create (e.g. instantiate BasicContainer,
		but repo comes back and says resource is NonRDFSource), this needs to raise an exception.
		'''

		goober = BasicContainer(repo, '%s/foo/goober' % testing_container_uri)
		goober.data = 'this is a test, this is only a test'
		goober.headers['Content-Type'] = 'text/plain'
		goober.create(specify_uri=True)



class TestURIParsing(object):

	'''
	assume 'foo' exists for all
	'''

	def test_full_uri_string(self):
		foo = repo.get_resource('http://localhost:8080/rest/%s/foo' % testing_container_uri)
		assert foo.exists


	def test_short_uri_string(self):
		foo = repo.get_resource('%s/foo' % testing_container_uri)
		assert foo.exists


	def test_URIRef_uri(self):
		foo = repo.get_resource(rdflib.term.URIRef('http://localhost:8080/rest/%s/foo' % testing_container_uri))
		assert foo.exists



class TestBinaryUpload(object):


	# upload file-like object
	def test_file_like_object(self):
		
		baz1 = Binary(repo, '%s/foo/baz1' % testing_container_uri)
		baz1.binary.data = open('README.md','rb')
		baz1.binary.mimetype = 'text/plain'
		baz1.create(specify_uri=True)
		assert baz1.exists


	# upload via Content-Location header
	def test_remote_location(self):

		baz2 = Binary(repo, '%s/foo/baz2' % testing_container_uri)
		baz2.binary.location = 'http://digital.library.wayne.edu/loris/fedora:wayne:vmc77220%7Cvmc77220_JP2/full/full/0/default.jpg'
		baz2.binary.mimetype = 'image/jpeg'
		baz2.create(specify_uri=True)
		assert baz2.exists



class TestBasicRelationship(object):

	# get children of foo
	def test_get_bc_children(self):

		'''
		gets all children of foo,
		confirms in the classpath of each child exists Resource class
		'''

		foo = repo.get_resource('%s/foo' % testing_container_uri)
		for child in foo.children(as_resources=True):
			assert Resource in inspect.getmro(child.__class__)

	# get children of foo
	def test_get_bc_parents(self):

		'''
		gets parents of bar, expecting foo
		confirms in the classpath of each child exists Resource class
		'''

		bar = repo.get_resource('%s/foo/bar' % testing_container_uri)
		for parent in bar.parents(as_resources=True):
			assert Resource in inspect.getmro(parent.__class__)

	# add triples
	def test_add_triples(self):

		'''
		adds multiple dc:subject triples for foo
		'''

		# get foo
		foo = repo.get_resource('%s/foo' % testing_container_uri)

		# rdflib.term.Literal
		foo.add_triple(foo.rdf.prefixes.dc.subject, rdflib.term.Literal('windy night'))

		# raw string
		foo.add_triple(foo.rdf.prefixes.dc.subject, 'stormy seas')

		# update foo
		foo.update()

		# confirm triples were added
		for val in ['windy night','stormy seas']:
			assert (foo.uri, foo.rdf.prefixes.dc.subject, rdflib.term.Literal(val, datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#string'))) in foo.rdf.graph


	# set triple
	def test_set_triple(self):

		'''
		adds dc:title triple, then sets new one, asserts new one
		'''

		# get foo
		foo = repo.get_resource('%s/foo' % testing_container_uri)

		# add title
		foo.add_triple(foo.rdf.prefixes.dc.title, 'great american novel')
		foo.update()

		# set (modify) title
		foo.set_triple(foo.rdf.prefixes.dc.title, 'one hit wonder')
		foo.update()

		# assert "one hit wonder"
		assert (foo.uri, foo.rdf.prefixes.dc.title, rdflib.term.Literal('one hit wonder', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#string'))) in foo.rdf.graph


	# remove triple
	def test_remove_triple(self):

		'''
		removes "stormy seas" subject
		'''

		# get foo
		foo = repo.get_resource('%s/foo' % testing_container_uri)

		# remove triple
		foo.remove_triple(foo.rdf.prefixes.dc.subject, 'stormy seas')
		foo.update()

		assert not (foo.uri, foo.rdf.prefixes.dc.subject, rdflib.term.Literal('stormy seas')) in foo.rdf.graph


	# RDF types
	def test_rdf_types(self):

		# string
		foo = repo.get_resource('%s/foo' % testing_container_uri)
		foo.add_triple(foo.rdf.prefixes.test.string_typing, 'string here, move along')
		assert next(foo.rdf.graph.objects(None, foo.rdf.prefixes.test.string_typing)).datatype == rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#string')

		# int
		foo.add_triple(foo.rdf.prefixes.test.integer_typing, 42)
		assert next(foo.rdf.graph.objects(None, foo.rdf.prefixes.test.integer_typing)).datatype == rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#int')

		# date
		foo.add_triple(foo.rdf.prefixes.test.date_typing, datetime.datetime.now())
		assert next(foo.rdf.graph.objects(None, foo.rdf.prefixes.test.date_typing)).datatype == rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#date')



class TestBasicCRUDPOST(object):

	# create, get, and delete POSTed resource
	def test_bc_crud(self):

		# test create
		bc = BasicContainer(repo, '%s' % testing_container_uri)
		bc.create()
		bc_uri = bc.uri
		assert bc.exists

		# test get
		bc = repo.get_resource(bc_uri)
		assert bc.exists

		# test delete
		bc.delete()
		bc = repo.get_resource(bc_uri)
		assert bc == False







########################################################
# TEARDOWN
########################################################
class TestTeardown(object):

	def test_teardown_testing_container(self):

		tc = repo.get_resource(testing_container_uri)
		tc.delete()
		tc = repo.get_resource(testing_container_uri)
		assert tc == False

