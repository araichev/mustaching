"""
CONVENTIONS:
    - A data frame of *transactions* is one with the following columns:
        * date: Numpy datetime
        * amount: float
        * description (optional): string
        * category (optional): Pandas 'category' 
        * comment (optional): string

TODO:
    - In tooltip, eliminate total if only one series in stack
"""
import random

import pandas as pd
import numpy as np
import colorlover as cl
from highcharts import Highchart


def create_sample_transactions(date1, date2, freq='12H', 
  income_categories=None, expense_categories=None):
    """
    Create a data frame of sample transactions (with all fields) between the given dates (date strings that Pandas can interpret) and at the given Pandas frequency.
    Each positive transaction will be assigned an income category from the given list ``income_categories``, and each negative transaction will be assigned an expense category from the given list ``expense_categories``.
    If these lists are not given, then whimsical default ones will be created.
    """
    # Create date range
    rng = pd.date_range(date1, date2, freq=freq, name='date')
    n = len(rng)

    # Create random amounts
    low = -100
    high = 100
    f = pd.DataFrame(np.random.randint(low, high, size=(n, 1)), 
      columns=['amount'], index=rng)
    f = f.reset_index()
    f['date'] = f['date'].map(lambda x: x.date())
    
    # Create random descriptions and comments
    f['description'] = [hex(random.getrandbits(20)) for i in range(n)]
    f['comment'] = [hex(random.getrandbits(40)) for i in range(n)]

    # Categorize amounts
    if income_categories is None:
        income_categories = ['yoga', 'reiki', 'thieving']
    if expense_categories is None:
        expense_categories = ['food', 'housing', 'transport', 'healthcare', 'soil testing']

    def categorize(x):
        if x > 0:
            return random.choice(income_categories)
        else:
            return random.choice(expense_categories)

    f['category'] = f['amount'].map(categorize)
    
    return f

def read_transactions(path, **kwargs):
    """
    Read a CSV file of transactions located at the given path (string or Path object), parse the date and category, and return the resulting data frame.
    Uses ``pandas.read_csv`` with the given extra keywords arguments.

    The CSV should contain at least the following columns

    - ``'date'``: string; something consistent and recognizable by Pandas, e.g 2016-11-26
    - ``'amount'``: float; amount of transaction; positive or negative, indicating a credit or debit, respectively
    - ``'description'`` (optional): string; description of transaction, e.g. 'dandelion and burdock tea'
    - ``'category'`` (optional): string; categorization of description, e.g. 'healthcare' 
    - ``'comment'`` (optional): string; comment on transaction, e.g. 'a gram of prevention is worth 62.5 grams of cure'

    """
    return pd.read_csv(path, parse_dates=['date'], 
      dtype={'category': 'category'}, **kwargs)

def get_duration(date, freq):
    """
    Return the duration of the period starting at the given date and spanning the given frequency.
    
    NOTES:
        Could not find a Pandas function to do this for me.
    """
    dr = pd.date_range(date, freq=freq, periods=2)
    return dr[1] - dr[0]

def summarize(transactions, freq='M', budget_and_freq=None, by_category=False,
  decimals=None):
    """
    Given a data frame of transactions, return a data frame with the columns:
    
    - ``'income'``: sum of positive amounts for the period
    - ``'expense'``: absolute value of the sum of the negative amounts for the period
    - ``'saving'``: income - expense

    where the period is the given Pandas frequency ``freq``.

    If ``by_category``, then group by the ``'category'`` column of ``transactions`` in addition to the period.

    If ``budget_and_freq`` is given as a pair (budget amount, budget period as a Pandas frequency), then include an extra column:

    - ``'period_budget'``: budget scaled to the given period ``freq``

    Round all values to the given number of decimals.
    """
    f = transactions.copy()
    f['income'] = f['amount'].map(lambda x: x if x > 0 else 0)
    f['expense'] = f['amount'].map(lambda x: -x if x < 0 else 0)
    f['saving'] = f['income'] - f['expense']    
    keep_cols = ['date', 'income', 'expense', 'saving']

    if by_category:
        if 'category' not in f.columns:
            raise ValueError('category column missing from data frame')
        
        f = f.set_index('date').groupby([pd.TimeGrouper(freq, label='left'), 'category']
          ).sum().fillna(0).reset_index()
        keep_cols.append('category')
    else:
        f = f.set_index('date').resample(freq, label='left'
          ).sum().fillna(0).reset_index()
    if budget_and_freq is not None:
        b, bfreq = budget_and_freq
        f['num_budget_periods'] = f['date'].map(
          lambda x: get_duration(x, freq)/get_duration(x, bfreq))
        f['period_budget'] = f['num_budget_periods']*b
        keep_cols.append('period_budget')
        
    f = f[keep_cols]
    
    if decimals is not None:
        f = f.round(decimals)
            
    return f

