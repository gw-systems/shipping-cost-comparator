"""
Settings package for Courier Module.
Import environment-specific settings based on DJANGO_ENV variable.
"""

import os

# Determine which settings module to use
env = os.getenv('DJANGO_ENV', 'development')

if env == 'production':
    from .prod import *
elif env == 'development':
    from .dev import *
else:
    from .dev import *
