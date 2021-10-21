import random
import itertools as it

import pandas as pd
import pandera as pa
import numpy as np
import plotly.graph_objects as pg
import textwrap as tw


def create_transactions(
    date1: str,
    date2: str,
    freq: str="12H",
    income_categories: list[str]=None,
    expense_categories: list[str]=None,
) -> pd.DataFrame:
    """
    Create a DataFrame of sample transactions between the given dates
    (date strings that Pandas can interpret, such as YYYYMMDD) and at
    the given Pandas frequency.
    The columns will be all those readable by the function :func:`read_transactions`.
    Each positive transaction will be assigned a income category from
    the given list ``income_categories``, and each negative transaction
    will be assigned a expense category from the given list
    ``expense_categories``.
    If these lists are not given, then whimsical default ones will be
    created.
    """
    # Create date range
    rng = pd.date_range(date1, date2, freq=freq, name="date")
    n = len(rng)

    # Create random amounts
    low = -70
    high = 100
    f = pd.DataFrame(
        np.random.randint(low, high, size=(n, 1)), columns=["amount"], index=rng
    )
    f = f.reset_index()

    # Create random descriptions and comments
    f["description"] = [hex(random.getrandbits(20)) for i in range(n)]
    f["comment"] = [hex(random.getrandbits(40)) for i in range(n)]

    # Categorize amounts
    if income_categories is None:
        income_categories = ["programming", "programming", "investing", "reiki"]
    if expense_categories is None:
        expense_categories = [
            "food",
            "shelter",
            "shelter",
            "transport",
            "healthcare",
            "soil testing",
        ]

    def categorize(x):
        if x > 0:
            return random.choice(income_categories)
        else:
            return random.choice(expense_categories)

    f["category"] = f["amount"].map(categorize)
    f["category"] = f["category"].astype("category")

    return f


SCHEMA = pa.DataFrameSchema({
    "date": pa.Column(pa.String),
    "amount": pa.Column(pa.Float, coerce=True),
    "description": pa.Column(pa.String, required=False, coerce=True),
    "category": pa.Column(pa.String, required=False, coerce=True),
    "comment": pa.Column(pa.String, required=False, coerce=True, nullable=True),
})

