# pyfc4 plugin: pcdm

# import base models
from pyfc4 import models as _models

# import models
from pyfc4.plugins.pcdm import models


# convenience function for creating example structure
def create_pcdm_demo_resources(repo):

	'''
	Convenience function to create example hierarchy of PCDM resources.

	Using Poe / Raven example from:
	https://wiki.duraspace.org/display/FEDORA4x/LDP-PCDM-F4+In+Action

	Args:
		repo (pyfc4.models.Repository): expects a repository instance
	'''

	# create container for all demo resources
	pcdmdemo = _models.BasicContainer(repo,'pcdmdemo')
	pcdmdemo.create(specify_uri=True)

	# create PCDM collection "poe"
	poe = models.PCDMCollection(repo,'pcdmdemo/collections/poe')
	poe.create(specify_uri=True)

	# create PCDM object "raven"
	raven = models.PCDMObject(repo,'pcdmdemo/objects/raven')
	raven.create(specify_uri=True)

	# create PCDM object for page 1
	page1 = models.PCDMObject(repo,'pcdmdemo/objects/raven/page1')
	page1.create(specify_uri=True)

	# create page text for page 1
	page1text = _models.Binary(repo, 'pcdmdemo/objects/raven/page1/files/text')
	page1text.binary.data = 'Once upon a midnight dreary, while I pondered, weak and weary,'
	page1text.binary.mimetype = 'text/plain'
	page1text.create(specify_uri=True)

	# create PCDM object for page 2
	page2 = models.PCDMObject(repo,'pcdmdemo/objects/raven/page2')
	page2.create(specify_uri=True)

	# create page text for page 2
	page2text = _models.Binary(repo, 'pcdmdemo/objects/raven/page2/files/text')
	page2text.binary.data = 'Over many a quaint and curious volume of forgotten lore'
	page2text.binary.mimetype = 'text/plain'
	page2text.create(specify_uri=True)

	# create page proxy object in raven


def delete_pcdm_demo_resources(repo):

	'''
	Convenience function to delete example hierarchy of PCDM resources.

	Args:
		repo (pyfc4.models.Repository): expects a repository instance
	'''

	pcdmdemo = repo.get_resource('pcdmdemo')
	pcdmdemo.delete()