Mustaching
***********

.. image:: http://mybinder.org/badge.svg
    :target: http://mybinder.org:/repo/araichev/mustaching

.. image:: https://travis-ci.org/araichev/mustaching.svg?branch=master
    :target: https://travis-ci.org/araichev/mustaching

A tiny Python 3.4+ library inspired by Mr. Money Mustache to summarize and plot personal finance data given in a CSV file.
Uses Pandas and Python-Highcharts to do most of the work.

.. image:: mustaching.jpeg

.. image:: chart.png


Installation
=============
- Using Pipenv, do ``pipenv install git+https://github.com/araichev/mustaching#egg=mustaching``
- Alternatively, using Pip and a virtual environment, do ``pip install git+https://github.com/araichev/mustaching``


Usage
=========
Play with the IPython notebook at ``ipynb/examples.ipynb``.
You can even do so online by clicking the Binder badge above.
Using Binder you can also upload your own transaction data into the notebook, but consider first `Binder's warning about private data <http://docs.mybinder.org/faq>`_.

Your CSV of transactions should contain at least the following columns

- ``'date'``: string; something consistent and recognizable by Pandas, e.g 2016-11-26
- ``'amount'``: float; amount of transaction; positive or negative, indicating a credit or debit, respectively
- ``'description'`` (optional): string; description of transaction, e.g. 'dandelion and burdock tea'
- ``'category'`` (optional): string; categorization of description, e.g. 'healthcare'
- ``'comment'`` (optional): string; comment on transaction, e.g. 'a gram of prevention is worth 16 grams of cure'

The business logic can be found in ``mustaching/main.py``


Documentation
==============
In docs and `on RawGit <https://rawgit.com/araichev/mustaching/master/docs/_build/singlehtml/index.html>`_.


Notes
========
- Development status: Alpha
- This project uses semantic versioning


Authors
========
- Alex Raichev, 2016-11
