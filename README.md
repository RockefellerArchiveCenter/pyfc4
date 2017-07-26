# pyfc4

Python 3.x client for Fedora Commons 4.x

## Requirements

  * Python 3.x

## ToDo

### Resource instantiation

  * passing `data`, `headers` when instantiating
    * that way, can instantiate from multiple angles (raw class or request response)
  * should include a placeholder for raw response as well, something like `raw_response`

### Structures

  * Indirect and Direct Containers (basic is quasi-understood and implemented)

### API HTTP verbs

Helpful: [RESTful HTTP API - Containers](https://wiki.duraspace.org/display/FEDORA40/RESTful+HTTP+API+-+Containers)

  * `GET`  Retrieve the content of the resource
  * `POST` Create new resources within a LDP container
  * `PATCH`  Modify the triples associated with a resource with SPARQL-Update
  * `OPTIONS` Outputs information about the supported HTTP methods, etc.
  * `MOVE`  Move a resource (and its subtree) to a new location
  * `COPY` Copy a resource (and its subtree) to a new location

### Performance

#### Caching / Sessions

Currently, there are no sessions or caching.  So for a method like `.children()`, it would require pinging the repo again to sniff out the `ldp:contains` triples.  Granted, this will soon be parsed on resource loading, what about updates?  Should there be a `self.refresh()` method?
