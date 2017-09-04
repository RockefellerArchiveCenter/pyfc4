# PCDM plugin for pyfc4

## Overview

This plugin provides basic support for the [Portland Common Data Model (PCDM)](http://pcdm.org/).  Currently, only a basic PCDM implementation of Collections, Objects, and Files; not including the [PCDM Works ontology](http://pcdm.org/2016/02/16/works).

This plugin eases the implementation of PCDM in the Linked Data Platform (LDP).  For example, creating a `pcdm.models.PCDMObject` will automatically create child directories such as `/members`, `/related`, `/files`, and `/associated` as suggested by PCDM in LDP recommendations.

Additionally, it provides some convenience methods and patterns for observing established PCDM relationships between resources.

As a plugin, it does not influence or interfere with the basic FC4/LDP functionality of pyfc4, but only extends it.

## Basic Usage

### Setup custom repository handle

The first step is importing the plugin alongside pyfc4, and instantiating a repository instance that includes the PCDM plugin custom resource type parser by setting the `custom_resource_type_parser` argument:  

```
# import base models
from pyfc4.models import *

# import pcdm models
from pyfc4.plugins import pcdm

repo = Repository(
	REPO_ROOT,
	REPO_USERNAME,
	REPO_PASSWORD,
	default_serialization='text/turtle',
	custom_resource_type_parser=pcdm.custom_resource_type_parser)
```

This custom parser, instead of reading the `Link` header to determine the LDP resource type, per the LDP spec, will retrieve the resource's entire graph and parse, looking for a PCDM `rdf:type` triple.  Rough tests have shown this approach to be almost as quick, as it does not require a `HEAD` and `GET` request as the default parser does.

### Create PCDM Collection and Objects

One thing to note: this plugin does not assume a default location for collections or objects.  Though a PCDM in LDP recommendation suggets there should be default locations such as `/collections` and/or `/objects`, with the option of submitting custom URI's, this proved akward at best.  Instead, this plugin assumes the user will handle the creation of resources in appropriate places.  This also opens the door for nested collection and object locations, again, falling on the user to implement as they wish.  

Create an example collection `colors`:
```
# create colors collection
colors = pcdm.models.PCDMCollection(repo, 'colors')
colors.create(specify_uri=True)
```

We can confirm that the pcdm resource parser works by retrieving this newly created resource:
```
In [6]: colors = repo.get_resource('colors')
DEBUG:pyfc4.models:GET request for http://localhost:8080/fcrepo/rest/colors/fcr:metadata, format text/turtle, headers {'Accept': 'text/turtle'}
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): localhost
DEBUG:urllib3.connectionpool:http://localhost:8080 "GET /fcrepo/rest/colors/fcr:metadata HTTP/1.1" 200 1688
DEBUG:pyfc4.models:custom resource type parser provided, attempting
DEBUG:pyfc4.plugins.pcdm:PCDM plugin, custom resource type parser firing
DEBUG:pyfc4.plugins.pcdm:found following rdf:types: [rdflib.term.URIRef('http://www.w3.org/ns/ldp#RDFSource'), rdflib.term.URIRef('http://www.w3.org/ns/ldp#Container'), rdflib.term.URIRef('http://pcdm.org/models#Collection'), rdflib.term.URIRef('http://fedora.info/definitions/v4/repository#Container'), rdflib.term.URIRef('http://fedora.info/definitions/v4/repository#Resource')]
DEBUG:pyfc4.models:using resource type: <class 'pyfc4.plugins.pcdm.models.PCDMCollection'>

In [7]: type(colors)
Out[7]: pyfc4.plugins.pcdm.models.PCDMCollection
```

Next, we can create some objects that will be part of this collection:
```
# create color objects
green = pcdm.models.PCDMObject(repo, 'green')
green.create(specify_uri=True)
yellow = pcdm.models.PCDMObject(repo, 'yellow')
yellow.create(specify_uri=True)
```

At this point we have the `/colors` collection, and the objects `/green` and `/yellow`.  To associate these objects with the collection as members, our end goal will be proxy objects for those resources in the collection's `/members` child container.  The PCDM plugin helps with this process:
```
colors.members.extend([green.uri, yellow.uri])
colors.update()
```

This creates proxy resources in `colors/members` that point to the resources `green` and `yellow`, regardless of where they live.  You can confirm by retrieving the colors resource again and observing the built-in attributes `.members`:
```
colors = repo.get_resource('colors')
In [13]: colors.members
Out[13]: 
[rdflib.term.URIRef('http://localhost:8080/fcrepo/rest/yellow'),
 rdflib.term.URIRef('http://localhost:8080/fcrepo/rest/green')]
```

We can confirm by observing the collection's entire RDF payload:
```
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

<http://localhost:8080/fcrepo/rest/colors> a fedora:Container,
        fedora:Resource,
        pcdm:Collection,
        ldp:Container,
        ldp:RDFSource ;
    fedora:created "2017-09-04T15:35:42.325000+00:00"^^xsd:dateTime ;
    fedora:createdBy "bypassAdmin" ;
    fedora:hasParent <http://localhost:8080/fcrepo/rest/> ;
    fedora:lastModified "2017-09-04T15:43:28.836000+00:00"^^xsd:dateTime ;
    fedora:lastModifiedBy "bypassAdmin" ;
    fedora:writable true ;
    pcdm:hasMember <http://localhost:8080/fcrepo/rest/green>,
        <http://localhost:8080/fcrepo/rest/yellow> ;
    ldp:contains <http://localhost:8080/fcrepo/rest/colors/members>,
        <http://localhost:8080/fcrepo/rest/colors/related> .
```

### Adding Binary Files
Binary files differ slightly in that the PCDM in LDP recommendations suggest they should live, not just a proxy object but the actual resource, in an object's `/files` child container.

So, at this point, the easiest approach is to create a `PCDMFile` resource directly in the object's `/files` directory (though it can be moved there later if necessary).

Example of creating a PCDMFile binary resource for the `green` resource:
```
# create spectrum binary as file for green
spectrum_green = pcdm.models.PCDMFile(repo, 'green/files/spectrum_green', binary_data='540nm', binary_mimetype='text/plain')
spectrum_green.create(specify_uri=True)
```

Re-retrieving the `green` object, we see that it now has this file included:
```
green = repo.get_resource('green')

In [16]: green.files
Out[16]: [rdflib.term.URIRef('http://localhost:8080/fcrepo/rest/green/files/spectrum_green')]
```

Like the normal pyfc4 NonRDFSource/Binary resources, this `spectrum_green` resource has a `.binary` namespace for accessing the binary file information itself:
```
# re-retrieve the spectrum_green resource
spectrum_green = repo.get_resource(green.files[0])

# observe .binary
In [19]: spectrum_green.binary.data
Out[19]: <Response [200]>

In [20]: spectrum_green.binary.data.content
Out[20]: b'540nm'

In [21]: spectrum_green.binary.mimetype
Out[21]: 'text/plain'
```

## Forthcoming

  * Look into the PCDM Works ontology, consider extending further to include FileSets and Works
  * confirm that `self.refresh()` will refresh all PCDM-important attributes such as `.members`, `.related`, `.files`, and `.associated` 