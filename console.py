# console

from pyfc4.models import *

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug('''
#######################################################################
pyfc4 convenience console.  All our triples are belong to you.
#######################################################################\
''')

# instantiate repository
repo = Repository('http://localhost:8080/rest','username','password', context={'foo':'http://foo.com/ontology/','bar':'http://bar.org#'})

'''
The following functions are created entirely for convenience/testing purposes.
'''

# demo resources
def create_demo_resources():

	# foo
	global foo
	foo = BasicContainer(repo, 'foo')
	foo.create(specify_uri=True)

	# goober
	global goober
	goober = BasicContainer(repo, 'goober')
	goober.create(specify_uri=True)

	# bar
	global bar
	bar = BasicContainer(repo, 'foo/bar')
	bar.create(specify_uri=True)

	# baz
	global baz
	baz = Binary(repo, 'foo/baz')
	baz.binary.data = open('README.md','rb')
	baz.binary.mimetype = 'text/plain'
	baz.create(specify_uri=True)

	return (foo,goober,bar,baz)


def get_demo_resources():
	global foo
	foo = repo.get_resource('foo')
	global goober
	goober = repo.get_resource('goober')
	global bar
	bar = repo.get_resource('foo/bar')
	global baz
	baz = repo.get_resource('foo/baz')


def delete_demo_resources():

	foo = repo.get_resource('foo')
	foo.delete()
	goober = repo.get_resource('goober')
	goober.delete()
