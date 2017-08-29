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


# configurations
# TODO: https://github.com/ghukill/pyfc4/issues/76
objects_path = 'objects'
collections_path = 'collections'


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

	def __init__(self, repo, uri='', response=None):

		# fire parent Container init()
		super().__init__(repo, uri="%s/%s" % (collections_path, uri), response=response)

		
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

	def __init__(self, repo, uri='', response=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, response=response)

		# members, related
		self.members = self.get_members()
		self.files = self.get_files()
		self.associated = self.get_associated()


	def get_members(self, retrieve=False):

		'''
		get pcdm:hasMember for this resource, optionally retrieving resource payload

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples.pcdm, 'hasMember'):
			members = [ PCDMObject(self.repo, uri) for uri in self.rdf.triples.pcdm.hasMember ]

			# if retrieve, perform retrieve through .refresh()
			if retrieve:
				for member in members:
					member.refresh()

			# return
			return members

		else:
			return []


	def get_files(self, retrieve=False):

		'''
		get pcdm:hasFile for this resource, optionally retrieving resource payload

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples.pcdm, 'hasFile'):
			files = [ _models.NonRDFSource(self.repo, uri) for uri in self.rdf.triples.pcdm.hasFile ]

			# if retrieve, perform retrieve through .refresh()
			if retrieve:
				for file in files:
					file.refresh()

			# return
			return files

		else:
			return []


	def get_associated(self, retrieve=False):

		'''
		get pcdm:hasRelatedFile for this resource, optionally retrieving resource payload

		Args:
			retrieve (bool): if True, issue .refresh() on resource thereby confirming existence and retrieving payload
		'''

		if self.exists and hasattr(self.rdf.triples.pcdm, 'hasRelatedFile'):
			files = [ _models.NonRDFSource(self.repo, uri) for uri in self.rdf.triples.pcdm.hasRelatedFile ]

			# if retrieve, perform retrieve through .refresh()
			if retrieve:
				for file in files:
					file.refresh()

			# return
			return files

		else:
			return []


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
		proxyFor (rdflib.term.URIRef,str): URI of resource this resource is a proxy in, sets ore:proxyIn triple
	'''

	def __init__(self, repo, uri='', response=None, proxyForURI=None, proxyInURI=None):

		# if full URI provided, as is the case with retrieval, derive "short" URI
		if repo.root in uri:
			uri = uri.split(collections_path)[-1].lstrip('/')

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











