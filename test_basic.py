
from pyfc4.models import *

import inspect
import pytest
import rdflib

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

		tc = BasicContainer(repo, testing_container_uri)
		tc.create(specify_uri=True)
		assert tc.exists


########################################################
# TESTS
########################################################

class TestBasicCRUD(object):

	
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
			assert type(foo.graph) == rdflib.graph.Graph


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
		baz.data = 'this is a test, this is only a test'
		baz.headers['Content-Type'] = 'text/plain'
		baz.create(specify_uri=True)
		assert baz.exists


	# get foo/baz
	def test_get_child_binary(self):

		baz = repo.get_resource('%s/foo/baz' % testing_container_uri)
		assert baz.exists



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



########################################################
# TEARDOWN
########################################################
class TestTeardown(object):

	def test_teardown_testing_container(self):

		tc = repo.get_resource(testing_container_uri)
		tc.delete()
		tc = repo.get_resource(testing_container_uri)
		assert tc == False

