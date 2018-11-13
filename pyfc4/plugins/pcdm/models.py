# pyfc4 plugin: pcdm.models

import copy
import time

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

class PCDMCollection(_models.BasicContainer):

	'''
	Class to represent PCDM Collections in LDP.

	----------------------------------------------------------------------------------
	URI Template	--	Resource Identified
	----------------------------------------------------------------------------------
	/collections/{id}	--	A Collection
	/collections/{id}/members/	--	Membership container for the parent Collection
	/collections/{id}/members/{proxy_obj_id}	--	Proxy for the member Collection or Object
	/collections/{id}/related/	--	Related object container for the parent Collection
	/collections/{id}/related/{proxy_obj_id}	--	 Proxy for the related Object
	----------------------------------------------------------------------------------

	When a PCDMCollection is created, the following child resources are automatically created:
		- /members
		- /related

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef, str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
	'''

	def __init__(self, repo, uri=None, response=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, response=response)

		# members, related
		self.members = self.get_members()
		self._orig_members = copy.deepcopy(self.members)
		self.related = self.get_related()
		self._orig_related = copy.deepcopy(self.related)


	def _post_create(self, auto_refresh=False):

		'''
		resource.create() hook

		For PCDM Collections, post creation, also create
		'''

		# set PCDM triple as Collection
		self.add_triple(self.rdf.prefixes.rdf.type, self.rdf.prefixes.pcdm.Collection)
		self.update(auto_refresh=auto_refresh)

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


	def get_members(self):

		'''
		get pcdm:hasMember for this resource, optionally retrieving resource payload

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples, 'pcdm') and hasattr(self.rdf.triples.pcdm, 'hasMember'):
			members = [ self.repo.parse_uri(uri) for uri in self.rdf.triples.pcdm.hasMember ]

			# return
			return members

		else:
			return []


	def get_related(self):

		'''
		get ore:aggregates for this resource, optionally retrieving resource payload

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples, 'ore') and hasattr(self.rdf.triples.ore, 'aggregates'):
			related = [ self.repo.parse_uri(uri) for uri in self.rdf.triples.ore.aggregates ]

			# return
			return related

		else:
			return []


	def _post_update(self):

		'''
		'''

		self.update_pcdm_relationship()


	def _post_refresh(self):

		'''
		'''

		self.update_pcdm_relationship()


	def update_pcdm_relationship(self):

		'''
		'''

		logger.debug("updating PCDM relationships")

		# determine member diff
		member_diff = {
			'new':set(self.members) - set(self._orig_members),
			'removed':set(self._orig_members) - set(self.members)
		}
		logger.debug(member_diff)

		# create proxy objects for added members
		for resource_uri in member_diff['new']:
			proxy_obj = PCDMProxyObject(self.repo, uri="%s/members" % (self.uri), proxyForURI=resource_uri)
			proxy_obj.create()

		# remove proxy objects for added members
		for resource_uri in member_diff['removed']:
			proxy_obj = self.repo.get_resource(resource_uri)
			proxy_obj.delete(remove_tombstone=True)


		# determine member diff
		related_diff = {
			'new':set(self.related) - set(self._orig_related),
			'removed':set(self._orig_related) - set(self.related)
		}
		logger.debug(member_diff)

		# create proxy objects for added members
		for resource_uri in related_diff['new']:
			proxy_obj = PCDMProxyObject(self.repo, uri="%s/related" % (self.uri), proxyForURI=resource_uri)
			proxy_obj.create()

		# remove proxy objects for added members
		for resource_uri in related_diff['removed']:
			proxy_obj = self.repo.get_resource(resource_uri)
			proxy_obj.delete(remove_tombstone=True)



