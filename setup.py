from distutils.core import setup

from condent import __version__


with open("README.rst") as readme:
    long_description = readme.read()


classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.1",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]


setup(
    name="condent",
    version=__version__,
    py_modules=["condent"],
    scripts=["bin/condent"],
    author="Julian Berman",
    author_email="Julian@GrayVines.com",
    classifiers=classifiers,
    description="A simple reindent for containers that reindents as I like it",
    license="MIT/X",
    long_description=long_description,
    url="http://github.com/Julian/condent",
)
