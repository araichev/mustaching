"""
CONVENTIONS:
    - A data frame of *transactions* is one with the following columns:
        * date: Numpy datetime
        * amount: float
        * description (optional): string
        * category (optional): Pandas 'category' 
        * comment (optional): string

TODO:
    - In tooltip, remove stack total in balance series
    - In tooltip, remove stack total if only one series in stack
"""
import random

import pandas as pd
import numpy as np
import colorlover as cl
from highcharts import Highchart

COLUMNS = {'date', 'amount', 'description', 'category', 'comment'}
REQUIRED_COLUMNS = {'date', 'amount'}

def create_sample_transactions(date1, date2, freq='12H', 
  credit_categories=None, debit_categories=None):
    """
    Create a data frame of sample transactions (with all fields) between the given dates (date strings that Pandas can interpret) and at the given Pandas frequency.
    Each positive transaction will be assigned an credit category from the given list ``credit_categories``, and each negative transaction will be assigned an debit category from the given list ``debit_categories``.
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
    if credit_categories is None:
        credit_categories = ['yoga', 'reiki', 'thieving']
    if debit_categories is None:
        debit_categories = ['food', 'housing', 'transport', 'healthcare', 'soil testing']

    def categorize(x):
        if x > 0:
            return random.choice(credit_categories)
        else:
            return random.choice(debit_categories)

    f['category'] = f['amount'].map(categorize)
    
    return f

def find_columns(raw_transactions):
    """
    Given a data frame, try to find in it the columns that correspond those in ``COLUMNS``.
    Build a dictionary of this correspondance of the form
    key column name -> column name in given data frame.
    Return the resulting dictionary, which might be incomplete.
    """
    f = raw_transactions.copy()
    col_dict = {}
    for c in f.columns:
        for key in COLUMNS:
            if key in c.lower():
                col_dict[key] = c
    return col_dict

def read_transactions(path, date_format=None):
    """
    Read a CSV file of transactions located at the given path (string or Path object), parse the date and category, and return the resulting data frame.

    The CSV should contain at least the following columns

    - ``'date'``: string
    - ``'amount'``: float; amount of transaction; positive or negative, indicating a credit or debit, respectively
    - ``'description'`` (optional): string; description of transaction, e.g. 'dandelion and burdock tea'
    - ``'category'`` (optional): string; categorization of description, e.g. 'healthcare' 
    - ``'comment'`` (optional): string; comment on transaction, e.g. 'a gram of prevention is worth 62.5 grams of cure'

    If the date format string ``date_format`` is given,  e.g ``'%Y-%m-%d'``, then parse dates using that format; otherwise use let Pandas guess the date format.
    """
    f = pd.read_csv(path)
    col_dict = find_columns(f)
    if not set(col_dict.keys()) >= REQUIRED_COLUMNS:
        raise ValueError(
          'Could not find columns resembling {!s} in file'.format(
          REQUIRED_COLUMNS))
    
    # Reformat column names
    rename1 = {val: key for key, val in col_dict.items()}
    rename2 = {c: c.strip().lower().replace(' ', '_') for c in f.columns}
    f = f.rename(columns=rename1).rename(columns=rename2)
    
    # Parse some
    f['date'] = pd.to_datetime(f['date'], format=date_format)
    if 'category' in f.columns:
        f['category'] = f['category'].str.lower()
        f['category'] = f['category'].astype('category')

    return f

def get_duration(date, freq):
    """
    Return the duration of the period starting at the given date and spanning the given frequency.
    
    NOTES:
        Could not find a Pandas function to do this for me.
    """
    dr = pd.date_range(date, freq=freq, periods=2)
    return dr[1] - dr[0]

def summarize(transactions, freq=None, budget_and_freq=(np.nan, 'A'), 
  by_category=False, decimals=None):
    """
    Given a data frame of transactions, return a data frame with the columns:
    
    - ``'date'``: start date of period
    - ``'credit'``: sum of positive amounts for the period
    - ``'debit'``: absolute value of the sum of the negative amounts for the period
    - ``'balance'``: credit - debit cumulative sum
    - ``'savings_rate'``: (credit - debit)/credit
    - ``'period_budget'``: budget scaled to the given period ``freq``

    where the period is given by the Pandas frequency string ``freq``.
    If that frequency is ``None``, then there is only one period, namely the runs from the first to the last date in ``transactions`` (ordered (chronologically), and the ``'date'`` value is the first date.
    
    The ``budget_and_freq`` is a pair (budget amount, budget period as a Pandas frequency string).

    If ``by_category``, then group by the ``'category'`` column of ``transactions`` in addition to the period.

    Round all values to the given number of decimals.
    """
    f = transactions.copy()
    if by_category and 'category' not in f.columns:
        raise ValueError('category column missing from data frame')

    f['credit'] = f['amount'].map(lambda x: x if x > 0 else 0)
    f['debit'] = f['amount'].map(lambda x: -x if x < 0 else 0)

    if freq is None:
        if by_category:
            g = f.groupby('category').sum().reset_index()
            g['balance'] = g['credit'].sum() - g['debit'].sum()
            g['savings_rate'] = g['balance']/g['credit'].sum()
        else:
            g = {}
            g['credit'] = f['credit'].sum()
            g['debit'] = f['debit'].sum()
            g['balance'] = g['credit'] - g['debit']
            g['savings_rate'] = g['balance']/g['credit'].sum()
            g = pd.DataFrame(g, index=[0])

        b, bfreq = budget_and_freq
        d1, d2 = f['date'].min(), f['date'].max()
        k = (d2 - d1)/get_duration(d1, bfreq)
        g['period_budget'] = k*b 
        # Add in first transaction date
        g['date'] = f['date'].min()
    else:
        tg = pd.TimeGrouper(freq, label='left', closed='left')
        if by_category:
            cols = [tg, 'category']
            g = f.set_index('date').groupby(cols).sum().reset_index()
            balance = 0
            balances = []
            savings_rates = []
            for __, group in g.set_index('date').groupby(tg):
                n = group.shape[0]
                balance += (group['credit'] - group['debit']).sum()
                balances.extend([balance for i in range(n)])
                savings_rate =\
                  (group['credit'] - group['debit']).sum()/\
                  group['credit'].sum()
                savings_rates.extend([savings_rate for i in range(n)])
            g['balance'] = balances
            g['savings_rate'] = savings_rates
        else:
            g = f.set_index('date').groupby(tg).sum().reset_index()
            g['balance'] = (g['credit'] - g['debit']).cumsum()  
            g['savings_rate'] = (g['credit'] - g['debit'])/g['credit']

        b, bfreq = budget_and_freq
        g['num_budget_periods'] = g['date'].map(
          lambda x: get_duration(x, freq)/get_duration(x, bfreq))
        g['period_budget'] = g['num_budget_periods']*b

    if by_category:
        keep_cols = ['date', 'credit', 'debit', 'balance', 
          'savings_rate', 'category', 'period_budget']
    else:
        keep_cols = ['date', 'credit', 'debit', 'balance', 
          'savings_rate', 'period_budget']

    g = g[keep_cols].copy()
    
    if decimals is not None:
        g = g.round(decimals)
            
    return g

def get_colors(column_name, n):
    """
    Return a list of ``n`` (positive integer) nice RGB color strings to use for color coding the given column (string; one of ``['credit', 'debit', 'period_budget', 'balance']``.

    NOTES:
        - Returns at most 9 distinct colors. Repeats color beyond that.
        - Helper function for :func:`plot`.  
    """
    VALID_COLUMN_NAMES = ['credit', 'debit', 'period_budget', 'balance']
    if column_name not in VALID_COLUMN_NAMES:
        raise ValueError('Column name must be one of {!s}'.format(VALID_COLUMN_NAMES))

    # Clip n to range or sequential-type colors
    low = 3
    high = 6
    k = np.clip(n, low, high) 
    kk = str(k)

    # Build colors in clipped range
    if column_name == 'credit':
        colors = cl.scales[kk]['seq']['GnBu'][::-1]
    elif column_name == 'debit':
        colors = cl.scales[kk]['seq']['OrRd'][::-1]
    elif column_name == 'period_budget':
        colors = ['rgb(255, 255, 255)' for __ in range(k)]
    elif column_name == 'balance':
        colors = ['#555' for __ in range(k)]

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

def plot(summary, currency='', width=None, height=None):
    """
    Plot the given transaction summary (output of :func:`summarize`) using Python HighCharts.
    Include the given currency units (string; e.g. 'NZD') in the plot labels.
    """
    f = summary.copy()
    chart = Highchart()

    # HighCharts kludge: use categorical x-axis to display dates properly
    dates = f['date'].map(lambda x:x.strftime('%Y-%m-%d')).unique()
    dates = sorted(dates.tolist())

    if currency:
        y_text = 'Money ({!s})'.format(currency)
    else:
        y_text = 'Money'
    
    options = {
        'lang': {
            'thousandsSep': ','
        },
        'chart' : {},
        'title': {
            'text': 'Account Summary'
        },
        'xAxis': {
            'type': 'category',
            'categories': dates,
        },
        'yAxis': {
            'title': {
                'text': y_text,
            }
        },
        'tooltip': {
            'headerFormat': '<b>{point.key}</b><table>',
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

    if width is not None:
        options['chart']['width'] = width

    if height is not None:
        options['chart']['height'] = height

    if 'category' in f.columns:
        options['plotOptions']['column']['stacking'] = 'normal'
        options['tooltip']['pointFormat'] = '''
          <tr>
          <td style="padding-right:1em">{series.name}  
          ({point.percentage:.1f}%)</td>
          <td style="text-align:right">{point.y:,.0f}''' + currency +\
          '''
          </td>
          </tr>
          '''
        options['tooltip']['footerFormat'] = '''
          <tr>
          <td style="padding-right:1em">Total</td>
          <td style="text-align:right">{point.total:,.0f} ''' + currency +\
          '''
          </td>
          </tr></table>
          '''
        options['tooltip']['shared'] = False

        # Split credit and debit into two stacks, each split by category
        for column in ['credit', 'debit']:
            # Sort categories by greatest value to least
            g = f.groupby('category').sum().reset_index(
              ).sort_values(column, ascending=False)
            categories = g.loc[g[column] > 0, 'category'].unique()
            n = len(categories)
            colors = get_colors(column, n)
            cond1 = f[column] > 0
            for category, color in zip(categories, colors):
                cond2 = (cond1 | f[column].isnull()) &\
                  (f['category'] == category)
                g = f[cond2].copy()
                name = '{!s} {!s}'.format(column.capitalize(), category)
                opts = {'name': name, 'stack': column, 'color': color}
                chart.add_data_set(g[column].values.tolist(), 'column', **opts)
        
        def my_agg(group):
            d = {}
            d['period_budget'] = group['period_budget'].iat[0]
            d['balance'] = group['balance'].iat[0]
            return pd.Series(d)
        
        g = f.groupby('date').apply(my_agg).reset_index()
        if g['period_budget'].dropna().empty:
            columns = ['balance']
        else:
            columns = ['period_budget', 'balance']
        for column in columns:
            name = column.split('_')[-1].capitalize()
            color = get_colors(column, 1)[0]
            opts = {
              'name': name, 
              'color': color, 
              }
            if column == 'balance':
                opts['series_type'] = 'line'
            else:
                opts['series_type'] = 'column'
                opts['stack'] = column
            chart.add_data_set(g[column].values.tolist(), **opts) 
            
    else:
        options['tooltip']['pointFormat'] = '''
          <tr>
          <td style="padding-right:1em">{series.name}</td>
          <td style="text-align:right">{point.y:,.0f} ''' + currency +\
          '''
          </td>
          </tr>
          '''
        options['tooltip']['footerFormat'] = '</table>'
        options['tooltip']['shared'] = True
        if f['period_budget'].dropna().empty:
            columns = ['credit', 'debit', 'balance']
        else:
            columns = ['credit', 'debit', 'period_budget', 'balance']
        for column in columns:
            name = column.split('_')[-1].capitalize()
            color = get_colors(column, 1)[0]
            opts = {
              'color': color, 
              'name': name,
              }
            if column == 'balance':
                opts['series_type'] = 'line'
            else:
                opts['series_type'] = 'column'
            chart.add_data_set(f[column].values.tolist(), **opts) 

    chart.set_dict_options(options)

    return chart