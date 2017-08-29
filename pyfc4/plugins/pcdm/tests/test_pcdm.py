# pyfc4 - tests

# import pyfc4 models
from pyfc4.models import *

# import pcdm plugin
from pyfc4.plugins import pcdm

from tests import localsettings

import pytest

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# target location for testing container
testing_container_uri = 'pcdm_testing'

# instantiate repository handles
repo = Repository(
	localsettings.REPO_ROOT,
	localsettings.REPO_USERNAME,
	localsettings.REPO_PASSWORD,
	context={'foo':'http://foo.com'})


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
class TestCRUD(object):

	def test_create_pcdm_root_containers(self):
		# overwrite pcdm defaults
		pcdm.models.objects_path = '%s/objects' % testing_container_uri
		pcdm.models.collections_path = '%s/collections' % testing_container_uri

		# create containers for collections and objects
		collections = BasicContainer(repo, "%s" % (pcdm.models.collections_path))
		collections.create(specify_uri=True)
		assert collections.exists
		objects = BasicContainer(repo, "%s" % (pcdm.models.objects_path))
		objects.create(specify_uri=True)
		assert objects.exists


	def test_create_and_retrieve_collection(self):

		# create sample colors collection
		colors = pcdm.models.PCDMCollection(repo, 'colors')
		colors.create(specify_uri=True)
		assert colors.exists

		# retrieve collection
		colors = repo.get_resource('%s/collections/colors' % testing_container_uri, resource_type=pcdm.models.PCDMCollection)
		assert type(colors) == pcdm.models.PCDMCollection

		# make global
		global colors


	def test_create_and_retrieve_objects(self):

		# create sample objects
		red = colors.create_member_object('red', specify_uri=True)
		global red
		green = colors.create_member_object('green', specify_uri=True)
		global green
		blue = colors.create_member_object('blue', specify_uri=True)
		global blue

		# assert child object exists
		assert green.exists

		# retrieve and assert type
		green = repo.get_resource('%s/objects/green' % testing_container_uri, resource_type=pcdm.models.PCDMObject)
		assert type(green) == pcdm.models.PCDMObject





	# # create children to green
	# lime = green.create_member_object('lime', specify_uri=True)
	# chartreuse = green.create_member_object('chartreuse', specify_uri=True)

	# # create poem for lime green
	# poem = lime.create_file('poem', specify_uri=True, data='you\'ve always been\ngood to me lime green', mimetype='text/plain')

	# # create related proxy object for lime
	# lime.create_related_proxy_object(chartreuse.uri,'chartreuse',specify_uri=True)

	# # create associated spectrum file for lime
	# lime.create_associated_file('spectrum',data='570nm',mimetype='text/plain',specify_uri=True)

	# # create collectoin without uri
	# generic_collection = models.PCDMCollection(repo)
	# generic_collection.create()

	# # create generic children
	# generic_child1 = generic_collection.create_member_object()
	# generic_child2 = generic_collection.create_member_object()
	# generic_child3 = generic_collection.create_member_object()

	# # create generic child to child1
	# generic_childA = generic_child1.create_member_object()

	# # create file for generic_childA
	# generic_file = generic_childA.create_file(data='We\'re in Delaware.', mimetype='text/plain')





########################################################
# TEARDOWN
########################################################
class TestTeardown(object):

	def test_teardown_testing_container(self):

		tc = repo.get_resource(testing_container_uri)
		tc.delete()
		tc = repo.get_resource(testing_container_uri)
		assert tc == False