
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

	# test get root
	def test_get_root_and_helpers(self):

		# get root node
		root = repo.get_resource(None)
		assert root.exists

		# test __repr__
		assert root.__repr__() == '<BasicContainer Resource, uri: %s>' % repo.root

		# test uri_as_string
		assert root.uri_as_string() == repo.root


	# test bad uri
	def test_bad_uri(self):

		with pytest.raises(Exception) as excinfo:
			repo.get_resource('*%($')
		assert 'error retrieving resource' in str(excinfo.value)	

	
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


	# create child, retrieve, delete, confirm with check_exists()
	def test_resource_existence(self):

		# create temp child resource
		tronic = BasicContainer(repo, '%s/foo/tronic' % testing_container_uri)
		tronic.create(specify_uri=True)
		assert tronic.check_exists()

		# attempt to recreate
		tronic_clone = BasicContainer(repo, '%s/foo/tronic' % testing_container_uri)
		with pytest.raises(Exception) as excinfo:
			tronic.create(specify_uri=True)
		assert 'resource exists attribute True' in str(excinfo.value)

		# delete tronic
		tronic_removal = repo.get_resource('%s/foo/tronic' % testing_container_uri)
		tronic_removal.delete()
		assert not tronic_removal.exists

		# confirm check_exists() updates resource instance
		tronic.check_exists()
		assert not tronic.exists


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


	# test alternate response formats for resource get
	def test_alternate_formats(self):

		# RDF XML
		foo = repo.get_resource('%s/foo' % testing_container_uri, response_format="application/rdf+xml")
		assert foo.headers['Content-Type'] == 'application/rdf+xml'

		# Turtle
		foo = repo.get_resource('%s/foo' % testing_container_uri, response_format="text/turtle")
		assert foo.headers['Content-Type'] == 'text/turtle'

		# with raw API
		response = repo.api.http_request('GET', foo.uri, data=None, headers={'Accept':'text/turtle'})
		assert foo.headers['Content-Type'] == 'text/turtle'
		response = repo.api.http_request('GET', foo.uri, data=None, headers=None, response_format='text/turtle')
		assert foo.headers['Content-Type'] == 'text/turtle'



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


	# create POST confirmations
	def test_bc_post_exceptions(self):

		# test create
		bc = BasicContainer(repo, '%s' % testing_container_uri)
		bc.create()
		bc_uri = bc.uri
		assert bc.exists

		# create child resource
		bc1 = BasicContainer(repo, bc.uri)
		bc1.create()
		assert bc1.exists

		# 404 - create child at bad location
		bc2 = BasicContainer(repo, "%s/does/not/exist" % bc.uri)
		with pytest.raises(Exception) as excinfo:
			bc2.create()
		assert 'target location does not exist' in str(excinfo.value)

		# 409 - create resrouce where another exists
		bc3 = BasicContainer(repo, bc.uri)
		with pytest.raises(Exception) as excinfo:
			bc3.create(specify_uri=True)
		assert 'resource already exists' in str(excinfo.value)

		# 410 - tombstone
		bc4 = BasicContainer(repo, '%s' % testing_container_uri)
		bc4.create()
		bc4.delete(remove_tombstone=False)
		bc5 = BasicContainer(repo, bc4.uri)
		with pytest.raises(Exception) as excinfo:
			bc5.create(specify_uri=True)
		assert 'tombstone for %s detected' % bc4.uri in str(excinfo.value)

		# test delete
		bc.delete()
		bc = repo.get_resource(bc_uri)
		assert bc == False



# test creation and linkages of DirectContainers
class TestDirectContainer(object):

	def test_create_dc(self):

		# create target goober container
		goober = BasicContainer(repo, '%s/goober' % testing_container_uri)
		goober.create(specify_uri=True)
		assert goober.exists

		# create DirectContainer that relates to goober
		tronic = DirectContainer(repo, '%s/tronic' % testing_container_uri, membershipResource=goober.uri, hasMemberRelation=goober.rdf.prefixes.foaf.knows)
		tronic.create(specify_uri=True)
		assert tronic.exists

		# create child to tronic, that goober should then relate to
		tronic2 = BasicContainer(repo, '%s/tronic/tronic2' % testing_container_uri)
		tronic2.create(specify_uri=True)
		assert tronic2.exists

		# finally, assert foaf:knows relation for goober --> tronic2 exists
		goober.refresh()
		assert next(goober.rdf.graph.objects(None, goober.rdf.prefixes.foaf.knows)) == tronic2.uri



