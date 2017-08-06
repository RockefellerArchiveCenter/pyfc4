# console

from pyfc4.models import *

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug('''
#######################################################################
pyfc4 debug/convenience console.  All our triples are belong to you.
#######################################################################\
''')

# instantiate repository
repo = Repository('http://localhost:8080/fcrepo/rest','fedoraAdmin','secret3', context={'foo':'http://foo.com/ontology/','bar':'http://bar.org#'})

'''
The following functions are created entirely for convenience/testing purposes.
'''

# fast get
def get(uri):
	return repo.get_resource(uri)
	

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



################################################
# Benchmarking
################################################

def bench_create_basic_container(number, resource_type):

	# expects number to create, and actual class 

	logger.debug("creating %s BasicContainers with pyfc4 and raw API" % number)
	report = {}
	
	# test within a transaction
	txn = repo.start_txn('txn')


	#########################################
	# use pyfc4, refreshing resource
	#########################################
	logger.debug('using pyfc4...')
	# start timer
	stime = time.time()
	for x in range(0, number):

		# create resource with minted uri
		r = BasicContainer(txn)
		'''
		it must be slower, as it parses refreshed RDF
		but how much slower?
		'''
		r.create()
	report['pyfc4_refresh'] = time.time()-stime


	#########################################
	# use pyfc4, no refresh
	#########################################
	logger.debug('using pyfc4...')
	# start timer
	stime = time.time()
	for x in range(0, number):

		# create resource with minted uri
		r = BasicContainer(txn)
		'''
		it must be slower, as it parses refreshed RDF
		but how much slower?
		'''
		r.create(auto_refresh=False)
	report['pyfc4_no_refresh'] = time.time()-stime


	#########################################
	# raw API
	#########################################
	logger.debug('using raw API...')
	# start timer
	stime = time.time()
	# send POST and create resource
	for x in range(0, number):
		r = requests.post(txn.root, data=None, headers=None)

	report['raw'] = time.time()-stime


	#########################################
	# report
	#########################################
	# rollback transaction
	txn.rollback()
	# report
	logger.debug(report)



def bench_refresh_triples(number):

	# expects number of triples to modify
	report = {}
	
	# test within a transaction
	txn = repo.start_txn('txn')

	#########################################
	# do not update quick triples
	#########################################
	logger.debug('not updating self.rdf.triples')
	r = BasicContainer(txn)
	r.create()
	# start timer
	stime = time.time()
	for x in range(0, number):
		r.add_triple(r.rdf.prefixes.foaf.knows, x, auto_refresh=False)
	report['no_update'] = time.time()-stime


	#########################################
	# use pyfc4, no refresh
	#########################################
	logger.debug('not updating self.rdf.triples')
	r = BasicContainer(txn)
	r.create()
	# start timer
	stime = time.time()
	for x in range(0, number):
		r.add_triple(r.rdf.prefixes.foaf.knows, x)
	report['update'] = time.time()-stime


	#########################################
	# report
	#########################################
	# rollback transaction
	txn.rollback()
	# report
	logger.debug(report)
	return report



