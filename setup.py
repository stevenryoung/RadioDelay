from setuptools import setup

reqs = ['pyaudio>=0.2.9']

setup(name='radiodelay',
      version='0.2.1',
      description='Tool for delaying radio to sync to television broadcast.',
      long_description='Tool for delaying radio to sync to television broadcast.',
      url='https://github.com/stevenryoung/RadioDelay',
      author='Steven R. Young',
      author_email="stevenryoung@gmail.com",
      license='GPLv3',
      packages=['radiodelay'],
      zip_safe=False,
      install_requires=reqs,
      package_data={'radiodelay': ['*.ini']})
