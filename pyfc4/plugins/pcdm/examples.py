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

	# add green and yellow to colors collection
	colors.members.extend([green.uri, yellow.uri])
	colors.update()

	# make green and yellow related
	green.related.append(yellow.uri)
	green.update()
	yellow.related.append(green.uri)
	yellow.update()

	# create spectrum binary as file for green
	spectrum_green = pcdm.models.PCDMFile(repo, 'green/files/spectrum_green', binary_data='540nm', binary_mimetype='text/plain')
	spectrum_green.create(specify_uri=True)

	# create loose spectrum binary, move to yellow
	spectrum_yellow = pcdm.models.PCDMFile(repo, 'spectrum_yellow', binary_data='570nm', binary_mimetype='text/plain')
	spectrum_yellow.create(specify_uri=True)
	spectrum_yellow.move(yellow.uri+'/files/spectrum_yellow')
	yellow.update()
	

# function to delete /collections and /objects
def delete_pcdm_demo_resources(repo):

	for uri in ['colors','green','yellow']:
		try:
			repo.get_resource(uri).delete(remove_tombstone=True)
		except:
			print('could not remove: %s' % uri)