def get_colors(column_name, n):
    """
    Return a list of ``n`` (positive integer) nice RGB color strings to use for color coding the given column (string; one of ``['income', 'expense', 'period_budget', 'saving']``.

    NOTES:
        - Returns at most 9 distinct colors. Repeats color beyond that.
        - Helper function for :func:`plot`.  
    """
    VALID_COLUMN_NAMES = ['income', 'expense', 'period_budget', 'saving']
    if column_name not in VALID_COLUMN_NAMES:
        raise ValueError('Column name must be one of {!s}'.format(VALID_COLUMN_NAMES))

    # Clip n to range or sequential-type colors
    low = 3
    high = 9
    k = np.clip(n, low, high) 
    kk = str(k)

    # Build colors in clipped range
    if column_name == 'income':
        colors = cl.scales[kk]['seq']['GnBu'][::-1]
    elif column_name == 'expense':
        colors = cl.scales[kk]['seq']['OrRd'][::-1]
    elif column_name == 'period_budget':
        colors = ['rgb(255, 255, 255)' for __ in range(k)]
    elif column_name == 'saving':
        colors = ['rgb(117,107,177)' for __ in range(k)]

    # Extend colors to unclipped range as required
    if n <= 0:
        colors = []
    elif 0 < n < low:
        colors = colors[:n]
    elif n > high:
        # Repeat colors
        q, r = divmod(n, k)
        colors = colors*q + colors[:r]

    return colors

def plot(summary, currency=None):
    """
    Plot the given transaction summary (output of :func:`summarize`) using Python HighCharts.
    Include the given currency units (string; e.g. 'NZD') in the plot labels.
    """
    f = summary.copy()
    chart = Highchart()

    if currency is None:
        y_text = 'Money'
    else:
        y_text = 'Money ({!s})'.format(currency)
    
    options = {
        'chart': {
            'width': 600,
            'height': 400,
        },
        'title': {
            'text': 'Account Summary'
        },
        'xAxis': {
            'type': 'datetime',
            'labels': {
                'format': '{value:%Y-%m-%d}',
                'rotation': -45,
                'align': 'right',
            },
        },
        'yAxis': {
            'title': {
                'text': y_text,
            }
        },
        'tooltip': {
            'headerFormat': '<b>{point.key:%Y-%m-%d}</b> ' +
              '(period start)<table>',
            'pointFormat': '<tr><td style="padding-right:1em">' +
              '{series.name}</td>' +
              '<td style="text-align:right">{point.y:.0f} ' + 
              currency + '</td></tr>',
            'useHTML': True,
        },
        'plotOptions': {
            'column': {
                'pointPadding': 0,
                'borderWidth': 1,
                'borderColor': '#333333',
            }
        },
        'credits': {
                'enabled': False,
            },
    }
    if 'category' in f.columns:
        options['plotOptions']['column']['stacking'] = 'normal'
        options['tooltip']['footerFormat'] =\
          '<tr><td style="padding-right:1em">'\
          'Total</td><td style="text-align:right">{point.total:.0f} ' +\
          currency + '</td></tr></table>'
        options['tooltip']['shared'] = False

        # Split income and expense into different stacks split by category
        for column in ['income', 'expense']:
            cond1 = f[column] > 0
            categories = f.loc[cond1, 'category'].unique()
            n = len(categories)
            colors = get_colors(column, n)
            for category, color in zip(categories, colors):
                cond2 = cond1 & (f['category'] == category)
                g = f[cond2].copy()
                name = '{!s} {!s}'.format(column.capitalize(), category)
                opts = {'name': name, 'stack': column, 'color': color}
                chart.add_data_set(g[['date', column]].values.tolist(), 'column', **opts)
        
        def my_agg(group):
            d = {}
            d['period_budget'] = group['period_budget'].iat[0]
            d['saving'] = group['saving'].sum()
            return pd.Series(d)
        
        g = f.groupby('date').apply(my_agg).reset_index()
        columns = ['period_budget', 'saving']
        for column in columns:
            name = column.split('_')[-1].capitalize()
            color = get_colors(column, 1)[0]
            opts = {'name': name, 'color': color, 'stack': column}
            if column == 'saving':
                opts['visible'] = False
            chart.add_data_set(g[['date', column]].values.tolist(), 'column', **opts) 
            
    else:
        options['tooltip']['footerFormat'] = '</table>'
        options['tooltip']['shared'] = True
        columns = ['income', 'expense', 'period_budget', 'saving']
        for column in columns:
            name = column.split('_')[-1].capitalize()
            color = get_colors(column, 1)[0]
            opts = {'color': color, 'name': name}
            if column == 'saving':
                opts['visible'] = False
            chart.add_data_set(f[['date', column]].values.tolist(), 'column', **opts) 

    chart.set_dict_options(options)

    return chart