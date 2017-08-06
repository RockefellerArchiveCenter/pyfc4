## Performance

pyfc4, for many operations, will be slower than a raw HTTP request to Fedora's API.  However, where it occassionaly lags in raw  performance for basic operations, it can facilitate common patterns and resource preparing and editing in ways that may make up for this.

Additionally, there are some flags and options for using pyfc4 in ways to approach the speed and simplicity of Fedora's API.

### Resource updating and RDF parsing

One way in which pyfc4 can be considerably slower, is **creating** or **updating** a number of objects.  This is because each time pyfc4 creates or updates a resource, it issues a follow-up `GET` request for the newly created, or modified, resource information.

However, to mitigate this, one can run methods like `resource.create` and `resource.update` with an optional flag `auto_refresh=False` that will prevent pyfc4 from running `resource.refresh` that updates the resource metadata.  This can dramatically improve performance:

![selection_075](https://user-images.githubusercontent.com/1753087/28998479-36c0b32a-79fa-11e7-8023-45435317c7c6.png)

And often, refreshing a resource's information is unnecessary when building or updating them programatically, as, by that point, you're likely fairly confident the results of actions.  That being true, even without running `resource.refresh`, the response headers from creation or update an object will confirm if the operation was successful.

### Object-like Triples

One of the more fun and handy corners of pyfc4 is parsing of triples from `self.rdf.graph` into a dot notation, object-like format for accessing.  An example:

```
# ldp:contains for a resource
In [5]: foo.rdf.triples.ldp.contains
Out[5]: 
[rdflib.term.URIRef('http://localhost:8080/rest/foo/bar'),
 rdflib.term.URIRef('http://localhost:8080/rest/foo/baz')]

# all triples, even recently modified, show up here
In [6]: foo.add_triple(foo.rdf.prefixes.foaf.knows, 'http://localhost:8080/rest/foo/baz')

In [7]: foo.rdf.triples.foaf.knows
Out[7]: [rdflib.term.Literal('http://localhost:8080/rest/foo/baz', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#string'))]
```

This triple accessing is not meant to usurp the normal graph navigation of `for s,p,o in graph`, or any of the other `rdflib` graph methods like `graph.triples`, `graph.objects`, etc.  But it can be handy shorthand for oft used predicates/relationships like `ldp:contains` or `rdf:type`.  

However, no good deed goes unpunished.  Because this object-like requires looping through a resource's graph for triples, it would require update everytime a triple is added or removed.  Over numerous iterations, either multipe changes to a single resource, or numerous changes to multiple resources, this can add up, as you can see from the graph:

![selection_076](https://user-images.githubusercontent.com/1753087/29002957-bc3cecfe-7a7b-11e7-9ad3-8e8a3fa6aee9.png)

Similar to optionally refreshing a resource after creation or update, you can pass the optional flag `auto_refresh=False` for `self.add_triple`, `self.set_triple`, or `self.remove_triple` to prevent this follow-up graph parsing.

### Sessions / Caching

Currently not implemented.
