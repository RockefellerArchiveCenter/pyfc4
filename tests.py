# console / testing

from pyfc4.models import *

# instantiate repository
repo = Repository('http://localhost:8080/rest','ghukill','password', context={'foo':'http://foo.com'})

# create foo (basic container)
def create_bc():
	foo = BasicContainer(repo, 'foo')
	foo.create()
	return foo.exists()

# get foo via repo.get_resource()
def get_bc():
	foo = repo.get_resource('foo')
	return foo.exists()

# create foo/bar (basic container)
def create_child_bc():
	bar = BasicContainer(repo, 'foo/bar')
	return bar.exists()

# get foo/bar from foo.children()
def get_child_bc():
	bar = repo.get_resource('foo/bar')
	return bar.exists()

# create foo/baz (NonRDF / binary), from foo
def create_child_binary():
	baz = BasicContainer(repo, 'foo/bar')

# get foo/baz
def get_child_binary():
	pass

# delete all three
def delete_test_resources():
	for uri in ['foo','foo/bar','foo/baz']:
		resource = repo.get_resource(uri)
		resource.delete(remove_tombstone=True)


def run_all_tests():
	create_bc()
	get_bc()
	create_child_bc()
	get_child_bc()
	create_child_binary()
	get_child_binary()
	delete_test_resources()