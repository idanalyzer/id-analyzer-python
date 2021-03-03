from setuptools import setup, find_packages

VERSION = '1.0.0'
DESCRIPTION = 'ID Analyzer API client library, scan and verify global passport, driver license and identification card.'


with open('README.md', 'r') as file:
    LONG_DESCRIPTION = file.read()

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="idanalyzer",
    version=VERSION,
    author="ID Analyzer",
    author_email="<support@idanalyzer.com>",
    url="https://www.idanalyzer.com",
    license="MIT",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=['requests'],
    keywords=['id card', 'driver license', 'passport', 'id verification', 'identification card', 'identity document', 'mrz', 'pdf417', 'aamva'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Telecommunications Industry"
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
        "Operating System :: OS Independent",
    ]
)