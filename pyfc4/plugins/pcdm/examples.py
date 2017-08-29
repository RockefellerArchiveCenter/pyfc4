# pyfc4 plugin: pcdm

# import base pyfc4 models
from pyfc4 import models as _models

# import pcdm models
from pyfc4.plugins.pcdm import models


# function to create handful of PCDM related objects
def create_pcdm_demo_resources(repo):

	'''
	Convenience function to create example hierarchy of PCDM resources.

	Args:
		repo (pyfc4.models.Repository): expects a repository instance
	'''

	# create root objcts /collections and /objects
	collections = _models.BasicContainer(repo, models.collections_path)
	collections.create(specify_uri=True)
	objects = _models.BasicContainer(repo, models.objects_path)
	objects.create(specify_uri=True)

	# create sample colors collection
	colors = models.PCDMCollection(repo, 'colors')
	colors.create(specify_uri=True)

	# create sample objects
	red = colors.create_member_object('red', specify_uri=True)
	green = colors.create_member_object('green', specify_uri=True)
	blue = colors.create_member_object('blue', specify_uri=True)

	# create children to green
	lime = green.create_member_object('lime', specify_uri=True)
	chartreuse = green.create_member_object('chartreuse', specify_uri=True)

	# create poem for lime green
	poem = lime.create_file('poem', specify_uri=True, data='you\'ve always been\ngood to me lime green', mimetype='text/plain')

	# create related proxy object for lime
	lime.create_related_proxy_object(chartreuse.uri,'chartreuse',specify_uri=True)

	# create associated spectrum file for lime
	lime.create_associated_file('spectrum',data='570nm',mimetype='text/plain',specify_uri=True)

	# create collectoin without uri
	generic_collection = models.PCDMCollection(repo)
	generic_collection.create()

	# create generic children
	generic_child1 = generic_collection.create_member_object()
	generic_child2 = generic_collection.create_member_object()
	generic_child3 = generic_collection.create_member_object()

	# create generic child to child1
	generic_childA = generic_child1.create_member_object()

	# create file for generic_childA
	generic_file = generic_childA.create_file(data='We\'re in Delaware.', mimetype='text/plain')


# function to delete /collections and /objects
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