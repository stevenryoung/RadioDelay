from setuptools import setup

reqs = ['pyaudio>=0.2.9', 'python-gflags>=2.0.0', "six"] # six is actually a gflags requirement not currently in pypi reqs

setup(name='radiodelay',
      version='0.1.0',
      description='Tool for delaying radio to sync to television broadcast.',
      url='https://github.com/stevenryoung/RadioDelay',
      author='Steven R. Young',
      license='GPLv3',
      packages=['radiodelay'],
      zip_safe=False,
      install_requires=reqs,
      package_data={'radiodelay': ['*.ini']})
