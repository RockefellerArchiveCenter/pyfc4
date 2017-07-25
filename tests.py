# console / testing

from pyfc4.models import *

# instantiate repository
repo = Repository('http://localhost:8080/rest','ghukill','password', context={'foo':'http://foo.com'})

# get foo
foo = repo.get_resource('foo')

# create basic container

# create NonRDF node

# delete both