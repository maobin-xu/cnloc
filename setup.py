# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="cnloc", 
    version="0.1.0", 
    description="Address Parser for Chinese Administrative Divisions", 
    long_description=open("README.md",encoding="utf-8").read(), 
    long_description_content_type="text/markdown",
    license="MIT", 

    author="Maobin Xu", 
    author_email="maobinxu@foxmail.com", 
    url="https://github.com/maobin-xu/cnloc", 

    packages=find_packages(),
    package_data={'cnloc': ['data/*.csv']},
    platforms="any",
    classifiers=[ 
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-3.0",
        "Operating System :: OS Independent",
        'Natural Language :: Chinese (Simplified)',
        'Topic :: Address Parsing :: Chinese Administrative Divisions',
    ],
    python_requires=">=3.6",
    install_requires=[
        "pandas",
        "ahocorasick",
    ],
)