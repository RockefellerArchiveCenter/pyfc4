# console

from pyfc4.models import *

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug('''
#######################################################################
pyfc4 convenience console.  All resources are belong to you.
#######################################################################\
''')

# instantiate repository
repo = Repository('http://localhost:8080/rest','username','password', context={'foo':'http://foo.com'})

# demo resources
def create_demo_resources():

	# foo
	foo = BasicContainer(repo, 'foo')
	foo.create(specify_uri=True)

	# bar
	bar = BasicContainer(repo, 'foo/bar')
	bar.create(specify_uri=True)

	# baz
	baz = BasicContainer(repo, 'foo/baz')
	baz.data = open('README.md','rb')
	baz.mimetype = 'text/plain'
	baz.create(specify_uri=True)


def load_dummy_resources():
	
	foo = repo.get_resource('foo')
	global foo

	bar = repo.get_resource('foo/bar')
	global bar

	baz = repo.get_resource('foo/baz')
	global baz


def delete_dummy_resources():

	foo = repo.get_resource('foo')
	foo.delete()