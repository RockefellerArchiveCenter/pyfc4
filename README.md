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

Resources also contain the method `check_exists` to ping the repository with a `HEAD` request and confirms, updating the attribute `.exists` in the process:

```
In [9]: foo.check_exists()
Out[9]: True
```
