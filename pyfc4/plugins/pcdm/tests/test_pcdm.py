# pyfc4 - tests

# import pyfc4 models
from pyfc4.models import *

# import pcdm plugin
from pyfc4.plugins import pcdm

from tests import localsettings

import pytest
import time

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# target location for testing container
testing_container_uri = 'pcdm_testing'

# instantiate repository handles with custom PCDM resource type parser
repo = Repository(
	localsettings.REPO_ROOT,
	localsettings.REPO_USERNAME,
	localsettings.REPO_PASSWORD,
	context={'foo':'http://foo.com'},
	default_serialization='text/turtle',
	custom_resource_type_parser=pcdm.custom_resource_type_parser)


########################################################
# SETUP
########################################################
class TestSetup(object):

	def test_create_testing_container(self):

		# attempt delete
		try:
			tc = repo.get_resource(testing_container_uri)
			tc.delete()
		except:
			logger.debug('could not find or delete testing container')

		# create testing container
		tc = BasicContainer(repo, testing_container_uri)
		tc.create(specify_uri=True)
		assert tc.exists


########################################################
# TESTS
########################################################
class TestCRUD(object):


	def test_create_and_retrieve_collection(self):

		# create sample colors collection
		global colors
		colors = pcdm.models.PCDMCollection(repo, '%s/colors' % testing_container_uri)
		colors.create(specify_uri=True)
		assert colors.exists

		# retrieve collection
		colors = repo.get_resource('%s/colors' % testing_container_uri)
		assert type(colors) == pcdm.models.PCDMCollection


	def test_create_and_retrieve_objects(self):

		# create color objects
		global green
		green = pcdm.models.PCDMObject(repo, '%s/green' % testing_container_uri)
		green.create(specify_uri=True)
		green = repo.get_resource('%s/green' % testing_container_uri)
		assert type(green) == pcdm.models.PCDMObject

		global yellow
		yellow = pcdm.models.PCDMObject(repo, '%s/yellow' % testing_container_uri)
		yellow.create(specify_uri=True)
		yellow = repo.get_resource('%s/yellow' % testing_container_uri)
		assert type(yellow) == pcdm.models.PCDMObject	


	def test_add_objects_to_collection(self):

		# add green and yellow to colors collection
		colors.members.extend([green.uri, yellow.uri])
		colors.update()

		# refresh colors and confirm as members
		colors.refresh()
		assert green.uri in colors.members
		assert yellow.uri in colors.members


	def test_relate_objects(self):

		# make green and yellow related
		green.related.append(yellow.uri)
		green.update()
		green.refresh()
		yellow.related.append(green.uri)
		yellow.update()
		yellow.refresh()

		# confirm relations
		assert green.uri in yellow.related
		assert yellow.uri in green.related


	def test_create_file_plaintext(self):

		# create spectrum binary as file for green in /files
		spectrum = pcdm.models.PCDMFile(repo, '%s/green/files/spectrum' % testing_container_uri, binary_data='540nm', binary_mimetype='text/plain')
		spectrum.create(specify_uri=True)
		assert spectrum.exists

		# retrieve
		spectrum = repo.get_resource(spectrum.uri)
		assert type(spectrum) == pcdm.models.PCDMFile

		# assert in green's files
		green = repo.get_resource('%s/green' % testing_container_uri)
		assert spectrum.uri in green.files


	def test_create_file_fileobject(self):

		# open README.md as file object
		with open('pyfc4/plugins/pcdm/README.md','rb') as f:

			# create readme binary as file for green in /files
			readme = pcdm.models.PCDMFile(repo, '%s/green/files/readme' % testing_container_uri, binary_data=f, binary_mimetype='text/plain')
			readme.create(specify_uri=True)
			assert readme.exists

		# retrieve
		readme = repo.get_resource(readme.uri)
		assert type(readme) == pcdm.models.PCDMFile

		# assert in green's files
		green = repo.get_resource('%s/green' % testing_container_uri)
		assert readme.uri in green.files


	def test_create_file_fileobject_loop(self):

		for x in range(10):

			# open README.md as file object
			with open('pyfc4/plugins/pcdm/README.md','rb') as f:

				# create readme binary as file for green in /files
				readme = pcdm.models.PCDMFile(repo, '%s/green/files/readme_%s' % (testing_container_uri,x), binary_data=f, binary_mimetype='text/plain')
				readme.create(specify_uri=True)
				assert readme.exists

			# retrieve
			readme = repo.get_resource(readme.uri)
			assert type(readme) == pcdm.models.PCDMFile

			# assert in green's files
			green = repo.get_resource('%s/green' % testing_container_uri)
			assert readme.uri in green.files


	def test_create_associated_file(self):

		# create associated file
		fits = pcdm.models.PCDMFile(repo, '%s/green/associated/fits' % testing_container_uri, binary_data='some fits data', binary_mimetype='text/plain')
		fits.create(specify_uri=True)
		assert fits.exists

		# retrieve
		fits = repo.get_resource(fits.uri)
		assert type(fits) == pcdm.models.PCDMFile

		# assert in green's files
		green = repo.get_resource('%s/green' % testing_container_uri)
		assert fits.uri in green.associated




########################################################
# TEARDOWN
########################################################
# class TestTeardown(object):

# 	def test_teardown_testing_container(self):

# 		tc = repo.get_resource(testing_container_uri)
# 		tc.delete()
# 		tc = repo.get_resource(testing_container_uri)
# 		assert tc == False