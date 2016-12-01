Budgeting
***********

.. image:: http://mybinder.org/badge.svg 
    :target: http://mybinder.org:/repo/araichev/budgeting


Some Python 3.4+ code for slicing, dicing, and plotting a CSV of personal finance data.
Uses Pandas and Python-Highcharts to do most of the work.


Examples
=========
Play with the IPython notebook ``examples.ipynb``.
You can do so online by clicking the Binder badge above.
You can even upload your own transaction data into the notebook, but consider first `Binder's warning about private data <http://docs.mybinder.org/faq>`_.

Your CSV of transactions should contain at least the following columns

- ``'date'``: string; something consistent and recognizable by Pandas, e.g 2016-11-26
- ``'amount'``: float; amount of transaction; positive or negative, indicating a credit or debit, respectively
- ``'description'`` (optional): string; description of transaction, e.g. 'dandelion and burdock tea'
- ``'category'`` (optional): string; categorization of description, e.g. 'healthcare' 
- ``'comment'`` (optional): string; comment on transaction, e.g. 'a gram of prevention is worth 16 grams of cure'


Authors
========
- Alex Raichev, 2016-11
