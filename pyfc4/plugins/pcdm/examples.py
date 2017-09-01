# pyfc4 plugin: pcdm

# import base pyfc4 models
from pyfc4 import models as _models

# import pcdm models
from pyfc4.plugins import pcdm


# function to create handful of PCDM related objects
def create_pcdm_demo_resources(repo):

	# create colors collection
	colors = pcdm.models.PCDMCollection(repo, 'colors')
	colors.create(specify_uri=True)

	# create color objects
	green = pcdm.models.PCDMObject(repo, 'green')
	green.create(specify_uri=True)
	yellow = pcdm.models.PCDMObject(repo, 'yellow')
	yellow.create(specify_uri=True)

	


# function to delete /collections and /objects
def delete_pcdm_demo_resources(repo):

	pass