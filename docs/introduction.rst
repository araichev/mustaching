Introduction
************
A Python 3.4+ package inspired by Mr. Money Mustache to summarize and plot personal finance data given in a CSV file.
Uses Pandas and Python-Highcharts to do most of the work.


Usage
=========
Play with the IPython notebook ``ipynb/examples.ipynb``.
You can do so online by clicking the Binder badge above.
You can even upload your own transaction data into the notebook, but consider first `Binder's warning about private data <http://docs.mybinder.org/faq>`_.

Your CSV of transactions should contain at least the following columns

- ``'date'``: string; something consistent and recognizable by Pandas, e.g 2016-11-26
- ``'amount'``: float; amount of transaction; positive or negative, indicating a credit or debit, respectively
- ``'description'`` (optional): string; description of transaction, e.g. 'dandelion and burdock tea'
- ``'category'`` (optional): string; categorization of description, e.g. 'healthcare' 
- ``'comment'`` (optional): string; comment on transaction, e.g. 'a gram of prevention is worth 16 grams of cure'


Notes
========
- Development status: Alpha
- This project uses semantic versioning (major.minor.micro), where each breaking feature or API change is considered a major change


Authors
========
- Alex Raichev, 2016-11


