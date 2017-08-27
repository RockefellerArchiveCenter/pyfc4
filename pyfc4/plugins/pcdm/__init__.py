# pyfc4 plugin: pcdm

# import base models
from pyfc4 import models as _models

# import models
from pyfc4.plugins.pcdm import models


# convenience function for creating example structure
def create_pcdm_demo_resources(repo):

	# create root objcts /collections and /objects
	collections = _models.BasicContainer(repo, 'collections')
	collections.create(specify_uri=True)
	objects = _models.BasicContainer(repo, 'objects')
	objects.create(specify_uri=True)

	# create sample colors collection
	colors = models.PCDMCollection(repo, 'colors')
	colors.create(specify_uri=True)

	# create sample objects
	red = colors.create_child_object('red', specify_uri=True)
	green = colors.create_child_object('green', specify_uri=True)
	blue = colors.create_child_object('blue', specify_uri=True)

	# create child to green
	lime = green.create_child_object('lime', specify_uri=True)

	# create poem for lime green
	poem = lime.create_file('poem', specify_uri=True, data='you\'ve always been\ngood to me lime green', mimetype='text/plain')

	# create collectoin without uri
	generic_collection = models.PCDMCollection(repo)
	generic_collection.create()

	# create generic children
	generic_child1 = generic_collection.create_child_object()
	generic_child2 = generic_collection.create_child_object()
	generic_child3 = generic_collection.create_child_object()

	# create generic child to child1
	generic_childA = generic_child1.create_child_object()

	# create file for generic_childA
	generic_file = generic_childA.create_file(data='We\'re in Delaware.', mimetype='text/plain')


def delete_pcdm_demo_resources(repo):

	'''
	Convenience function to delete example hierarchy of PCDM resources.

	Args:
		repo (pyfc4.models.Repository): expects a repository instance
	'''

	collections = repo.get_resource('collections')
	collections.delete()

	objects = repo.get_resource('objects')
	objects.delete()