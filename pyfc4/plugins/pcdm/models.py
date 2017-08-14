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



class Collection(_models.BasicContainer):

	'''
	Class to represent PCDM Collections in LDP.


	URI Template	--	Resource Identified
	/collections/{id}	--	A Collection
	/collections/{id}/members/	--	Membership container for the parent Collection
	/collections/{id}/members/{prxid}	--	Proxy for the member Collection or Object
	/collections/{id}/related/	--	Related object container for the parent Collection
	/collections/{id}/related/{prxid}	--	 Proxy for the related Object

	'''

	def __init__(self, repo, uri=None, response=None):

		# fire parent Container init()
		super().__init__(repo, uri=uri, response=response)


	def _post_create(self):

		'''
		resource.create() hook
		'''

		logger.debug('_post_create firing')



# class Object(models.BasicContainer):

# 	'''
	
# 	'''

# 	def __init__(self,
# 		repo,
# 		parent_object,
# 		uri=None,
# 		response=None,
# 		membershipResource=None,
# 		hasMemberRelation=None):

# 		# fire parent Container init()
# 		super().__init__(repo, uri=uri, response=response)

# 		# if resource does not yet exist, set rdf:type
# 		self.add_triple(self.rdf.prefixes.rdf.type, self.rdf.prefixes.ldp.DirectContainer)

# 		# save membershipResource, hasMemberRelation		
# 		self.membershipResource = membershipResource
# 		self.hasMemberRelation = hasMemberRelation

# 		# if membershipResource or hasMemberRelation args are set, set triples
# 		if membershipResource:
# 			self.add_triple(self.rdf.prefixes.ldp.membershipResource, membershipResource)
# 		if hasMemberRelation:
# 			self.add_triple(self.rdf.prefixes.ldp.hasMemberRelation, hasMemberRelation)



# class PCDM_Files(models.DirectContainer):

# 	'''

# 	'''

# 	def __init__(self,
# 		repo,
# 		parent_object,
# 		uri=None,
# 		response=None,
# 		membershipResource=None,
# 		hasMemberRelation=None):

# 		# fire parent Container init()
# 		super().__init__(repo, uri=uri, response=response)

# 		# if resource does not yet exist, set rdf:type
# 		self.add_triple(self.rdf.prefixes.rdf.type, self.rdf.prefixes.ldp.DirectContainer)

# 		# save membershipResource, hasMemberRelation		
# 		self.membershipResource = membershipResource
# 		self.hasMemberRelation = hasMemberRelation

# 		# if membershipResource or hasMemberRelation args are set, set triples
# 		if membershipResource:
# 			self.add_triple(self.rdf.prefixes.ldp.membershipResource, membershipResource)
# 		if hasMemberRelation:
# 			self.add_triple(self.rdf.prefixes.ldp.hasMemberRelation, hasMemberRelation)