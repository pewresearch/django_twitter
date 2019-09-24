import os
from setuptools import setup, find_packages

with open(
    os.path.join(os.path.dirname(__file__), "django_twitter", "VERSION"), "rb"
) as version_file:
    __version__ = str(version_file.read()).strip()

with open(os.path.join(os.path.dirname(__file__), "README.md"), "rb") as readme:
    README = str(readme.read())

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open("requirements.txt") as reqs:
    install_requires = [
        line
        for line in reqs.read().split("\n")
        if line and not line.startswith(("--", "git+ssh"))
    ]
    dependency_links = [
        line
        for line in reqs.read().split("\n")
        if line and line.startswith(("--", "git+ssh"))
    ]

setup(
    name="django_twitter",
    version=__version__,
    description="twitter models for django projects",
    long_description=README,  # 'http://labs.pewresearch.tech/docs/libs/django_twitter',
    url="https://github.com/pewresearch/django_twitter",
    author="Pew Research Center",
    author_email="admin@pewresearch.tech",
    install_requires=install_requires,
    dependency_links=dependency_links,
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    include_package_data=True,
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        #        'Development Status :: 1 - Planning',
        #        'Development Status :: 2 - Pre-Alpha',
        "Development Status :: 3 - Alpha",
        #        'Development Status :: 4 - Beta',
        #        'Development Status :: 5 - Production/Stable',
        #        'Development Status :: 6 - Mature',
        #        'Development Status :: 7 - Inactive'
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
    ],
    keywords="pew pew pew",
    license="MIT",
)
