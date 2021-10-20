Introduction
************
A tiny Python 3.9+ library inspired by Mr. Money Mustache to summarize and plot personal finance data given in a CSV file of transactions.
Uses Pandas and Plotly to do most of the work.

.. image:: _static/plot.png
    :width: 500px
    :alt: chart

Smacks of `plain text accounting <http://plaintextaccounting.org/>`_ but is limited to single-entry transactions and focuses only on income and expenses.
For full-featured double-entry bookkeeping in Python, use a different library, such as `beancount <https://bitbucket.org/blais/beancount/overview>`_.


Installation
=============
Create a Python 3.9+ virtual environment and run ``poetry add mustaching``.


Usage
=========
Play with the Jupyter notebook at ``notebooks/examples.ipynb``.
You can even do so online by clicking the Binder badge above.
Using Binder you can also upload your own transaction data into the notebook, but consider first `Binder's warning about private data <http://docs.mybinder.org/faq>`_.

Your CSV of transactions should contain at least the following columns

- ``'date'``: string; something consistent and recognizable by Pandas, e.g 2016-11-26
- ``'amount'``: float; amount of transaction; positive or negative, indicating an income or expense, respectively
- ``'description'`` (optional): string; description of transaction, e.g. 'dandelion and burdock tea'
- ``'category'`` (optional): string; categorization of description, e.g. 'healthcare'
- ``'comment'`` (optional): string; comment on transaction, e.g. 'a gram of prevention is worth 16 grams of cure'

The business logic can be found in ``mustaching/main.py``


Documentation
==============
At `raichev.net/mustaching_docs <https://raichev.net/mustaching_docs>`_.


Notes
========
- Development status: Alpha
- This project uses semantic versioning


Authors
========
- Alex Raichev, 2016-11