class PCDMObject(_models.BasicContainer):

	'''
	Class to represent PCDM Objects in LDP.

	----------------------------------------------------------------------------------
	URI Template	--	Resource Identified
	----------------------------------------------------------------------------------
	/objects/{id}	--	An Object
	/objects/{id}/files/	--	Container for component Files of the Object
	/objects/{id}/files/{binary_id}	--	A component File
	/objects/{id}/files/{binary_id}/fcr:metadata	--	Technical metadata about the File
	/objects/{id}/members/	--	Membership container for the parent Object
	/objects/{id}/members/{proxy_obj_id}	--	Proxy for the member Object
	/objects/{id}/related/	--	Related object container for the parent Object
	/objects/{id}/related/{proxy_obj_id}	--	Proxy for the related Object
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

	def __init__(self, repo, uri=None, response=None, retrieve_pcdm_links=True):

		# fire parent Container init()
		super().__init__(repo, uri=uri, response=response)

		# members, related
		self.members = self.get_members(retrieve=retrieve_pcdm_links)
		self._orig_members = copy.deepcopy(self.members)
		self.files = self.get_files(retrieve=retrieve_pcdm_links)
		self._orig_files = copy.deepcopy(self.files)
		self.associated = self.get_associated(retrieve=retrieve_pcdm_links)
		self._orig_associated = copy.deepcopy(self.associated)
		self.related = self.get_related(retrieve=retrieve_pcdm_links)
		self._orig_related = copy.deepcopy(self.related)


	def _post_create(self, auto_refresh=False):

		'''
		resource.create() hook
		'''

		# set PCDM triple as Object
		self.add_triple(self.rdf.prefixes.rdf.type, self.rdf.prefixes.pcdm.Object)
		self.update(auto_refresh=auto_refresh)

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


	def get_members(self, retrieve=False):

		'''
		get pcdm:hasMember for this resource

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples, 'pcdm') and hasattr(self.rdf.triples.pcdm, 'hasMember'):
			members = [ self.repo.parse_uri(uri) for uri in self.rdf.triples.pcdm.hasMember ]

			# return
			return members

		else:
			return []


	def get_files(self, retrieve=False):

		'''
		get pcdm:hasFile for this resource

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples, 'pcdm') and hasattr(self.rdf.triples.pcdm, 'hasFile'):
			files = [ self.repo.parse_uri(uri) for uri in self.rdf.triples.pcdm.hasFile ]

			# return
			return files

		else:
			return []


	def get_associated(self, retrieve=False):

		'''
		get pcdm:hasRelatedFile for this resource

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples, 'pcdm') and hasattr(self.rdf.triples.pcdm, 'hasRelatedFile'):
			files = [ self.repo.parse_uri(uri) for uri in self.rdf.triples.pcdm.hasRelatedFile ]

			# return
			return files

		else:
			return []


	def get_related(self, retrieve=False):

		'''
		get ore:aggregates for this resource

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples, 'ore') and hasattr(self.rdf.triples.ore, 'aggregates'):
			related = [ self.repo.parse_uri(uri) for uri in self.rdf.triples.ore.aggregates ]

			# return
			return related

		else:
			return []


	def _post_update(self):

		'''
		'''

		self.update_pcdm_relationship()


	def _post_refresh(self):

		'''
		'''

		self.update_pcdm_relationship()


	def update_pcdm_relationship(self):

		'''
		'''

		logger.debug("updating PCDM relationships")

		# determine member diff
		member_diff = {
			'new':set(self.members) - set(self._orig_members),
			'removed':set(self._orig_members) - set(self.members)
		}
		logger.debug(member_diff)

		# create proxy objects for added members
		for resource_uri in member_diff['new']:
			proxy_obj = PCDMProxyObject(self.repo, uri="%s/members" % (self.uri), proxyForURI=resource_uri)
			proxy_obj.create()

		# remove proxy objects for added members
		for resource_uri in member_diff['removed']:
			proxy_obj = self.repo.get_resource(resource_uri)
			proxy_obj.delete(remove_tombstone=True)


		# determine member diff
		related_diff = {
			'new':set(self.related) - set(self._orig_related),
			'removed':set(self._orig_related) - set(self.related)
		}
		logger.debug(member_diff)

		# create proxy objects for added members
		for resource_uri in related_diff['new']:
			proxy_obj = PCDMProxyObject(self.repo, uri="%s/related" % (self.uri), proxyForURI=resource_uri)
			proxy_obj.create()

		# remove proxy objects for added members
		for resource_uri in related_diff['removed']:
			proxy_obj = self.repo.get_resource(resource_uri)
			proxy_obj.delete(remove_tombstone=True)



class PCDMFile(_models.NonRDFSource):

	'''
	Extends NonRDFSource(Binary).

	Inherits:
		NonRDFSource

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
		binary_data: optional, file data, accepts file-like object, raw data, or URL
		binary_mimetype: optional, mimetype for provided data
	'''

	def __init__(self, repo, uri=None, response=None, binary_data=None, binary_mimetype=None):

		# fire parent Resource init()
		super().__init__(repo, uri=uri, response=response, binary_data=binary_data, binary_mimetype=binary_mimetype)


	def _post_create(self, auto_refresh=False):

		'''
		resource.create() hook

		For PCDM File
		'''

		# set PCDM triple as Collection
		self.add_triple(self.rdf.prefixes.rdf.type, self.rdf.prefixes.pcdm.File)
		self.update(auto_refresh=auto_refresh)



class PCDMProxyObject(_models.BasicContainer):

	'''
	Class to represent PCDM Proxy Objects in PCDM/LDP

	Args:
		repo (Repository): instance of Repository class
		uri (rdflib.term.URIRef,str): input URI
		response (requests.models.Response): defaults None, but if passed, populate self.data, self.headers, self.status_code
		proxyFor (rdflib.term.URIRef,str): URI of resource this resource is a proxy for, sets ore:proxyFor triple
		proxyFor (rdflib.term.URIRef,str): URI of resource this resource is a proxy in, sets ore:proxyIn triple
	'''

	def __init__(self, repo, uri=None, response=None, proxyForURI=None, proxyInURI=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, response=response)

		self.proxyForURI = proxyForURI
		self.proxyInURI = proxyInURI


	def _post_create(self, auto_refresh=False):

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
		self.update(auto_refresh=auto_refresh)



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



class PCDMAssociatedContainer(_models.DirectContainer):

	'''
	Class to represent Associated under a PCDM Object


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
