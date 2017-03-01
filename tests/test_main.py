import datetime as dt

import pytest

from .context import mustaching
from mustaching import *


def test_build_sample_transactions():
	t = build_sample_transactions('2016-12-01', '2017-03-01')
	assert isinstance(t, pd.DataFrame)
	assert set(t.columns) == COLUMNS
	assert isinstance(t['date'].iat[0], pd.tslib.Timestamp)

def test_find_colums():
	f = pd.DataFrame(columns=['Amount', 'DATE', 'credity'])
	get = find_columns(f)
	expect = {'amount': 'Amount', 'date': 'DATE'}
	assert get == expect

def test_get_duration():
	date = dt.date(2017, 1, 1)

	x = get_duration(date, 'MS')
	assert x.days == 31

	x = get_duration(date, 'M')
	assert x.days == 28

	x = get_duration(date, 'W')
	assert x.days == 7

	x = get_duration(date, 'A')
	assert x.days == 365

def test_summarize():
	t = build_sample_transactions('2017-01-01', '2017-12-31')

	s = summarize(t)
	default_cols = ['date', 'credit', 'debit', 'balance', 'period_savings_rate']
	assert set(s.columns) == set(default_cols)
	assert s.shape[0] == 1

	s = summarize(t, freq='MS')
	assert set(s.columns) == set(default_cols)
	assert s.shape[0] == 12

	s = summarize(t, by_category=True)
	cat_cols = default_cols + ['category']
	assert set(s.columns) == set(cat_cols)
	ncats = t.category.nunique()
	assert s.shape[0] == ncats

	s = summarize(t, budget_and_freq=(100, 'W'))
	budget_cols = default_cols + ['period_budget']
	assert set(s.columns) == set(budget_cols)
	assert s.shape[0] == 1
	assert s['period_budget'].iat[0] == 100*365/7

	s = summarize(t, freq='MS', by_category=True)
	assert set(s.columns) == set(cat_cols)
	assert s.shape[0] == ncats*12

	s = summarize(t, freq='MS', budget_and_freq=(100, 'W'))
	assert set(s.columns) == set(budget_cols)
	assert s.shape[0] == 12
	assert s['period_budget'].iat[0] == 100*(31/7)

	s = summarize(t, by_category=True, budget_and_freq=(100, 'W'))
	assert set(s.columns) == set(budget_cols + cat_cols)
	assert s.shape[0] == ncats
	assert s['period_budget'].iat[0] == 100*(365/7)

	s = summarize(t, freq='MS', by_category=True, budget_and_freq=(100, 'W'))
	assert set(s.columns) == set(budget_cols + cat_cols)
	assert s.shape[0] == 12*ncats
	assert s['period_budget'].iat[0] == 100*(31/7)

def test_get_colors():
	n = 300
	c = get_colors('credit', n)
	assert len(c) == n
	assert len(set(c)) == 6

	with pytest.raises(ValueError):
		c = get_colors('bingo', n)
