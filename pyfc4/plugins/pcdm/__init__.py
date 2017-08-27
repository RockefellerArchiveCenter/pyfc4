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
	pcdmdemo.create(specify_uri=True, auto_refresh=False)

	# create generic collections
	collections = _models.BasicContainer(repo,'pcdmdemo/collections')
	collections.create(specify_uri=True, auto_refresh=False)

	# create generic collections
	objects = _models.BasicContainer(repo,'pcdmdemo/objects')
	objects.create(specify_uri=True, auto_refresh=False)

	# create PCDM collection "poe"
	poe = models.PCDMCollection(repo,'pcdmdemo/collections/poe')
	poe.create(specify_uri=True, auto_refresh=False)

	# create PCDM object "raven"
	raven = models.PCDMObject(repo,'pcdmdemo/objects/raven')
	raven.create(specify_uri=True, auto_refresh=False)

	# create proxy object at /collections/poe/members that points to /objects/raven
	ravenproxy = models.PCDMObject(repo, 'pcdmdemo/collections/poe/members/ravenproxy')
	ravenproxy.create(specify_uri=True, auto_refresh=True)
	ravenproxy.add_triple(ravenproxy.rdf.prefixes.rdf.type, ravenproxy.rdf.prefixes.ore.Proxy)
	ravenproxy.add_triple(ravenproxy.rdf.prefixes.ore.proxyFor, raven.uri)
	ravenproxy.update()

	# create PCDM object for page 1
	ravenpage1 = models.PCDMObject(repo,'pcdmdemo/objects/ravenpage1')
	ravenpage1.create(specify_uri=True, auto_refresh=False)

	# create page text for page 1
	ravenpage1text = _models.Binary(repo, 'pcdmdemo/objects/ravenpage1/files/text')
	ravenpage1text.binary.data = 'Once upon a midnight dreary, while I pondered, weak and weary,'
	ravenpage1text.binary.mimetype = 'text/plain'
	ravenpage1text.create(specify_uri=True, auto_refresh=False)

	# create proxy object at /raven/members that points to /objects/ravenpage1
	ravenpage1proxy = models.PCDMObject(repo, 'pcdmdemo/objects/raven/members/ravenpage1proxy')
	ravenpage1proxy.create(specify_uri=True, auto_refresh=True)
	ravenpage1proxy.add_triple(ravenpage1proxy.rdf.prefixes.rdf.type, ravenpage1proxy.rdf.prefixes.ore.Proxy)
	ravenpage1proxy.add_triple(ravenpage1proxy.rdf.prefixes.ore.proxyFor, ravenpage1.uri)
	ravenpage1proxy.add_triple(ravenpage1proxy.rdf.prefixes.ore.proxyIn, raven.uri)
	ravenpage1proxy.update()
	

	# create PCDM object for page 2
	ravenpage2 = models.PCDMObject(repo,'pcdmdemo/objects/ravenpage2')
	ravenpage2.create(specify_uri=True, auto_refresh=False)

	# create page text for page 2
	ravenpage2text = _models.Binary(repo, 'pcdmdemo/objects/ravenpage2/files/text')
	ravenpage2text.binary.data = 'Over many a quaint and curious volume of forgotten lore'
	ravenpage2text.binary.mimetype = 'text/plain'
	ravenpage2text.create(specify_uri=True, auto_refresh=False)

	# create proxy object at /raven/members that points to /objects/ravenpage1
	ravenpage2proxy = models.PCDMObject(repo, 'pcdmdemo/objects/raven/members/ravenpage2proxy')
	ravenpage2proxy.create(specify_uri=True, auto_refresh=True)
	ravenpage2proxy.add_triple(ravenpage2proxy.rdf.prefixes.rdf.type, ravenpage2proxy.rdf.prefixes.ore.Proxy)
	ravenpage2proxy.add_triple(ravenpage2proxy.rdf.prefixes.ore.proxyFor, ravenpage2.uri)
	ravenpage2proxy.add_triple(ravenpage2proxy.rdf.prefixes.ore.proxyIn, raven.uri)
	ravenpage2proxy.update()



def delete_pcdm_demo_resources(repo):

	'''
	Convenience function to delete example hierarchy of PCDM resources.

	Args:
		repo (pyfc4.models.Repository): expects a repository instance
	'''

	pcdmdemo = repo.get_resource('pcdmdemo')
	pcdmdemo.delete()



# convenience function for creating example structure
def create_pcdm_demo_resources_convenience(repo):

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

	# create collectoin without uri
	generic_collection = models.PCDMCollection(repo)
	generic_collection.create()

	# create generic children
	generic_child1 = generic_collection.create_child_object()
	generic_child2 = generic_collection.create_child_object()
	generic_child3 = generic_collection.create_child_object()


def delete_pcdm_demo_resources_convenience(repo):

	'''
	Convenience function to delete example hierarchy of PCDM resources.

	Args:
		repo (pyfc4.models.Repository): expects a repository instance
	'''

	collections = repo.get_resource('collections')
	collections.delete()

	objects = repo.get_resource('objects')
	objects.delete()