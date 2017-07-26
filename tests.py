# console / testing

from pyfc4.models import *

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# instantiate repository
repo = Repository('http://localhost:8080/rest','ghukill','password', context={'foo':'http://foo.com'})

# create foo (basic container)
def create_bc():
	foo = BasicContainer(repo, 'foo')
	foo.create()
	return foo.exists()

# get foo via repo.get_resource()
def get_bc():
	foo = repo.get_resource('foo')
	return foo.exists()

# test RDF parsing of different Content-Types
def test_graph_parse():
	content_types = [
		'application/ld+json',
		'application/n-triples',
		'application/rdf+xml',
		'text/n3',
		'text/plain',
		'text/turtle'
	]
	for content_type in content_types:
		print("testing parsing of Content-Type: %s" % content_type)
		foo = repo.get_resource('foo', response_format=content_type)
	return True

# create foo/bar (basic container)
def create_child_bc():
	bar = BasicContainer(repo, 'foo/bar')
	bar.create()
	return bar.exists()

# get foo/bar from foo.children()
def get_child_bc():
	bar = repo.get_resource('foo/bar')
	return bar.exists()

# create foo/baz (NonRDF / binary), from foo
def create_child_binary():
	baz = Binary(repo, 'foo/baz')
	baz.data = 'this is a test, this is only a test'
	baz.headers['Content-Type'] = 'text/plain'
	baz.create()
	return baz.exists()

# get foo/baz
def get_child_binary():
	baz = repo.get_resource('foo/baz')
	return baz.exists()

# delete all three
def delete_test_resources():
	for uri in ['foo','foo/bar','foo/baz']:
		try:
			resource = repo.get_resource(uri)
			resource.delete(remove_tombstone=True)
		except:
			logger.debug('could not delete %s' % uri)

# run all tests
def run_all_tests(cleanup=False):
	
	tests = [	
		create_bc(),
		get_bc(),
		test_graph_parse(),
		create_child_bc(),
		get_child_bc(),
		create_child_binary(),
		get_child_binary()
	]

	if cleanup:
		delete_test_resources()

	if False in tests:
		logger.debug('\n\nTESTS RESULT: not all tests passed\n\n')
	else:
		logger.debug('\n\nTESTS RESULT: all systems go!\n\n')


if __name__ == '__main__':
	run_all_tests(cleanup=True)