# pyfc4

![Travis Build](https://travis-ci.org/ghukill/pyfc4.svg?branch=master "Travis Build")

Python client for Fedora Commons 4.

## Requirements

  * Python 3.5+
  * [Fedora Commons 4.7+]((http://fedorarepository.org/))

## Installation

```
pip install -e .
```

## Tests

Copy `tests/localsettings.py.template` to `tests/localsettings.py` and edit to point at your instance of Fedora.

Then run:
```
./runtests.sh
```

## Documentation

See [docs](docs) folder

## Acknowledgements

pyfc4 is the product of some years working with Fedora Commons 3.x, and participating in, and learning from, the greater Fedora Commons community.  Projects like [Eulfedora](https://github.com/emory-libraries/eulfedora) out of Emory University have been instrumental for inspiration and design.  Larger ecosystems like [Islandora](https://islandora.ca/) and [Samvera](https://samvera.org/) have also been invaluable for observing patterns of usage and architecture.  Big credit and thanks to these projects and communities for sharing their insight and code.