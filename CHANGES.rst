Changes
========
3.1.3, 2021-01-23
-----------------
- Used Pandera for data validation.
- Tweaked chart colors.


3.1.2, 2020-09-06
-----------------
- Upgraded to Python 3.8.


3.1.1, 2019-04-03
------------------
- Switched to Poetry.
- Published docs using publish-sphinx-docs.
- Published on PyPi.
- Dropped unused categories in ``summarize()``.


3.1.0, 2018-03-31
------------------
- Changed the columns output by the function ``summarize``


3.0.0, 2018-01-01
------------------
- Renamed the function ``build_sample_transactions`` to ``create_transactions``
- Added more columns to the output of the function ``summarize``
- Switched from using 'credit' and 'debit' to 'income' and 'expense', because i find that clearer


2.2.1, 2017-10-14
------------------
- In function ``summarize``, changed weekly and daily averages calculations to use credit - debit. Also changed default sort order of DataFrame output.


2.2.0, 2017-09-25
------------------
- Changed function ``summarize`` to split savings rate by category and to include weekly and daily averages when no frequency is given
- Fixed an edge-case division-by-zero bug in function ``summarize``


2.1.0, 2017-05-07
------------------
- Fixed a bug in function ``insert_repeating`` that lost the categorical dtype
- Added optional slicing by date in function ``summarize``


2.0.1, 2017-04-26
-------------------
- Fixed the bug where ``setup.py`` could not find the license file


2.0.0, 2017-04-25
-----------------
- Removed ``budget_and_freq`` option, because i don't need that extra complexity
- Calculated spending rate
- Added function ``insert_repeating`` to avoid having to record repeating transactions in my personal spendings
- Prepared for PyPi


1.2.1, 2017-03-01
-----------------
- Fixed README and ``ipynb/examples.ipynb``


1.2.0, 2017-03-01
------------------
- Lowercased category names and values when reading transactions
- Added percentages to bar chart stacks when splitting by categories
- Sorted categories from highest to lowest values in bar chart stacks
- Changed name to 'mustaching' and restructured directories
- Wrote automated tests


1.1.0, 2016-12-13
------------------
- Made function ``read_ransactions`` infer column names a little
- Made funnction ``summarize`` always create ``'period_budget'`` column and fill it with NaNs if no budget given


1.0.0, 2016-12-10
------------------
- Changed summary columns to ``'credit'``, ``'expense'``, and ``'balance'``
- Plotted balance as a cumulative sum line series


0.1.1, 2016-11-21
------------------
Fixed date labels and off-by-1-day error in time grouping


0.1.0, 2016-11-18
------------------
First release
