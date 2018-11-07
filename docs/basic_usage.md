## Basic Usage

Assuming an instance of FC4 at `http://localhost:8080/rest`

  * [establishing repository connection](#instantiate-repository-handle)
  * creating resources
    * [RDF](#create-rdf-resources)
    * [NonRDF](#create-nonrdf-binary-resources)
  * [retrieving resources](#get-resources)
  * [resource relationships](#resource-relationships)
    * [parents / children](#convenience-methods-for-children--parents)
    * [reading / writing triples](#reading--writing-triples)
    * [object-like access](#object-like-access)
  * [transactions](#transactions)
  * [versioning](#versioning)

#### Import pyfc4
```
from pyfc4.models import *
```

#### Instantiate repository handle
```
repo = Repository('http://localhost:8080/rest','username','password')
```

#### Create RDF Resources

Create [BasicContainer](https://www.w3.org/TR/ldp/#ldpbc) with uri `foo`.  Adding `specifiy_true` to `create()` uses the HTTP verb `PUT`, and creates the resource at the desired URI:

```
foo = BasicContainer(repo, 'foo')
foo.create(specify_uri=True) 
```

Create child resource `foo/bar` under `foo`:

```
bar = BasicContainer(repo, 'foo/bar')
bar.create(specify_uri=True) 
```

Alternatively, use the built-in Fedora URI minter issuing `POST` requests by not setting `specify_uri` (which defaults to `False`).

```
In [1]: bc = BasicContainer(repo)
In [2]: bc.create()
Out[2]: True
In [3]: bc.uri # check newly created and assigned resource uri
Out[3]: rdflib.term.URIRef('http://localhost:8080/rest/c4/a1/12/f5/c4a112f5-ab38-476c-8ebc-75b221b18300')
```

Though each resource contains mechanisms for viewing and modifying RDF data under `self.rdf`, there is the convenience method `self.dump()` to return the raw RDF for the resource:
```
# default serialization is turtle (ttl)
In [5]: print(foo.dump())

@prefix dbpedia: <http://dbpedia.org/ontology/> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix ebucore: <http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#> .
@prefix fedora: <http://fedora.info/definitions/v4/repository#> .
@prefix fedoraconfig: <http://fedora.info/definitions/v4/config#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix ldp: <http://www.w3.org/ns/ldp#> .
@prefix ore: <http://www.openarchives.org/ore/terms/> .
@prefix pcdm: <http://pcdm.org/models#> .
@prefix premis: <http://www.loc.gov/premis/rdf/v1#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix test: <info:fedora/test/> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xmlns: <http://www.w3.org/2000/xmlns/> .
@prefix xs: <http://www.w3.org/2001/XMLSchema> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix xsi: <http://www.w3.org/2001/XMLSchema-instance> .

<http://localhost:8080/rest/foo> a fedora:Container,
        fedora:Resource,
        ldp:Container,
        ldp:RDFSource ;
    fedora:created "2017-08-29T20:05:57.109000+00:00"^^xsd:dateTime ;
    fedora:createdBy "bypassAdmin"^^xsd:string ;
    fedora:hasParent <http://localhost:8080/rest/> ;
    fedora:lastModified "2017-08-29T20:05:57.109000+00:00"^^xsd:dateTime ;
    fedora:lastModifiedBy "bypassAdmin"^^xsd:string ;
    fedora:writable true .

```

Optionally, provide a serialization format that python's rdflib library accepts, such as `application/rdf+xml`:
```
In [7]: print(foo.dump(format='application/rdf+xml'))
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
   xmlns:fedora="http://fedora.info/definitions/v4/repository#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
>
  <rdf:Description rdf:about="http://localhost:8080/rest/foo">
    <fedora:lastModifiedBy rdf:datatype="http://www.w3.org/2001/XMLSchema#string">bypassAdmin</fedora:lastModifiedBy>
    <rdf:type rdf:resource="http://fedora.info/definitions/v4/repository#Resource"/>
    <rdf:type rdf:resource="http://fedora.info/definitions/v4/repository#Container"/>
    <fedora:lastModified rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2017-08-29T20:05:57.109000+00:00</fedora:lastModified>
    <fedora:writable rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">true</fedora:writable>
    <rdf:type rdf:resource="http://www.w3.org/ns/ldp#Container"/>
    <fedora:createdBy rdf:datatype="http://www.w3.org/2001/XMLSchema#string">bypassAdmin</fedora:createdBy>
    <rdf:type rdf:resource="http://www.w3.org/ns/ldp#RDFSource"/>
    <fedora:created rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2017-08-29T20:05:57.109000+00:00</fedora:created>
    <fedora:hasParent rdf:resource="http://localhost:8080/rest/"/>
  </rdf:Description>
</rdf:RDF>
```

#### Create NonRDF (Binary) Resources

FC4, and LDP instances in general, also have [NonRDFSource](https://www.w3.org/TR/ldp/#ldpnr) (Binary) resources.  These contain binary files.

Create a binary resource `foo/baz` under `foo`.  This opens the file `README.md` as the binary content, and sets the mimetype as `text/plain`:

```
baz = Binary(repo, 'foo/baz') # 'Binary' is alias for 'NonRDFSource' which also works
baz.binary.data = open('README.md','rb')
baz.binary.mimetype = 'text/plain'
baz.create(specify_uri=True)
```

Alternatively, you can also set the binary contents directly at `baz.binary.data`:

```
baz1 = Binary(repo, 'foo/baz1')
baz1.binary.data = 'I see a little silhouetto of a man. Scaramouche, Scaramouche, will you do the fandango?'
baz1.binary.mimetype = 'text/plain'
baz1.create(specify_uri=True)
```

or, by providing a remote URL that Fedora will retrieve and attach to that NonRDF resource during creation:

```
baz2 = Binary(repo, 'foo/baz2')
baz2.binary.location = 'http://example.org/image.jpg'
baz2.binary.mimetype = 'image/jpeg'
baz2.create(specify_uri=True)
```

#### Get Resources

To retrieve resources to work with, the repository instance `repo` has method `get_resource` that returns a `Resource` instance of that URI.  `get_resource` will accept the full URI, `http://localhost:8080/rest/foo`, a "short" uri, `foo`, or an `rdflib.term.URIRef` instance, `rdflib.term.URIRef('http://localhost:8080/rest/foo')`:

```
# all have same result
foo = repo.get_resource('http://localhost:8080/rest/foo')
foo = repo.get_resource('foo')
foo = repo.get_resource(rdflib.term.URIRef('http://localhost:8080/rest/foo'))
```

When `HEAD` request for resource returns HTTP status code `200`, `foo.exists` is set to `True`:

```
In [8]: foo.exists
Out[8]: True
```

Resources also contain the method `check_exists` to ping the repository with a `HEAD` request and update the attribute `.exists`:

```
In [9]: foo.check_exists()
Out[9]: True
```

Resources have the attribute `.uri` which returns a `rdflib.term.URIRef` instance, or optionally, can be returned as a string:

```
In [6]: foo.uri
Out[6]: rdflib.term.URIRef('http://localhost:8080/rest/foo')

In [7]: foo.uri_as_string()
Out[7]: 'http://localhost:8080/rest/foo'
```

Retrieving resources that do not exist will return `False`:

```
i_do_not_exist = repo.get_resource('xyz123')
In [5]: i_do_not_exist
Out[5]: False
```

Retrieving NonRDFSources is similar to RDFSources, with the addition of a `self.binary` section.  The `self.binary.mimetype` is retrieved from the resource's graph, while the binary data itself is made ready for access, *but not downloaded*, at `self.binary.data` as a `requests.models.Response` instance.  

The easiest and most performant way to use this data is to use a requests object's built-in [`iter_content`](http://docs.python-requests.org/en/master/api/#requests.Response.iter_content) method.

For example:
```
# retrieve binary resource
baz = repo.get_resource('foo/baz')

# observe binary.data
In [8]: type(baz.binary.data)
Out[8]: requests.models.Response

# access binary data in one swoop
baz.binary.data.content

# chunk data for large files
for chunk in baz.binary.data.iter_content(1024): using 1024 byte chunk size
  # do things with chunk
```

You can also return specific byte ranges with a built-in convenience function, `self.binary.range` that expects the beginning and end of the range, with an optional `stream` parameter:
```
# iterate through bytes 500-1000
for chunk in baz.binary.range(500,1000).iter_content(1024):
  # do things with chunk
```

#### Resource relationships

##### Convenience methods for children / parents

Based on the predicate `ldp:contains`, get children of resource:

```
In [2]: foo.children()
Out[2]: 
[rdflib.term.URIRef('http://localhost:8080/rest/foo/baz'),
 rdflib.term.URIRef('http://localhost:8080/rest/foo/bar')]
```

Optionally, return pyfc4 `Resource` instances of child objects:

```
In [3]: foo.children(as_resources=True)
Out[3]: 
[<NonRDFSource Resource, uri: http://localhost:8080/rest/foo/baz>,
 <BasicContainer Resource, uri: http://localhost:8080/rest/foo/bar>]
```

Based on the predicate `fedora:hasParent`, get parent of resource:

```
In [4]: bar.parents()
Out[4]: [rdflib.term.URIRef('http://localhost:8080/rest/foo')]
```

Again, can return parent as pyfc4 `Resource` instance:

```
In [5]: bar.parents(as_resources=True)
Out[5]: [<BasicContainer Resource, uri: http://localhost:8080/rest/foo>]
```

##### Reading / writing triples

When working with triples for a resource, the subject for all triples is assumed to be the URI of the resource itself.  Additionally, resources come with some predefind prefixes for ease of use.  These can be found under `foo.rdf.prefixes`, and derive from the repository instance at `repo.context`.

All modifications are written to the parsed graph for a resource under `foo.rdf.graph`, but are *not* written to repository intsance of the resource.  This allows for batch modifying, without multiple request/responses from the server.

To add triples, pass a predicate and an object:

```
# using built-in prefixes, and a string literal
foo.add_triple(foo.rdf.prefixes.dc['subject'], 'minty')

# example of a foaf predicate, pointing to another resource
foo.add_triple(foo.rdf.prefixes.foaf['knows'], bar.uri)
```

To commit these modifications to the resource's graph, use the method `.update`.  This sends the updated graph as a `PATCH` request, then retrieves the updated graph and sets that to the resource instance.

```
foo.update()
```

Removing triples is similar to adding, passing a predicate and an object:

```
foo.remove_triple(foo.rdf.prefixes.dc['subject'], 'minty')
foo.update()
```

**Note:** Multiple additions and removals can happen before issuing `.update()`.  All modifications are stored locally in a graph, then diffed against the last known graph from the repository, and only changes are sent.

In addition to the default prefixes/namespaces, you can instantiate a repository instance with additional prefixes that will trickle through and be available in similar fashion:

```
# instantiate repository with additional GeoNames prefix 'gn'
repo = Repository('http://localhost:8080/rest','username','password', context={'gn':'http://www.geonames.org/ontology#'})
DEBUG:pyfc4.models:context provided, merging with defaults

# create resource
goober = BasicContainer(repo, 'goober')
goober.create(specify_uri=True)

# add triple using GeoNames prefix 'gn'
goober.add_triple(goober.rdf.prefixes.gn['countryCode'], 'FR')
goober.update()

# retrieve triples with gn.countryCode predicate, note that 'gn' prefix is expanded in triple creation and retrieval
for t in goober.triples(p=goober.rdf.prefixes.gn['countryCode']):
	print(t)
(rdflib.term.URIRef('http://localhost:8080/rest/goober'), rdflib.term.URIRef('http://www.geonames.org/ontology#countryCode'), rdflib.term.Literal('FR'))
```

##### Object-like access

Somewhat of a convenience addition, you can access triples parsed from a resource's graph in an object-like fashion.  For example:

```
# get ldp:contains 
In [6]: foo.rdf.triples.ldp.contains
Out[6]:
[rdflib.term.URIRef('http://localhost:8080/rest/foo/bar'),
 rdflib.term.URIRef('http://localhost:8080/rest/foo/baz')]

# In [8]: goober.rdf.triples.foaf.knows
Out[8]: [rdflib.term.URIRef('http://localhost:8080/rest/tronic/tronic2')]

# a more complete example of how this trickles through
# add namespace
In [9]: foo.add_namespace('licorice','http://licorice.org#')

# add triple
In [10]: foo.add_triple(foo.rdf.prefixes.licorice['best_color'], 'black')

# update
In [11]: foo.update()
Out[11]: True

# now, object-like access to this triple parsed from graph
In [12]: foo.rdf.triples.licorice.best_color
Out[12]: [rdflib.term.Literal('black', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#string'))]
```

#### Transactions

pyfc4 also supports use of [Transactions](https://wiki.duraspace.org/display/FEDORA40/Transactions) in FC4.  Transactions allow for work to be done on resources in the repository within a contained session, with the ability to commit or roll back changes made within that session.

From a practical point of view, in FC4, transactions are a prefix attached to all URIs that indicate these resources are part of, and being modified within, that transaction.  So, where the base path may have originally been, `http://localhost:8080/rest`, for a scoped transaction, the base path might become something like, `http://localhost:8080/rest/txn:123456789/`.

In pyfc4, transaction are spawned from a repository instance, given a name (either declared or minted), and stored in a dictionary at `repo.txns`.  Multiple transactions may be running at one time.  Transaction also expire, automatically, after three minutes of non-use.

For example, to start a new transaction called `postcard_ingest` to handle the ingest of a handful of resources that relate to a single image: 

```
In [1]: postcard_txn = repo.start_txn('postcard_txn')
DEBUG:pyfc4.models:POST request for http://localhost:8080/rest//fcr:tx, format None, headers None
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): localhost
DEBUG:urllib3.connectionpool:http://localhost:8080 "POST /rest//fcr:tx HTTP/1.1" 201 0
DEBUG:pyfc4.models:spawning transaction: http://localhost:8080/rest/tx:12f2534f-b088-4a03-8546-54ad6bec3c9b
DEBUG:pyfc4.models:context provided, merging with defaults
```

At any time, you can confirm whether or not a transaction exists, and view when it will expire:
```
In [3]: postcard_txn.active
Out[3]: True
In [4]: postcard_txn.expires
Out[4]: 'Thu, 03 Aug 2017 19:40:50 GMT'
```

To keep a transaction alive:
```
In [5]: postcard_txn.keep_alive()
Out[5]: True

In [6]: postcard_txn.expires
Out[6]: 'Thu, 03 Aug 2017 19:42:32 GMT' # notice bumped time
```

You can also fire transactions without declaring a name, and receive an automatically generated one:
```
In [7]: txn = repo.start_txn()
DEBUG:pyfc4.models:POST request for http://localhost:8080/rest//fcr:tx, format None, headers None
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): localhost
DEBUG:urllib3.connectionpool:http://localhost:8080 "POST /rest//fcr:tx HTTP/1.1" 201 0
DEBUG:pyfc4.models:spawning transaction: http://localhost:8080/rest/tx:bee8fb1f-4b91-438e-bf95-c5484bd4a8d6
DEBUG:pyfc4.models:context provided, merging with defaults

In [8]: txn.name
Out[8]: '9d4eff000e8d40bf913ac8424725799b'
```

Multiple transactions can exist for a single repository instance:
```
In [9]: repo.txns
Out[9]:
{'9d4eff000e8d40bf913ac8424725799b': <pyfc4.models.Transaction at 0x105ebbef0>,
 'postcard_txn': <pyfc4.models.Transaction at 0x106871b00>}
 ```

 While a transaction is open, you can use just like a normal repository instance.  Here's an example of creating a resource, passing a transacation as the repository instance:
 ```
 blackberry = BasicContainer(postcard_txn,'blackberry')
 blackberry.create(specify_uri=True)
 Out[16]: True
 ```

 Then, when ready to commit changes that have occurred within the transaction:
 ```
In [18]: postcard_txn.commit()
DEBUG:pyfc4.models:POST request for http://localhost:8080/rest/tx:12f2534f-b088-4a03-8546-54ad6bec3c9b/fcr:tx/fcr:commit, format None, headers None
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): localhost
DEBUG:urllib3.connectionpool:http://localhost:8080 "POST /rest/tx:12f2534f-b088-4a03-8546-54ad6bec3c9b/fcr:tx/fcr:commit HTTP/1.1" 204 0
DEBUG:pyfc4.models:commit for transaction: http://localhost:8080/rest/tx:12f2534f-b088-4a03-8546-54ad6bec3c9b/, successful
Out[18]: True

In [19]: postcard_txn.active
Out[19]: False
```

Conversely, to rollback all changes that occurred within a transaction:
```
postcard_txn.rollback()
```

#### Versioning

pyfc4 also supports some versioning of resources.  Most interactions, if not all, involve the URL pattern `/foo/fcr:versions`.  Versions represent a state of a resource, including the RDF information, and binary files associated with a NonRDFSource.  They can be created, retrieved, reverted to, and deleted.

Create a new version:
```
# only argument is a string value to serve as a label for the version
foo.create_version('v1')
```

You can see this version was created and saved to `foo.versions`:
```
In [24]: foo.versions
Out[24]: namespace(v1=<ResourceVersion Resource, uri: http://localhost:8080/rest/foo/fcr:versions/v1>)
```

When a resource is retrieved, previous versions are *not* automatically retrieved, for performance reasons.  However, previous versions can all be retrieved and found at `foo.versions`:
```
foo.get_versions()
In [29]: foo.versions
Out[29]: namespace(v1=<ResourceVersion Resource, uri: http://localhost:8080/rest/foo/fcr:versions/v1>)
```

Each version is an instance of the class `ResourceVersion` that includes a couple methods.  One, is to revert the current resource to that version:
```
foo.versions.v1.revert_to()
```

Another, is to delete that version from the resource's history:
```
foo.versions.v1.delete()
```

Each `ResourceVersion` instance contains that version of the resource at `.resource`, fully parsed, and available for investigating:
```
In [32]: foo.versions.v1.resource.rdf.triples.ldp.contains
Out[32]: 
[rdflib.term.URIRef('http://localhost:8080/rest/foo/fcr:versions/v1/bar'),
 rdflib.term.URIRef('http://localhost:8080/rest/foo/fcr:versions/v1/baz')]

In [33]: foo.versions.v1.resource.children()
Out[33]: 
[rdflib.term.URIRef('http://localhost:8080/rest/foo/fcr:versions/v1/baz'),
 rdflib.term.URIRef('http://localhost:8080/rest/foo/fcr:versions/v1/bar')]
```
**Note:** Resource versions cannot be modified, rendering `version.update()` useless.
