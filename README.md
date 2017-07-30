# pyfc4

Python 3.x client for [Fedora Commons 4.x](http://fedorarepository.org/)

![Travis Build](https://travis-ci.org/ghukill/pyfc4.svg?branch=master "Travis Build")

## Requirements

  * Python 3.x

## Installation

```
pip install -e .
```

## Tests

Requires `pyfc4` installed as module.

```
./runtests.sh
```

## Basic Usage

Assuming an instance of FC4 at `http://localhost:8080`

#### Instantiate repository handle
```
repo = Repository('http://localhost:8080/rest','username','password', context={'foo':'http://foo.com'})
```

#### Create Resources

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

Create [NonRDFSource](https://www.w3.org/TR/ldp/#ldpnr) (Binary) resource `foo/baz` under `foo`.  This opens the file `README.md` as the binary content, and sets the mimetype as `text/plain`:

```
baz = Binary(repo, 'foo/baz') # 'Binary' is alias for 'NonRDFSource' which also works
baz.binary.data = open('README.md','rb')
baz.binary.mimetype = 'text/plain'
baz.create(specify_uri=True)
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
foo.add_triple(foo.rdf.prefixes.dc.subject, 'minty')

# example of a foaf predicate, pointing to another resource
foo.add_triple(foo.rdf.prefixes.foaf.knows, bar.uri)
```

To commit these modifications to the resource's graph, use the method `.update`.  This sends the updated graph as a `PUT` request, then retrieves the updated graph and sets that to the resource instance.

```
foo.update()
```

Removing triples is similar to adding, passing a predicate and an object:

```
foo.remove_triple(foo.rdf.prefixes.dc.subject, 'minty')
foo.update()
```
