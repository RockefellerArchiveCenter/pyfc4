from setuptools import setup

setup(name='pyfc4',
      version='0.1',
      description='Python 3 client for Fedora Commons 4',
      url='http://github.com/ghukill/pyfc4',
      author='Graham Hukill',
      author_email='ghukill@gmail.com',
      license='MIT License',
      install_requires=[
      	'pytest',
            'pytest-cov',
      	'rdflib',
      	'rdflib-jsonld',
      	'requests'
      ],
      packages=['pyfc4'],
      zip_safe=False)