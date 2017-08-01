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

	# tronic (DirectContainer) --> foaf:knows --> goober, and tronic2 child of tronic
	global tronic
	tronic = DirectContainer(repo, 'tronic', membershipResource=goober.uri, hasMemberRelation=goober.rdf.prefixes.foaf.knows)
	tronic.create(specify_uri=True)
	global tronic2
	tronic2 = BasicContainer(repo, 'tronic/tronic2')
	tronic2.create(specify_uri=True)

	# ding (IndirectContainer)
	global ding
	ding = IndirectContainer(repo,'ding', membershipResource=goober.uri, hasMemberRelation=goober.rdf.prefixes.foaf.based_near, insertedContentRelation=goober.rdf.prefixes.foaf.based_near)
	ding.create(specify_uri=True)
	global dong
	dong = BasicContainer(repo,'ding/dong')
	dong.add_triple(dong.rdf.prefixes.foaf.based_near, foo.uri)
	dong.create(specify_uri=True)

	# refresh goober
	goober.refresh()

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


def delete_demo_resources():

	for resource in ['foo','goober','tronic', 'ding']:
		try:
			r = repo.get_resource(resource)
			r.delete()
		except:
			logger.debug('could not delete %s' % resource)

