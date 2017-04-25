from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='mustaching',
    version='2.0.0',
    author='Alex Raichev',
    url='https://github.com/araichev/mustaching',
    license=license,
    description='A Python 3.4+ package for Mr. Money Mustaching',
    long_description=readme,
    install_requires=[
        'pandas>=0.19',
        'python-highcharts>=0.3.1',
    ],
    packages=find_packages(exclude=('tests', 'docs')),   
)

