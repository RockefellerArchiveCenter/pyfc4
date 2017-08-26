# pyfc4 - tests

from pyfc4.models import *

# import pcdm plugin
from pyfc4.plugins.pcdm.models import PCDMCollection, PCDMObject

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


	def test_create_pcdm_collection(self):

		# create resource
		pcdm_col = PCDMCollection(repo, '%s/pcdm_col' % testing_container_uri)
		pcdm_col.create(specify_uri=True)

		# assert exists
		assert pcdm_col.exists

		# assert PCDM Collection
		assert type(pcdm_col) == PCDMCollection

		# assert extending BasicContainer
		assert isinstance(pcdm_col, BasicContainer)


	def test_retrieve_pcdm_collection(self):

		# retrieve resource
		pcdm_col = repo.get_resource('%s/pcdm_col' % testing_container_uri, resource_type=PCDMCollection)

		# assert PCDM Collection
		assert type(pcdm_col) == PCDMCollection


	def test_create_pcdm_object(self):

		# create resource
		pcdm_obj = PCDMObject(repo, '%s/pcdm_obj' % testing_container_uri)
		pcdm_obj.create(specify_uri=True)

		# assert exists
		assert pcdm_obj.exists

		# assert PCDM Object
		assert type(pcdm_obj) == PCDMObject

		# assert extending BasicContainer
		assert isinstance(pcdm_obj, BasicContainer)


	def test_retrieve_pcdm_object(self):

		# retrieve resource
		pcdm_obj = repo.get_resource('%s/pcdm_obj' % testing_container_uri, resource_type=PCDMObject)

		# assert PCDM Collection
		assert type(pcdm_obj) == PCDMObject



########################################################
# TEARDOWN
########################################################
class TestTeardown(object):

	def test_teardown_testing_container(self):

		tc = repo.get_resource(testing_container_uri)
		tc.delete()
		tc = repo.get_resource(testing_container_uri)
		assert tc == False