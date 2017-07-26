
from pyfc4.models import *

import rdflib

# logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import pytest

# instantiate repository
repo = Repository('http://localhost:8080/rest','ghukill','password', context={'foo':'http://foo.com'})


########################################################
# SETUP
########################################################
@pytest.fixture()
def before():
	print('removing test objects pre-tests')
	for uri in ['foo','foo/bar','foo/baz']:
		try:
			resource = repo.get_resource(uri)
			resource.delete(remove_tombstone=True)
		except:
			print('could not delete %s' % uri)


########################################################
# TESTS
########################################################
# create foo (basic container)
@pytest.mark.usefixtures("before")
def test_create_bc():
	foo = BasicContainer(repo, 'foo')
	foo.create()
	assert foo.exists

# get foo via repo.get_resource()
def test_get_bc():
	foo = repo.get_resource('foo')
	assert foo.exists


# test RDF parsing of different Content-Types
def test_graph_parse():
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
		foo = repo.get_resource('foo', response_format=content_type)
		# test that graph was parsed correctly
		assert type(foo.graph) == rdflib.graph.Graph


# create foo/bar (basic container)
def test_create_child_bc():
	bar = BasicContainer(repo, 'foo/bar')
	bar.create()
	assert bar.exists


# get foo/bar from foo.children()
def test_get_child_bc():
	bar = repo.get_resource('foo/bar')
	assert bar.exists


# create foo/baz (NonRDF / binary), from foo
def test_create_child_binary():
	baz = Binary(repo, 'foo/baz')
	baz.data = 'this is a test, this is only a test'
	baz.headers['Content-Type'] = 'text/plain'
	baz.create()
	assert baz.exists


# get foo/baz
def test_get_child_binary():
	baz = repo.get_resource('foo/baz')
	assert baz.exists


