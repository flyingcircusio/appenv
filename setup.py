# This should be only one line. If it must be multi-line, indent the second
# line onwards to keep the PKG-INFO file format intact.
"""Self-contained bootstrapping/updating of Python applications deployed
through shared repositories.
"""

from setuptools import setup, find_packages


setup(
    name='appenv',
    version='0.1',
    author='Christian Theune',
    author_email='ct@flyingcircus.io',
    license='BSD (3-clause)',
    url='https://github.com/flyingcircusio/appenv/',
    keywords='deployment',
    classifiers="""\
License :: OSI Approved :: BSD License
Programming Language :: Python
Programming Language :: Python :: 3
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3 :: Only
"""[:-1].split('\n'),
    description=__doc__.strip(),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=True,
    python_requires='>=3.6',
)
