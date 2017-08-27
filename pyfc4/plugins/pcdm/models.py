# pyfc4 plugin: pcdm.models

# import pyfc4 base models
from pyfc4 import models as _models

# logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

'''
Implementation of PCDM in LDP:
https://docs.google.com/document/d/1RI8aX8XQEk-30-Ht-DaPF5nz_VtI1-eqxUuDvF3nhv0/edit#
'''


# configurations to be handled later (no trailing slash)
pcdm_objects_path = 'objects'
pcdm_collections_path = 'collections'


class PCDMCollection(_models.BasicContainer):

	'''
	Class to represent PCDM Collections in LDP.

	----------------------------------------------------------------------------------
	URI Template	--	Resource Identified
	----------------------------------------------------------------------------------
	/collections/{id}	--	A Collection
	/collections/{id}/members/	--	Membership container for the parent Collection
	/collections/{id}/members/{prxid}	--	Proxy for the member Collection or Object
	/collections/{id}/related/	--	Related object container for the parent Collection
	/collections/{id}/related/{prxid}	--	 Proxy for the related Object
	----------------------------------------------------------------------------------

	When a PCDMCollection is created, the following child resources are automatically created:
		- /members
		- /related

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
	'''

	def __init__(self, repo, uri='', response=None):

		# fire parent Container init()
		super().__init__(repo, uri="%s/%s" % (pcdm_collections_path, uri), response=response)


	def _post_create(self):

		'''
		resource.create() hook

		For PCDM Collections, post creation, also create 
		'''

		# create /members child resource
		members_child = PCDMMembersContainer(
			self.repo,
			'%s/members' % self.uri_as_string(),
			membershipResource=self.uri,
			hasMemberRelation=self.rdf.prefixes.pcdm.hasMember,
			insertedContentRelation=self.rdf.prefixes.ore.proxyFor)
		members_child.create(specify_uri=True)

		# create /related child resource
		related_child = PCDMRelatedContainer(
			self.repo,
			'%s/related' % self.uri_as_string(),
			membershipResource=self.uri,
			hasMemberRelation=self.rdf.prefixes.ore.aggregates,
			insertedContentRelation=self.rdf.prefixes.ore.proxyFor)
		related_child.create(specify_uri=True)


	# def delete(self):

	# 	'''
	# 	overrides BasicContainer .delete, removing all associated resources
	# 	'''


	def create_child_object(self, uri='', specify_uri=False):

		'''
		create child object to collection
			- create PCDMObject at /objects/raven
			- create children /files, /members, /related, /associated
			- create proxy obect at /collections/poe/members/raven_proxy (if uri provided), with the following triples:
				- rdf:type --> ore.Proxy
				- ore:proxyFor --> pcdmbar.uri
			- because /members is DirectContainer, would create triples:
				- poe.uri --> pcdm.hasMember --> raven.uri

		Args:
			uri: optional uri for child object (should not start with trailing slash)

		Returns:
			PCDMObject
		'''

		# instantiate and create PCDMObject
		obj = PCDMObject(self.repo, uri="%s/%s" % (pcdm_objects_path, uri))
		obj.create(specify_uri=specify_uri)

		# create proxy object
		# proxy_obj = PCDMObject(self.repo, uri="%s/members/%s" % (self.uri, uri))
		# proxy_obj.create(specify_uri=specify_uri)
		# proxy_obj.add_triple(proxy_obj.rdf.prefixes.rdf.type, proxy_obj.rdf.prefixes.ore.Proxy)
		# proxy_obj.add_triple(proxy_obj.rdf.prefixes.ore.proxyFor, obj.uri)
		# proxy_obj.update()

		# create proxy object
		proxy_obj = PCDMProxyObject(self.repo, uri="%s/members/%s" % (self.uri, uri), proxyForURI=obj.uri)
		proxy_obj.create(specify_uri=specify_uri)



class PCDMObject(_models.BasicContainer):

	'''
	Class to represent PCDM Objects in LDP.

	----------------------------------------------------------------------------------
	URI Template	--	Resource Identified
	----------------------------------------------------------------------------------
	/objects/{id}	--	An Object
	/objects/{id}/files/	--	Container for component Files of the Object
	/objects/{id}/files/{bsid}	--	A component File
	/objects/{id}/files/{bsid}/fcr:metadata	--	Technical metadata about the File
	/objects/{id}/members/	--	Membership container for the parent Object
	/objects/{id}/members/{prxid}	--	Proxy for the member Object
	/objects/{id}/related/	--	Related object container for the parent Object
	/objects/{id}/related/{prxid}	--	Proxy for the related Object
	/objects/{id}/associated/	--	Container for associated Files
	----------------------------------------------------------------------------------

	When a PCDMObject is created, the following child resources are automatically created:
		- /files
		- /members
		- /related
		- /associated

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
	'''

	def __init__(self, repo, uri='', response=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, response=response)


	def _post_create(self):

		'''
		resource.create() hook
		'''

		# create /files child resource
		files_child = PCDMFilesContainer(
			self.repo,
			'%s/files' % self.uri_as_string(),
			membershipResource=self.uri,
			hasMemberRelation=self.rdf.prefixes.pcdm.hasFile)
		files_child.create(specify_uri=True)

		# create /members child resource
		members_child = PCDMMembersContainer(
			self.repo,
			'%s/members' % self.uri_as_string(),
			membershipResource=self.uri,
			hasMemberRelation=self.rdf.prefixes.pcdm.hasMember,
			insertedContentRelation=self.rdf.prefixes.ore.proxyFor)
		members_child.create(specify_uri=True)

		# create /related child resource
		related_child = PCDMRelatedContainer(
			self.repo,
			'%s/related' % self.uri_as_string(),
			membershipResource=self.uri,
			hasMemberRelation=self.rdf.prefixes.ore.aggregates,
			insertedContentRelation=self.rdf.prefixes.ore.proxyFor)
		related_child.create(specify_uri=True)

		# create /associated child resource
		associated_child = PCDMAssociatedContainer(
			self.repo,
			'%s/associated' % self.uri_as_string(),
			membershipResource=self.uri,
			hasMemberRelation=self.rdf.prefixes.pcdm.hasRelatedFile)
		associated_child.create(specify_uri=True)


	# def delete(self):

	# 	'''
	# 	overrides BasicContainer .delete, removing all associated resources
	# 	'''