def validate_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Raise a Pandera SchemaError if the given DataFrame of transactions does not
    agree with the schema :const:SCHEMA.
    Otherwise, return the DataFrame as is.
    """
    return SCHEMA.validate(transactions)


def read_transactions(path: str, date_format: str=None, **kwargs) -> pd.DataFrame:
    """
    Read a CSV file of transactions located at the given path (string
    or Path object), parse the date and category, and return the
    resulting DataFrame.

    The CSV should contain at least the following columns

    - ``'date'``: string
    - ``'amount'``: float; amount of transaction; positive or negative,
      indicating a income or expense, respectively
    - ``'description'`` (optional): string; description of transaction,
      e.g. 'dandelion and burdock tea'
    - ``'category'`` (optional): string; categorization of description,
      e.g. 'healthcare'
    - ``'comment'`` (optional): string; comment on transaction, e.g.
      'a gram of prevention is worth 62.5 grams of cure'

    If the date format string ``date_format`` is given,  e.g
    ``'%Y-%m-%d'``, then parse dates using that format; otherwise use
    let Pandas guess the date format.
    """
    f = (
        pd.read_csv(path, **kwargs)
        .rename(lambda x: x.strip().lower(), axis="columns")
        .filter(["date", "amount", "description", "category", "comment"])
        .pipe(validate_transactions)
    )

    # Parse some
    f["date"] = pd.to_datetime(f["date"], format=date_format)
    if "category" in f.columns:
        f["category"] = f["category"].str.lower()
        f["category"] = f["category"].astype("category")

    return f.sort_values(["date", "amount"])


def insert_repeating(
    transactions: pd.DataFrame,
    amount: float,
    freq: str,
    description: str=None,
    category: str=None,
    comment: str=None,
    start_date: str=None,
    end_date: str=None,
) -> pd.DataFrame:
    """
    Given a DataFrame of transactions, add to it a repeating transaction
    at the given frequency for the given amount with the given optional
    description, category, and comment.
    Restrict the repeating transaction to the given start and end dates
    (date objects), inclusive.
    If no start date is given, then repeat from the first transaction date.
    If no end date is given, then repeat to the last transaction date.
    Drop duplicate rows and return the resulting DataFrame.
    """
    f = transactions.copy()
    if start_date is None:
        start_date = f["date"].min()
    if end_date is None:
        end_date = f["date"].max()

    g = pd.DataFrame([])
    dates = pd.date_range(start_date, end_date, freq=freq)
    g["date"] = dates
    g["amount"] = amount

    if description is not None:
        g["description"] = description
    if category is not None:
        g["category"] = category
        g["category"] = g["category"].astype("category")
    if comment is not None:
        g["comment"] = comment

    h = pd.concat([f, g]).drop_duplicates().sort_values(["date", "amount"])
    if "category" in h.columns:
        h["category"] = h["category"].astype("category")

    return h


def summarize(
    transactions: pd.DataFrame,
    freq: str="MS",
    decimals: int=2,
    start_date: str=None,
    end_date: str=None,
) -> dict:
    """
    Given a DataFrame of transactions, slice it from the given start
    date to and including the given end date date (strings that Pandas
    can interpret, such as YYYYMMDD) if specified, drop unused categories,
    and return a dictionary with the keys 'by_none', 'by_period', 'by_category',
    'by_category_and_period' whose corresponding values are DataFrames with the
    following columns.

    - key "by_none"
        * ``"start_date"``: first transaction date
        * ``"end_date"``: last transaction date
        * ``"income"``: sum of positive transaction amounts for the date range
        * ``"expense"``: absolute value of sum of negative transaction amounts for the
          date range
        * ``"balance"``: income - expense
        * ``"savings_pc"``: 100 * balance / income

    - key "by_period"
        * ``"date"``: date of period after date range has been resampled at
          frequency ``freq``
        * ``"income"``: sum of positive transaction amounts for the period
        * ``"expense"``: absolute value of sum of negative transactions for the period
        * ``"balance"``: income - expense for the period
        * ``"savings_pc``: 100 * balance / income
        * ``"cumulative_income"``: income plus the incomes of all previous periods
        * ``"cumulative_balance"``: balance plus the balances of all previous periods
        * ``"cumulative_savings_pc"``: 100 * cumulative_balance / cumulative_income

    - key "by_category"
        * ``"category"``: category of transactions
        * ``"income"``: sum of positive transaction amounts for the category and
          date range
        * ``"expense"``: absolute value of sum of negative transaction amounts for the
          category and date range
        * ``"balance"``: income - expense
        * ``"income_to_total_income_pc"``: 100 * income / (total income for date range)
        * ``"expense_to_total_income_pc"``: 100 * expense / (total income for date range)
        * ``"expense_to_total_expense_pc"``: 100 * expense / (total expense for date range)
        * ``"daily_avg_balance"``: sum of all amounts for category divided by the number
          of days in the date range
        * ``"weekly_avg_balance"``: sum of all amounts for category divided by the number
          of weeks in the date range
        * ``"monthly_avg_balance"``: sum of all amounts for category divided by the number
          of months in the date range
        * ``"yearly_avg_balance"``: sum of all amounts for category divided by the number
          of years in the date range

    - key "by_category_and_period"
        * ``"date"``: date of period after date range has been resampled at
          frequency ``freq``
        * ``"category"``: category of transactions
        * ``"income"``: sum of positive transaction amounts for the period and category
        * ``"expense"``: absolute value of sum of negative transactions for the period
          and category
        * ``"balance"``: income - expense for the period and category
        * ``"income_to_period_income_pc"``: 100 * income / (total income for period)
        * ``"expense_to_period_income_pc"``: 100 * expense / (total income for period)
        * ``"expense_to_period_expense_pc"``: 100 * expense / (total expense for period)

    Round all values to the given number of decimals, or set ``decimals=None`` to avoid rounding.
    """
    f = transactions.copy()

    # Filter to start and end dates
    if start_date is None:
        start_date = f["date"].min()
    else:
        start_date = pd.to_datetime(start_date)
    if end_date is None:
        end_date = f["date"].max()
    else:
        end_date = pd.to_datetime(end_date)

    f = f.loc[lambda x: (x.date >= start_date) & (x.date <= end_date)].copy()

    if "category" in f.columns:
        has_category = True
        # Removed unused categories
        f.category = f.category.cat.remove_unused_categories()
    else:
        has_category = False



    # Create income and expense columns
    f["income"] = f.amount.map(lambda x: x if x > 0 else 0)
    f["expense"] = f.amount.map(lambda x: -x if x < 0 else 0)
    f["balance"] = f.income - f.expense
    f = f.filter(["date", "category", "income", "expense", "balance"])

    # Count some dates
    delta = end_date - start_date
    num_days = delta.days + 1
    num_weeks = num_days / 7
    num_months = num_days / (365 / 12)
    num_years = num_days / 365

    result = {}

    # By none
    result["by_none"] = (
        f
        .assign(
            start_date=start_date,
            end_date=end_date,
        )
        .groupby(["start_date", "end_date"])
        .sum()
        .reset_index()
        .assign(
            savings_pc=lambda x: 100 * x.balance / x.income,
        )
    )
    total = result["by_none"].to_dict("records")[0]

    # By period
    period = pd.Grouper(freq=freq, label="left", closed="left")
    result["by_period"] = (
        f
        .set_index("date")
        .groupby(period)
        .sum()
        .reset_index()
        .assign(
            savings_pc=lambda x: 100 * x.balance / x.income,
            cumulative_income=lambda x: x.income.cumsum(),
            cumulative_balance=lambda x: x.balance.cumsum(),
            cumulative_savings_pc=lambda x: 100 * x.cumulative_balance / x.cumulative_income,
        )
    )

    # By category
    if has_category:
        result["by_category"] = (
            f
            .groupby("category")
            .sum()
            .reset_index()
            .assign(
                income_to_total_income_pc=lambda x: 100 * x.income / total["income"],
                expense_to_total_income_pc=lambda x: 100 * x.expense / total["income"],
                expense_to_total_expense_pc=lambda x: 100 * x.expense / total["expense"],
                daily_avg_balance=lambda x: x.balance / num_days,
                weekly_avg_balance=lambda x: x.balance / num_weeks,
                monthly_avg_balance=lambda x: x.balance / num_months,
                yearly_avg_balance=lambda x: x.balance / num_years,
            )
        )
    else:
        result["by_category"] = pd.DataFrame()

    # By period and category
    if has_category:
        result["by_category_and_period"] = (
            f
            .set_index("date")
            .groupby([period, "category"])
            .sum()
            .reset_index()
            # Merge in period totals
            .merge(
                result["by_period"]
                .filter(["date", "income", "expense"])
                .rename(columns={
                    "income": "period_income",
                    "expense": "period_expense",
                })
            )
            # Compute period-category percentages
            .assign(
                income_to_period_income_pc=lambda x: 100 * x.income / x.period_income,
                expense_to_period_income_pc=lambda x: 100 * x.expense / x.period_income,
                expense_to_period_expense_pc=lambda x: 100 * x.expense / x.period_expense,
            )
            .drop(["period_income", "period_expense"], axis="columns")
        )
    else:
        result["by_category_and_period"] = pd.DataFrame()

    if decimals is not None:
        new_result = {}
        for k, v in result.items():
            new_result[k] = v.round(decimals)
        result = new_result

    return result


def make_title(summary: pd.DataFrame, header: str=None, currency: str=None) -> str:
    """
    Helper function for :func:`plot`.
    Given a summary of the form output by the function :func:`summarize`,
    return a string with the given header and currency and a summary basic
    summary of transactions, which acts as a title for plot.
    """
    g = summary["by_none"]
    if currency == "$":
        # Workaround a Plotly dollar sign bug;
        # see https://stackoverflow.com/questions/40753033/plotly-js-using-two-dollar-signs-in-a-title-without-latex
        currency = "&#36;"

    return tw.dedent(
        f"""
        <b>{header}</b>
        <br>{g.start_date.iat[0]:%Y-%m-%d} to {g.end_date.iat[0]:%Y-%m-%d}
        <br>income = {g.income.iat[0]:,.0f}{currency} ·
        expense = {g.expense.iat[0]:,.0f}{currency} ·
        balance = {g.balance.iat[0]:,.0f}{currency} ·
        savings pc = {g.savings_pc.iat[0]:.1f}%
        """
    )


def interleave(a: list, b: list) -> list:
    """
    Given two lists a_0, a_1,...,b_n and b_0, b_1,...,b_n of length n,
    return the interleaved list a_0, b_0, a_1, b_1,...,a_n, b_n of length 2n.
    """
    return list(it.chain(*zip(a, b)))


def _plot_by_none(
    summary: pd.DataFrame,
    currency: str=None,
    height: int=None,
) -> dict:

    """
    Helper function for :func:`plot`.
    """
    f = summary["by_none"].copy()

    if currency is None:
        currency = ""

    hovertemplate = (
        "<b>%{meta}</b><br>"
        "%{y:,.0f}" + currency + "<br><extra></extra>"
    )

    # Make bars for income and expense
    traces = [
        pg.Bar(
            y=f.income,
            name="income",
            meta="income",
            marker_color="#636efa",
            hovertemplate=hovertemplate,
        ),
        pg.Bar(
            y=f.expense,
            name="expense",
            meta="expense",
            marker_color="#ef553b",
            hovertemplate=hovertemplate,
        ),
    ]

    layout = dict(
        title=make_title(summary, "Summary by none", currency),
        xaxis=dict(title="", showticklabels=False),
        yaxis=dict(separatethousands=True, title="value", ticksuffix=currency),
        legend_title_text="",
        legend_traceorder="normal",
        template="plotly_white",
        height=height,
        barmode="group",
        uniformtext_minsize=8,
        uniformtext_mode='hide',
    )
    fig = pg.Figure(data=traces, layout=layout)

    return fig


def _plot_by_category(
    summary: pd.DataFrame,
    currency: str=None,
    height: int=None,
) -> dict:

    """
    Helper function for :func:`plot`.
    """
    if summary["by_category"].empty:
        return pg.Figure()

    f = summary["by_category"].copy()

    if currency is None:
        currency = ""

    hovertemplate = (
        "<b>%{meta}</b><br>"
        "%{y:,.0f}" + currency + "<br>" +
        "%{x}<extra></extra>"
    )

    # Make stacked bars for income and expense
    traces = [
        pg.Bar(
            x=["income", "expense"],
            y=interleave(g.income, g.expense),
            name=category,
            meta=category,
            hovertemplate=hovertemplate,
            text=pd.Series(interleave(
                g.income_to_total_income_pc,
                g.expense_to_total_expense_pc,
            )).map(lambda x: f"{x:.0f}%"),
            textposition="inside",
        )
        for category, g in f.groupby("category")
    ]

    layout = dict(
        title=make_title(summary, "Summary by category", currency),
        xaxis=dict(title=""),
        yaxis=dict(separatethousands=True, title="value", ticksuffix=currency),
        legend_title_text="",
        legend_traceorder="normal",
        template="plotly_white",
        height=height,
        barmode="stack",
        uniformtext_minsize=8,
        uniformtext_mode='hide',
    )
    fig = pg.Figure(data=traces, layout=layout)

    return fig

def _plot_by_period(
    summary: pd.DataFrame,
    currency: str=None,
    height: int=None,
) -> dict:
    """
    Helper function for :func:`plot`.
    """
    if currency is None:
        currency = ""

    hovertemplate = (
        "<b>%{meta}</b><br>"
        "%{y:,.0f}" + currency + "<br>" +
        "%{x}<extra></extra>"
    )

    f = summary["by_period"].copy()
    traces = [
        pg.Bar(
            x=f.date,
            y=f.income,
            name="income",
            meta="income",
            marker_color="#636efa",
            hovertemplate=hovertemplate,
        ),
        pg.Bar(
            x=f.date,
            y=f.expense,
            name="expense",
            meta="expense",
            marker_color="#ef553b",
            hovertemplate=hovertemplate,
        ),
        pg.Scatter(
            x=f.date,
            y=f.cumulative_balance,
            name="cumulative balance",
            meta="cumulative balance",
            line_color="black",
            hovertemplate=hovertemplate,
        )
    ]

    layout = dict(
        title=make_title(summary, "Summary by period", currency),
        xaxis=dict(title="period", tickformat="%Y-%m-%d", ticklabelmode="period"),
        yaxis=dict(separatethousands=True, title="value", ticksuffix=currency),
        legend_title_text="",
        template="plotly_white",
        height=height,
    )
    fig = pg.Figure(data=traces, layout=layout)

    if f.date.nunique() < 20:
        fig.update_xaxes(
            tickvals=f.date.map(lambda x: x.strftime("%Y-%m-%d")).unique().tolist()
        )

    return fig


def _plot_by_category_and_period(
    summary: pd.DataFrame,
    currency: str=None,
    height: int=None,
) -> dict:
    """
    Helper function for :func:`plot`.
    Use multi-category x-axis for this plot as a workaround to Plotly's lack
    of support for grouped and stacked bar charts.
    """
    if summary["by_category"].empty:
        return pg.Figure()

    f1 = summary["by_category_and_period"].copy()
    f0 = summary["by_period"].copy()

    if currency is None:
        currency = ""

    hovertemplate = (
        "<b>%{meta}</b><br>"
        "%{y:,.0f}" + currency + "<br>" +
        "%{x}<extra></extra>"
    )

    # Make stacked bars for income and expense grouped by date
    f1["date"] = f1.date.map(lambda x: x.strftime("%Y-%m-%d"))
    n = f1.date.nunique()
    traces = [
        pg.Bar(
            x=[
                interleave(g.date, g.date),
                ["income", "expense"]*n,
            ],
            y=interleave(g.income, g.expense),
            name=category,
            meta=category,
            hovertemplate=hovertemplate,
            text=pd.Series(interleave(
                g.income_to_period_income_pc,
                g.expense_to_period_expense_pc,
            )).map(lambda x: f"{x:.0f}%"),
            textposition="inside",
        )
        for category, g in f1.groupby("category")
    ]
    # Make line plot of cumulative balance;
    # hack it to match the x-axis of the stacked bars
    f0 = summary["by_period"].copy()
    f0["date"] = f0.date.map(lambda x: x.strftime("%Y-%m-%d"))
    traces.append(
        pg.Scatter(
            x=[interleave(f0.date, f0.date), ["income", "expense"]*n],
            y=interleave([np.nan for __ in f0.cumulative_balance], f0.cumulative_balance),
            name="cumulative balance",
            meta="cumulative balance",
            line_color="black",
            hovertemplate=hovertemplate,
            connectgaps=True,
        )
    )

    # Set layout
    if n > 10:
        width = 100*n
    else:
        width = None

    layout = dict(
        title=make_title(summary, "Summary by category and period", currency),
        xaxis=dict(title="period"),
        yaxis=dict(separatethousands=True, title="value", ticksuffix=currency),
        legend_title_text="",
        legend_traceorder="normal",
        template="plotly_white",
        width=width,
        height=height,
        barmode="stack",
        uniformtext_minsize=8,
        uniformtext_mode='hide',
    )
    fig = pg.Figure(data=traces, layout=layout)

    return fig

def plot(summary: pd.DataFrame, currency: str=None, height: int=None) -> dict:
    if summary["by_category"].empty:
        result = {
            "by_none": _plot_by_none(summary, currency, height),
            "by_period": _plot_by_period(summary, currency, height),
        }
    else:
        result = {
            "by_category": _plot_by_category(summary, currency, height),
            "by_category_and_period": _plot_by_category_and_period(summary, currency, height),
        }
    return result