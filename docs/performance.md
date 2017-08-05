## Performance

pyfc4, for many operations, will be slower than a raw HTTP request to Fedora's API.  However, where it occassionaly lags in raw  performance for basic operations, it can facilitate common patterns and resource preparing and editing in ways that may make up for this.

Additionally, there are some flags and options for using pyfc4 in ways to approach the speed and simplicity of Fedora's API.

### Resource updating and RDF parsing

One way in which pyfc4 can be considerably slower, is **creating** or **updating** a number of objects.  This is because each time pyfc4 creates or updates a resource, it issues a follow-up `GET` request for the newly created, or modified, resource information.

However, to mitigate this, one can run methods like `resource.create` and `resource.update` with an optional flag `refresh=False` that will prevent pyfc4 from running `resource.refresh` that updates the resource metadata.  This can dramatically improve performance:

![selection_075](https://user-images.githubusercontent.com/1753087/28998479-36c0b32a-79fa-11e7-8023-45435317c7c6.png)

And often, refreshing a resource's information is unnecessary when building or updating them programatically, as, by that point, you're likely fairly confident the results of actions.  That being true, even without running `resource.refresh`, the response headers from creation or update an object will confirm if the operation was successful.

### Sessions / Caching

Currently not implemented.
