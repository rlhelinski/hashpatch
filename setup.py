import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "hashpatch",
    version = "0.1",
    author = "Ryan Helinski",
    author_email = "rlhelinski@gmail.com",
    description = ("A Python module to update a remote copy, rearrange files "
            "to a new structure, and delete duplicates, using simple sha1sum "
            "files as storage"),
    license = "BSD",
    keywords = "checksum file duplicate synchronize",
    url = "https://github.com/rlhelinski/hashpatch",
    py_modules=['progressbar', 'hashpatch'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPLv2 License",
    ],
)
