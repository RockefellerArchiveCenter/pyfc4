# console

from pyfc4.models import *

# logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug('''
#######################################################################
pyfc4 convenience console.  All resources are belong to you.
#######################################################################\
''')

# instantiate repository
repo = Repository('http://localhost:8080/rest','username','password', context={'foo':'http://foo.com'})

