# pyfc4 plugin: pcdm.models

# import pyfc4 base models
from pyfc4 import models as _models

# logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

'''
Implementation of PCDM in LDP.
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
	/collections/{id}/members/{prxid}	--	Proxy for the member Collection or Object
	/collections/{id}/related/	--	Related object container for the parent Collection
	/collections/{id}/related/{prxid}	--	 Proxy for the related Object
	----------------------------------------------------------------------------------

	When a PCDMCollection is created, the following child resources are automatically created:
		- /members
		- /related
	'''

	def __init__(self, repo, uri=None, response=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, response=response)


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



class PCDMObject(_models.BasicContainer):

	'''
	Class to represent PCDM Collections in LDP.

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
	'''

	def __init__(self, repo, uri=None, response=None):

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











