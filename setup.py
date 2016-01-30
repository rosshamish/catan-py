from distutils.core import setup

with open("README.md", "r") as fp:
    long_description = fp.read()

version = {'__version__': '0.1.6'}
# with open('version.py', 'r') as fp:
#     exec(fp.read(), version)

setup(name="catan",
      version=version['__version__'],
      author="Ross Anderson",
      author_email="ross.anderson@ualberta.ca",
      url="https://github.com/rosshamish/catan-py/",
      download_url = 'https://github.com/rosshamish/catan-py/tarball/' + version['__version__'],
      description="models for representing and manipulating a game of catan",
      long_description=long_description,
      keywords=[],
      classifiers=[],
      license="GPLv3",

      packages=["catan"],
      install_requires=[
          'hexgrid',
          'catanlog',
          'undoredo',
      ],
	)

