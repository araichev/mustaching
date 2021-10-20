import pytest
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
    t = create_transactions("2017-01-01", "2017-12-31")
    s = summarize(t, freq="QS", decimals=None)

    assert set(s.keys()) == {
        "by_none",
        "by_period",
        "by_category",
        "by_category_and_period",
    }

    assert set(s["by_none"].columns) == {
        "start_date",
        "end_date",
        "income",
        "expense",
        "balance",
        "savings_pc",
    }

    assert set(s["by_period"].columns) == {
        "date",
        "income",
        "expense",
        "balance",
        "savings_pc",
        "cumulative_income",
        "cumulative_balance",
        "cumulative_savings_pc",
    }

    assert set(s["by_category"].columns) == {
        "category",
        "income",
        "expense",
        "balance",
        "income_to_total_income_pc",
        "expense_to_total_income_pc",
        "expense_to_total_expense_pc",
        "daily_avg_balance",
        "weekly_avg_balance",
        "monthly_avg_balance",
        "yearly_avg_balance",
    }
    assert s["by_category"].income_to_total_income_pc.sum() == pytest.approx(100)
    assert s["by_category"].expense_to_total_expense_pc.sum() == pytest.approx(100)

    assert set(s["by_category_and_period"].columns) == {
        "date",
        "category",
        "income",
        "expense",
        "balance",
        "income_to_period_income_pc",
        "expense_to_period_income_pc",
        "expense_to_period_expense_pc",
    }
    for __, group in s["by_category_and_period"].groupby("date"):
        assert group.income_to_period_income_pc.sum() == pytest.approx(100)
        assert group.expense_to_period_expense_pc.sum() == pytest.approx(100)

    # Unused categories should by dropped
    s = summarize(t.iloc[-2:])
    assert s["by_category"].category.cat.categories.size == s["by_category"].category.nunique()

    s = summarize(t.drop(["category"], axis="columns"))
    assert s["by_category"].empty
    assert s["by_category_and_period"].empty


def test_plot():
    t = create_transactions("2017-01-01", "2017-12-31")

    summary = summarize(t, freq="MS")
    p = plot(summary, currency="$")
    assert set(p.keys()) == {"by_category", "by_category_and_period"}

    summary = summarize(t.drop("category", axis="columns"), freq="MS")
    p = plot(summary, currency="$")
    assert set(p.keys()) == {"by_none", "by_period"}
