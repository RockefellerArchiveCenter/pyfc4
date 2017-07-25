# console / testing

from pyfc4.models import *

# instantiate repository
repo = Repository('http://localhost:8080/rest','ghukill','password', context={'foo':'http://foo.com'})

# create foo (basic container)
def create_bc():
	pass

# get foo
def get_bc():
	pass

# create foo/bar (basic container)
def create_child_bc():
	pass

# get foo/bar from foo.children()
def get_child_bc():
	pass

# create foo/baz (NonRDF / binary), from foo
def create_child_binary():
	pass

# get foo/baz
def get_child_binary():
	pass

# delete all three
def delete_test_resources():
	pass