class PCDMProxyObject(_models.BasicContainer):

	'''
	Class to represent PCDM Proxy Objects in PCDM/LDP

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
		proxyFor (rdflib.term.URIRef,str): URI of resource this resource is a proxy for, sets ore:proxyFor triple
	'''

	def __init__(self, repo, uri='', response=None, proxyForURI=None, proxyInURI=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, response=response)

		self.proxyForURI = proxyForURI
		self.proxyInURI = proxyInURI


	def _post_create(self):

		'''
		resource.create() hook
		'''

		# set rdf type
		self.add_triple(self.rdf.prefixes.rdf.type, self.rdf.prefixes.ore.Proxy)

		# set triple for what this resource is a proxy for
		if self.proxyForURI:
			self.add_triple(self.rdf.prefixes.ore.proxyFor, self.proxyForURI)

		# if proxyIn set, add triple
		if self.proxyInURI:
			self.add_triple(self.rdf.prefixes.ore.proxyFor, self.proxyForURI)

		# update
		self.update()


	# def delete(self):

	# 	'''
	# 	overrides BasicContainer .delete, removing all associated resources
	# 	'''



class PCDMFilesContainer(_models.DirectContainer):

	'''
	Class to represent Files under a PCDM Object

	Inherits:
		DirectContainer

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
		membershipResource (rdflib.term): resource that will accumlate triples as children are added
		hasMemberRelation (rdflib.term): predicate that will be used when pointing from URI in ldp:membershipResource to ldp:insertedContentRelation
	'''

	def __init__(self,
		repo,
		uri=None,
		response=None,
		membershipResource=None,
		hasMemberRelation=None):

		# fire parent DirectContainer init()
		super().__init__(
			repo,
			uri=uri,
			response=response,
			membershipResource=membershipResource,
			hasMemberRelation=hasMemberRelation)


	def _post_create(self):

		'''
		resource.create() hook
		'''

		logger.debug('no additional create actions')
		return True



class PCDMMembersContainer(_models.IndirectContainer):

	'''
	Class to represent Related under a PCDM Collection or Object


	Inherits:
		IndirectContainer

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
		membershipResource (rdflib.term): resource that will accumlate triples as children are added
		hasMemberRelation (rdflib.term): predicate that will be used when pointing from URI in ldp:membershipResource to ldp:insertedContentRelation
		insertedContentRelation (rdflib.term): destination for ldp:hasMemberRelation from ldp:membershipResource
	'''

	def __init__(self,
		repo,
		uri=None,
		response=None,
		membershipResource=None,
		hasMemberRelation=None,
		insertedContentRelation=None):

		# fire parent Container init()
		super().__init__(
			repo,
			uri=uri,
			response=response,
			membershipResource=membershipResource,
			hasMemberRelation=hasMemberRelation,
			insertedContentRelation=insertedContentRelation)


	def _post_create(self):

		'''
		resource.create() hook
		'''

		logger.debug('no additional create actions')
		return True



class PCDMRelatedContainer(_models.IndirectContainer):

	'''
	Class to represent Related under a PCDM Collection or Object


	Inherits:
		IndirectContainer

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
		membershipResource (rdflib.term): resource that will accumlate triples as children are added
		hasMemberRelation (rdflib.term): predicate that will be used when pointing from URI in ldp:membershipResource to ldp:insertedContentRelation
		insertedContentRelation (rdflib.term): destination for ldp:hasMemberRelation from ldp:membershipResource
	'''

	def __init__(self,
		repo,
		uri=None,
		response=None,
		membershipResource=None,
		hasMemberRelation=None,
		insertedContentRelation=None):

		# fire parent Container init()
		super().__init__(
			repo,
			uri=uri,
			response=response,
			membershipResource=membershipResource,
			hasMemberRelation=hasMemberRelation,
			insertedContentRelation=insertedContentRelation)


	def _post_create(self):

		'''
		resource.create() hook
		'''

		logger.debug('no additional create actions')
		return True



class PCDMAssociatedContainer(_models.IndirectContainer):

	'''
	Class to represent Associated under a PCDM Object


	Inherits:
		IndirectContainer

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
		membershipResource (rdflib.term): resource that will accumlate triples as children are added
		hasMemberRelation (rdflib.term): predicate that will be used when pointing from URI in ldp:membershipResource to ldp:insertedContentRelation
		insertedContentRelation (rdflib.term): destination for ldp:hasMemberRelation from ldp:membershipResource
	'''

	def __init__(self,
		repo,
		uri=None,
		response=None,
		membershipResource=None,
		hasMemberRelation=None,
		insertedContentRelation=None):

		# fire parent Container init()
		super().__init__(
			repo,
			uri=uri,
			response=response,
			membershipResource=membershipResource,
			hasMemberRelation=hasMemberRelation,
			insertedContentRelation=insertedContentRelation)


	def _post_create(self):

		'''
		resource.create() hook
		'''

		logger.debug('no additional create actions')
		return True











