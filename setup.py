from setuptools import setup, find_packages

setup(
  name = 'recast-control-center-prototype',
  version = '0.0.1',
  description = 'prototype web frontend for RECAST project at CERN',
  long_description = 'prototype web frontend for RECAST project at CERN. Provides users with options to request new RECAST requests, process them using a backend, and display results.',
  url = 'http://github.com/recast-hep/recast-frontend-prototype',
  author = 'Lukas Heinrich',
  author_email = 'lukas.heinrich@cern.ch',
  packages=find_packages(),
  install_requires = [
    'celery==3.1.20',
    'redis',
    'gevent==1.1b4',
    'gevent-socketio',
    'msgpack-python',
    'socket.io-emitter',
    'recast-api',
    'recast-backend',
    'recast-resultblueprints',
    'Flask',
    'Flask-SSO',
    'Click',
    'IPython'
  ],
  entry_points = {
    'console_scripts': [
      'recast-control-center = recastcontrolcenter.servercli:servercli',
      'recast-admin = recastcontrolcenter.admin.recastadmin:recastadmin'
    ]
  },
  include_package_data = True,
  zip_safe=False,
  dependency_links = [
    'https://github.com/ziyasal/socket.io-python-emitter/tarball/master#egg=socket.io-emitter-0.1.3',
    'https://github.com/recast-hep/recast-api/tarball/master#egg=recast-api-0.0.1',
    'https://github.com/recast-hep/recast-resultblueprints/tarball/master#egg=recast-resultblueprints-0.0.1',
    'https://github.com/recast-hep/recast-backend/tarball/master#egg=recast-backend-0.0.1',
  ]
)
