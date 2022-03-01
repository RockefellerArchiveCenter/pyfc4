from setuptools import setup

setup(name='pyfc4',
      version='0.7',
      description='Python 3 client for Fedora Commons 4',
      url='http://github.com/ghukill/pyfc4',
      author='Graham Hukill',
      author_email='ghukill@gmail.com',
      license='MIT License',
      install_requires=[
        'pytest',
        'pytest-cov',
        'rdflib',
        'requests'
      ],
      classifiers = [
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
      ],
      packages=['pyfc4', 'pyfc4.plugins', 'pyfc4.plugins.pcdm'],
      zip_safe=False)