# test creation and linkages of DirectContainers
class TestIndirectContainer(object):

	def test_create_ic(self):

		# retrieve goober
		goober = repo.get_resource('%s/goober' % testing_container_uri)

		# retrieve foo
		foo = repo.get_resource('%s/foo' % testing_container_uri)

		# create IndirectContainer that sets a foaf:based_near relationship from goober to foo
		ding = IndirectContainer(repo,'%s/ding' % testing_container_uri, membershipResource=goober.uri, hasMemberRelation=goober.rdf.prefixes.foaf.based_near, insertedContentRelation=goober.rdf.prefixes.foaf.based_near)
		ding.create(specify_uri=True)
		assert ding.exists

		# create child resource to ding
		dong = BasicContainer(repo,'%s/ding/dong' % testing_container_uri)
		# add triple that triggers dong's IndirectContainer relationship
		dong.add_triple(dong.rdf.prefixes.foaf.based_near, foo.uri)
		dong.create(specify_uri=True)
		assert dong.exists

		# finally, assert triple from goober --> foaf:based_near --> foo
		goober.refresh()
		assert next(goober.rdf.graph.objects(None, goober.rdf.prefixes.foaf.based_near)) == foo.uri



# test basic transactions
class TestTransactions(object):

	def test_transactions_CRUD(self):

		# start new transaction, 'zing'
		zing = repo.start_txn('zing')
		assert zing.active

		# retrieve this transaction as another name
		zinger = repo.get_txn('zinger', zing.root)
		assert zinger.active

		# create bc in zing
		zingfoo = BasicContainer(zing, '%s/zingfoo' % testing_container_uri)
		zingfoo.create(specify_uri=True)
		assert zingfoo.exists

		# commit zing and test for commit of zingfoo
		zing.commit()
		assert not zing.active # not active any longer
		zingfoo = repo.get_resource('%s/zingfoo' % testing_container_uri)
		assert zingfoo.exists

		# begin new, unnamed txn
		txn = repo.start_txn()
		assert txn.active

		# create zingfoo2 in txn
		zingfoo2 = BasicContainer(txn, '%s/zingfoo2' % testing_container_uri)
		zingfoo2.create(specify_uri=True)
		assert zingfoo2.exists

		# but, rollback and confirm not committed
		txn.rollback()
		zingfoo2 = repo.get_resource('%s/zingfoo2' % testing_container_uri)
		assert not zingfoo2



# test moving/copying
class TestMovingCopying(object):

	def test_move_resource(self):

		# create new resource to move
		ephem = BasicContainer(repo, '%s/ephem' % testing_container_uri)
		ephem.create(specify_uri=True)
		assert ephem.exists

		# move resource, and capture as new resource
		ephem2 = repo.get_resource(ephem.move('%s/ephem2' % testing_container_uri))

		# test
		assert not ephem.exists
		assert ephem2.exists


	def test_copy_resource(self):

		# grab ephem2
		ephem2 = repo.get_resource('%s/ephem2' % testing_container_uri)

		# copy to ephem3
		ephem3 = repo.get_resource(ephem2.copy('%s/ephem3' % testing_container_uri))

		# test
		assert ephem2.exists
		assert ephem3.exists



# versioning
class TestVersions(object):

	def test_create_versions(self):

		# get foo
		foo = repo.get_resource('%s/foo' % testing_container_uri)

		# create version before modification
		v1 = foo.create_version('v1')
		assert type(foo.versions.v1) == ResourceVersion
		v2 = foo.create_version('v2')
		assert type(foo.versions.v2) == ResourceVersion


	def test_retrieve_versions(self):

		# get foo
		foo = repo.get_resource('%s/foo' % testing_container_uri)

		# retrieve versions
		foo.get_versions()
		assert type(foo.versions.v1) == ResourceVersion
		assert type(foo.versions.v2) == ResourceVersion


	def test_delete_version(self):

		# get foo and versions
		foo = repo.get_resource('%s/foo' % testing_container_uri)
		foo.get_versions()

		# assert cannot delete v2, as most recent
		with pytest.raises(Exception) as excinfo:
			foo.versions.v2.delete()
		assert 'code 400' in str(excinfo.value)

		# but delete v1
		foo.versions.v1.delete()
		assert not hasattr(foo.versions, 'v1')


	def test_revert_to_version(self):

		# get foo
		foo = repo.get_resource('%s/foo' % testing_container_uri)

		# add triple
		foo.add_triple(foo.rdf.prefixes.dc.coverage, 'forest')
		foo.update()
		assert foo.rdf.triples.dc.coverage[0] == rdflib.term.Literal('forest', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#string'))

		# get versions and revert to foo_v1 (pre triple)
		foo.get_versions()
		foo.versions.v2.revert_to()

		# assert new triple does not exist
		assert not hasattr(foo.rdf.triples.dc, 'coverage')


	def create_binary_version(self):

		# get baz
		baz = repo.get_resource('%s/foo/baz' % testing_container_uri)

		# create versions and confirm exists
		v1 = baz.create_version('v1')
		assert type(baz.versions.v1) == ResourceVersion	


########################################################
# TEARDOWN
########################################################
class TestTeardown(object):

	def test_teardown_testing_container(self):

		tc = repo.get_resource(testing_container_uri)
		tc.delete()
		tc = repo.get_resource(testing_container_uri)
		assert tc == False

