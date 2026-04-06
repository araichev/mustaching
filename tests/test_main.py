import pandas as pd
import pandera as pa
import pytest

from .context import mustaching
from mustaching import main as m


def _sample_transactions():
    f = pd.DataFrame(
        {
            "date": [
                "2025-04-01",
                "2025-04-02",
                "2025-05-01",
                "2025-05-03",
                "2025-06-15",
                "2025-06-20",
                "2025-07-01",
                "2025-07-02",
                "2025-08-01",
                "2025-08-02",
                "2025-09-01",
                "2025-09-03",
            ],
            "amount": [100, -40, 200, -60, 50, -20, 120, -30, 80, -50, 140, -70],
            "description": [f"tx-{i}" for i in range(12)],
            "category": [
                "salary",
                "food",
                "salary",
                "rent",
                "investing",
                "food",
                "salary",
                "food",
                "investing",
                "rent",
                "salary",
                "rent",
            ],
            "comment": [None] * 12,
        }
    )
    f["date"] = pd.to_datetime(f["date"])
    f["category"] = pd.Categorical(
        f["category"],
        categories=["salary", "food", "rent", "investing", "unused"],
    )
    return f


def test_create_transactions():
    t = m.create_transactions("2016-12-01", "2017-03-01")

    assert isinstance(t, pd.DataFrame)
    assert set(t.columns) == {"date", "amount", "description", "category", "comment"}
    assert isinstance(t["date"].iat[0], pd.Timestamp)
    assert str(t["category"].dtype) == "category"
    assert t["date"].is_monotonic_increasing


def test_validate_transactions():
    valid = pd.DataFrame(
        {
            "date": ["2020-12-31"],
            "amount": [69],
        }
    )
    m.validate_transactions(valid)

    missing_date = pd.DataFrame(
        {
            "Date": ["2020-12-31"],
            "amount": [69],
        }
    )
    with pytest.raises(pa.errors.SchemaError):
        m.validate_transactions(missing_date)

    wrong_date_type = pd.DataFrame(
        {
            "date": [2020],
            "amount": [69],
        }
    )
    with pytest.raises(pa.errors.SchemaError):
        m.validate_transactions(wrong_date_type)


def test_insert_repeating():
    t = m.create_transactions("2017-01-01", "2017-03-01")
    desc = "oh no!"

    f = m.insert_repeating(t, -100, "MS", desc)

    assert f.shape[0] == t.shape[0] + 3
    assert f["amount"].sum() == t["amount"].sum() - 300
    assert str(f["category"].dtype) == "category"
    assert (f.loc[f["description"] == desc, "amount"] == -100).all()


def test_summarize():
    t = _sample_transactions()

    # Structure and percentage checks
    s = m.summarize(
        t,
        freq="QS",
        decimals=None,
        start_date="2025-04-01",
        end_date="2025-09-30",
    )

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
    for _, group in s["by_category_and_period"].groupby("date"):
        assert group.income_to_period_income_pc.sum() == pytest.approx(100)
        assert group.expense_to_period_expense_pc.sum() == pytest.approx(100)

    # Unused categories should be dropped
    s_subset = m.summarize(t.iloc[:2], decimals=None)
    assert (
        s_subset["by_category"].category.cat.categories.size
        == s_subset["by_category"].category.nunique()
    )

    # Missing category column should produce empty category summaries
    s_no_category = m.summarize(t.drop(["category"], axis="columns"), decimals=None)
    assert s_no_category["by_category"].empty
    assert s_no_category["by_category_and_period"].empty

    # Month-end frequencies should be labeled at month end, not previous month end
    s_me = m.summarize(
        t,
        freq="ME",
        decimals=None,
        start_date="2025-04-01",
        end_date="2025-09-30",
    )
    assert s_me["by_period"]["date"].iat[0] == pd.Timestamp("2025-04-30")
    assert s_me["by_period"]["date"].is_monotonic_increasing


def test_plot():
    t = _sample_transactions()

    # Category-aware plots
    summary = m.summarize(
        t,
        freq="ME",
        decimals=None,
        start_date="2025-04-01",
        end_date="2025-06-30",
    )
    p = m.plot(summary, currency="$")
    assert set(p.keys()) == {"by_category", "by_category_and_period"}

    # Sparse category/period combinations should still render in chronological order
    expected_dates = [
        "2025-04-30",
        "2025-04-30",
        "2025-05-31",
        "2025-05-31",
        "2025-06-30",
        "2025-06-30",
    ]
    for trace in p["by_category_and_period"].data[:-1]:
        assert list(trace.x[0]) == expected_dates

    # No-category plots
    summary = m.summarize(t.drop("category", axis="columns"), freq="MS")
    p = m.plot(summary, currency="$")
    assert set(p.keys()) == {"by_none", "by_period"}
