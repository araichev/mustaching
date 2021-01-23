from itertools import product

import pytest
import highcharts
import pandera as pa

from .context import mustaching
from mustaching import *


def test_create_transactions():
    t = create_transactions("2016-12-01", "2017-03-01")
    assert isinstance(t, pd.DataFrame)
    assert set(t.columns) == {"date", "amount", "description", "category", "comment"}
    assert isinstance(t["date"].iat[0], pd.Timestamp)


def test_validate_transactions():
    f = pd.DataFrame({
        "date": ["2020-12-31"],
        "amount": [69],
    })
    validate_transactions(f)

    f = pd.DataFrame({
        "Date": ["2020-12-31"],
        "amount": [69],
    })
    with pytest.raises(pa.errors.SchemaError):
        validate_transactions(f)

    f = pd.DataFrame({
        "date": [2020],
        "amount": [69],
    })
    with pytest.raises(pa.errors.SchemaError):
        validate_transactions(f)

def test_insert_repeating():
    t = create_transactions("2017-01-01", "2017-03-01")
    desc = "oh no!"
    f = insert_repeating(t, -100, "MS", desc)
    assert f.shape[0] == t.shape[0] + 3
    assert f["amount"].sum() == t["amount"].sum() - 300
    assert f["category"].dtype == "category"


def test_summarize():
    default_cols = [
        "date",
        "income",
        "expense",
        "balance",
        "savings_pc_for_period",
        "spending_pc_for_period",
    ]
    avg_cols = ["daily_avg", "weekly_avg", "monthly_avg", "yearly_avg"]
    cat_cols = [
        "category",
        "spending_pc_for_period_and_category",
        "income_pc_for_period_and_category",
        "expense_pc_for_period_and_category",
    ]

    t = create_transactions("2017-01-01", "2017-12-31")
    s = summarize(t)
    expect_cols = default_cols + avg_cols
    assert set(s.columns) == set(expect_cols)
    assert s.shape[0] == 1

    s = summarize(t, freq="MS")
    expect_cols = default_cols
    assert set(s.columns) == set(expect_cols)
    assert s.shape[0] == 12

    s = summarize(t, by_category=True, decimals=None)
    expect_cols = default_cols + avg_cols + cat_cols
    assert set(s.columns) == set(expect_cols)
    ncats = t.category.nunique()
    assert s.shape[0] == ncats
    assert s["spending_pc_for_period_and_category"].sum() == pytest.approx(
        s["spending_pc_for_period"].iat[0]
    )

    # Unused categories should by dropped
    s = summarize(t.iloc[-2:], by_category=True)
    assert s.category.cat.categories.size == s.category.nunique()

    s = summarize(t, freq="MS", by_category=True, decimals=None)
    expect_cols = default_cols + cat_cols
    assert set(s.columns) == set(expect_cols)
    assert s.shape[0] == ncats * 12
    for __, group in s.groupby("date"):
        assert group["spending_pc_for_period_and_category"].sum() == pytest.approx(
            group["spending_pc_for_period"].iat[0]
        )


def test_get_colors():
    n = 300
    c = get_colors("income", n)
    assert len(c) == n
    assert len(set(c)) == 6


def test_plot():
    t = create_transactions("2017-01-01", "2017-12-31")
    for freq, by_category in product([None, "W"], [True, False]):
        s = summarize(t, freq=freq, by_category=by_category)
        p = plot(s)
        assert isinstance(p, highcharts.highcharts.highcharts.Highchart)
