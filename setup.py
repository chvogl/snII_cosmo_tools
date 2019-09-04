from setuptools import setup, find_packages

setup(
    name='snII_cosmo_tools',
    url='https://github.com/chvogl/snII_cosmo_tools.git',
    author='Christian Vogl',
    author_email='cvogl@mpa-garching.mpg.de',
    packages=find_packages(),
    package_data={'snII_cosmo_tools': ['templates/*.html']}
)
