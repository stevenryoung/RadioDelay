from setuptools import setup

reqs = ["pyaudio>=0.2.9"]

setup(
    name="radiodelay",
    version="0.2.0-dev",
    description="Tool for delaying radio to sync to television broadcast.",
    url="https://github.com/stevenryoung/RadioDelay",
    author="Steven R. Young",
    license="GPLv3",
    packages=["radiodelay"],
    zip_safe=False,
    install_requires=reqs,
    package_data={"radiodelay": ["*.ini"]},
)
