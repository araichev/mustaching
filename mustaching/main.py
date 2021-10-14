"""
CONVENTIONS:
    - A DataFrame of *transactions* is one with the following columns:
        * date: Numpy datetime
        * amount: float
        * description (optional): string
        * category (optional): Pandas 'category'
        * comment (optional): string
"""
import random
from typing import Dict

import pandas as pd
import pandera as pa
import numpy as np
import colorlover as cl
from highcharts import Highchart


def create_transactions(
    date1, date2, freq="12H", income_categories=None, expense_categories=None
):
    """
    Create a DataFrame of sample transactions between the given dates
    (date strings that Pandas can interpret, such as YYYYMMDD) and at
    the given Pandas frequency.
    Include all the columns in the set ``COLUMNS``.
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

def read_transactions(path, date_format=None, **kwargs):
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
    transactions,
    amount,
    freq,
    description=None,
    category=None,
    comment=None,
    start_date=None,
    end_date=None,
):
    """
    Given a DataFrame of transactions, add to it a repeating transaction
    at the given frequency for the given amount with the given optional
    description, category, and comment.
    Restrict the repeating transaction to the given start and end dates
    (date objects), inclusive, if given; otherwise repeat from the first
    transaction date to the last.
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
    transactions,
    freq="MS",
    decimals=2,
    start_date=None,
    end_date=None,
):
    """
    Given a DataFrame of transactions, slice it from the given start
    date to and including the given end date date (strings that Pandas
    can interpret, such as YYYYMMDD) if specified, and return a dictionary
    with the keys 'by_none', 'by_period', 'by_category', 'by_period_and_category'
    whose corresponding values are DataFrames with the following columns:

    ...

    Round all values to the given number of decimals.
    Set ``decimals=None`` to avoid rounding.
    """
    f = transactions.copy()
    if "category" in f.columns:
        has_category = True
        # Removed unused categories
        f.category = f.category.cat.remove_unused_categories()
    else:
        has_category = False

    # Set start and end dates
    if start_date is None:
        start_date = f["date"].min()
    else:
        start_date = pd.to_datetime(start_date)
    if end_date is None:
        end_date = f["date"].max()
    else:
        end_date = pd.to_datetime(end_date)

    # Filter to start and end dates
    f = f.loc[lambda x: (x.date >= start_date) & (x.date <= end_date)].copy()


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
        result["by_period_and_category"] = (
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
        result["by_period_and_category"] = pd.DataFrame()

    if decimals is not None:
        new_result = {}
        for k, v in result.items():
            new_result[k] = v.round(decimals)
        result = new_result

    return result


def get_colors(column_name, n):
    """
    Return a list of ``n`` (positive integer) nice RGB color strings
    to use for color coding the given column (string; one of
    ``['income', 'expense', 'period_budget', 'balance']``.

    NOTES:

    - Returns at most 6 distinct colors. Repeats color beyond that.
    - Helper function for :func:`plot`.
    """

    # Clip n to range or sequential-type colors
    low = 3
    high = 6
    k = np.clip(n, low, high)
    kk = str(k)

    # Build colors in clipped range
    if column_name == "income":
        colors = cl.scales[kk]["seq"]["GnBu"][::-1]
    elif column_name == "expense":
        colors = cl.scales[kk]["seq"]["OrRd"][::-1]
    else:
        colors = ["#555" for __ in range(k)]

    # Extend colors to unclipped range as required
    if n <= 0:
        colors = []
    elif 0 < n < low:
        colors = colors[:n]
    elif n > high:
        # Repeat colors
        q, r = divmod(n, k)
        colors = colors * q + colors[:r]

    return colors


# def plot(summary, currency=None, width=None, height=None):
#     """
#     Given a transaction summary of the form output by :func:`summarize`,
#     plot it using Python HighCharts.
#     Include the given currency units (string; e.g. 'NZD') in the y-axis
#     label.
#     Override the default chart width and height, if desired.
#     """
#     f = summary.copy()
#     chart = Highchart()

#     # Initialize chart options.
#     # HighCharts kludge: use categorical x-axis to display dates properly.
#     dates = f["date"].map(lambda x: x.strftime("%Y-%m-%d")).unique()
#     dates = sorted(dates.tolist())

#     if currency is not None:
#         y_text = "Money ({!s})".format(currency)
#     else:
#         currency = ""
#         y_text = "Money"

#     chart_opts = {
#         "lang": {"thousandsSep": ","},
#         "chart": {"zoomType": "xy"},
#         "title": {"text": "Account Summary"},
#         "xAxis": {"type": "category", "categories": dates},
#         "yAxis": {"title": {"text": y_text}, "reversedStacks": False},
#         "tooltip": {"headerFormat": "<b>{point.key}</b><table>", "useHTML": True},
#         "plotOptions": {
#             "column": {"pointPadding": 0, "borderWidth": 1, "borderColor": "#333333"}
#         },
#         "credits": {"enabled": False},
#     }

#     if width is not None:
#         chart_opts["chart"]["width"] = width

#     if height is not None:
#         chart_opts["chart"]["height"] = height

#     if "category" in f.columns:
#         # Update chart options
#         chart_opts["plotOptions"]["series"] = {"stacking": "normal"}
#         chart_opts["tooltip"]["pointFormat"] = (
#             """
#           <tr>
#           <td style="padding-right:1em">{series.name}
#           ({point.percentage:.0f}%)</td>
#           <td style="text-align:right">{point.y:,.0f} """
#             + currency
#             + """
#           </td>
#           </tr>
#           """
#         )
#         chart_opts["tooltip"]["footerFormat"] = (
#             """
#           <tr>
#           <td style="padding-right:1em">Stack total</td>
#           <td style="text-align:right">{point.total:,.0f} """
#             + currency
#             + """
#           </td>
#           </tr></table>
#           """
#         )
#         chart_opts["tooltip"]["shared"] = False

#         # Create data series.
#         # Split income and expense into two stacks, each split by category.
#         for column in ["income", "expense"]:
#             # Sort categories by greatest value to least
#             g = (
#                 f.groupby("category")
#                 .sum()
#                 .reset_index()
#                 .sort_values(column, ascending=False)
#             )
#             categories = g.loc[g[column] > 0, "category"].unique()
#             n = len(categories)
#             colors = get_colors(column, n)
#             cond1 = f[column] > 0
#             for category, color in zip(categories, colors):
#                 cond2 = (cond1 | f[column].isnull()) & (f["category"] == category)
#                 g = f[cond2].copy()
#                 name = "{!s} {!s}".format(column.capitalize(), category)
#                 series_opts = {
#                     "name": name,
#                     "color": color,
#                     "series_type": "column",
#                     "stack": column,
#                     "borderColor": "white",
#                 }
#                 chart.add_data_set(g[column].values.tolist(), **series_opts)

#         # Aggregate balance
#         def my_agg(group):
#             d = {}
#             d["balance"] = group["balance"].iat[0]
#             return pd.Series(d)

#         g = f.groupby("date")["balance"].first().reset_index()
#         series_opts = {
#             "name": "Balance",
#             "color": get_colors("balance", 1)[0],
#             "series_type": "line",
#             "borderColor": "white",
#         }
#         chart.add_data_set(g["balance"].values.tolist(), **series_opts)

#     else:
#         # Update chart options
#         chart_opts["tooltip"]["pointFormat"] = (
#             """
#           <tr>
#           <td style="padding-right:1em">{series.name}</td>
#           <td style="text-align:right">{point.y:,.0f} """
#             + currency
#             + """
#           </td>
#           </tr>
#           """
#         )
#         chart_opts["tooltip"]["footerFormat"] = "</table>"
#         chart_opts["tooltip"]["shared"] = True

#         # Create data series
#         for column in ["income", "expense", "balance"]:
#             series_opts = {
#                 "color": get_colors(column, 1)[0],
#                 "name": column.split("_")[-1].capitalize(),
#                 "series_type": "line" if column == "balance" else "column",
#                 "borderColor": "white",
#             }
#             chart.add_data_set(f[column].values.tolist(), **series_opts)

#     chart.set_dict_options(chart_opts)

#     return chart
