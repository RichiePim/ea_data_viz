import plotly.express as px
import pandas as pd
from pandas.tseries.offsets import MonthEnd
import numpy as np
from dash import dcc
from dash import html
from dash import dash_table
from utils.plots.bar import Bar
from utils.subtitle import get_instructions
from utils.subtitle import get_data_source
from utils.plots.scatter import Scatter
from utils.plots.line import Line
import requests
from io import StringIO
from utils.get_data.open_phil import download_grants, process_grants, save_grants

op_grants = None
def get_op_grants():
    global op_grants
    if type(op_grants) != type(None):
        return op_grants

    try:
        # Try to get fresh data from the API and save it
        if save_grants():  # This will download, save, and return True if successful
            op_grants = pd.read_csv('./assets/data/openphil_grants.csv')
            op_grants = process_grants(op_grants)
            if op_grants is not None:
                return op_grants

        # Fallback to local file if API fails
        print("Falling back to local file...")
        op_grants = pd.read_csv('./assets/data/openphil_grants.csv')
        op_grants = process_grants(op_grants)
        
        return op_grants
    except Exception as e:
        print(f"Error loading Open Philanthropy data: {e}")
        return None


def org_bar_chart(op_grants):
    # Only aggregate numeric columns
    numeric_cols = op_grants.select_dtypes(include=[np.number]).columns
    op_orgs = op_grants.groupby(by='Organization Name')[numeric_cols].sum().reset_index()
    op_orgs = op_orgs.sort_values(by='Amount')
    op_orgs['x'] = op_orgs['Organization Name']
    op_orgs['y'] = op_orgs['Amount']
    op_orgs['text'] = op_orgs['Amount'].apply(lambda x: f'${x:,.0f}')

    def hover(row):
        org = row['Organization Name']
        amount = row['text']
        grants = row['grants'] if 'grants' in row else 'N/A'
        return f'<b>{org}</b><br>{grants} grants<br>{amount} total'
    op_orgs['hover'] = op_orgs.apply(hover, axis=1)

    op_orgs_truncated = op_orgs.reset_index().iloc[:20]

    return Bar(op_orgs_truncated, title='Top 20 Donee Organizations')


def cause_bar_chart(op_grants):
    # Only aggregate numeric columns
    numeric_cols = op_grants.select_dtypes(include=[np.number]).columns
    op_causes = op_grants.groupby(by='Focus Area')[numeric_cols].sum().reset_index()
    op_causes = op_causes.sort_values(by='Amount')
    op_causes['x'] = op_causes['Focus Area']
    op_causes['y'] = op_causes['Amount']
    op_causes['text'] = op_causes['Amount'].apply(lambda x: f'${x:,.0f}')

    def hover(row):
        area = row['Focus Area']
        amount = row['text']
        grants = row['grants'] if 'grants' in row else 'N/A'
        return f'<b>{area}</b><br>{grants} grants<br>{amount} total'
    op_causes['hover'] = op_causes.apply(hover, axis=1)

    height_per_bar = 25 if len(op_causes) > 10 else 28
    height = height_per_bar * len(op_causes) + 20
    return Bar(op_causes, height=height, title='Focus Areas')


def grants_scatter(op_grants):
    return Scatter(
        op_grants,
        x = "Date",
        y = "Amount",
        # color="Focus Area",
        # size='Amount',
        hover = 'hover',
        log_y = True,
        title = 'Individual Grants (log)',
        y_title = 'Amount (USD)',
        x_title = '',
    )

def openphil_grants_scatter_section():

    op_grants = get_op_grants()

    return html.Div(
        [
            html.Div(
                html.H2('Open Philanthropy Grants'),
                className='section-title',
            ),
            get_instructions('open_phil'),
            html.Div(
                [
                    html.Div(
                        grants_scatter(op_grants),
                        className='plot-container',
                    ),
                ],
                className='section-body'
            ),
            get_data_source('open_phil'),
        ],
        className = 'section',
        id='op-grants-scatter-section',
    )

def openphil_grants_categories_section():

    op_grants = get_op_grants()

    return html.Div(
        [
            html.Div(
                html.H2('Open Philanthropy Grants by Focus Area and Donee Organization'),
                className='section-title',
            ),
            get_instructions(),
            html.Div(
                html.Div(
                    [
                        html.Div(
                            cause_bar_chart(op_grants),
                            className='plot-container',
                        ),
                        html.Div(
                            org_bar_chart(op_grants),
                            className='plot-container',
                        ),
                    ],
                    className='grid desk-cols-2 tab-cols-2',
                ),
                className='section-body'
            ),
            get_data_source('open_phil'),
        ],
        className = 'section',
        id='op-grants-categories',
    )

def group_by_month(op_grants):

    # Round the dates to the end of the month
    op_grants['Date'] += MonthEnd(1)

    # Generate a date range up to the present
    min_date = op_grants['Date'].min()
    max_date = op_grants['Date'].max()
    dates = pd.date_range(start=min_date, end=max_date, freq='M')

    grants_by_month = pd.DataFrame(columns=[
        'date',
        'grants',
        'focus_areas',
        'organizations',
        'total_amount',
        'n_grants',
    ])

    for i, date in enumerate(dates):
        grants_by_month_i = op_grants.loc[ op_grants['Date'] == date ]
        grants_by_month.loc[i, 'date'] = date
        grants_by_month.loc[i, 'grants'] = grants_by_month_i['Grant'].tolist()
        grants_by_month.loc[i, 'focus_areas'] = grants_by_month_i['Focus Area'].tolist()
        grants_by_month.loc[i, 'organizations'] = grants_by_month_i['Focus Area'].tolist()
        grants_by_month.loc[i, 'total_amount'] = grants_by_month_i['Amount'].sum()
        grants_by_month.loc[i, 'n_grants'] = len(grants_by_month_i)

    return grants_by_month


def openphil_line_plot_section():

    op_grants = get_op_grants()
    op_grants = op_grants.sort_values(by='Date').reset_index()

    def monthly_hover(row):
        month = row['date'].strftime('%B %Y')
        result = ''
        result += f"<b>{month}</b>"
        result += f"<br>{row.n_grants} grants"
        result += f"<br>${row.total_amount:,.2f} total value"
        return result

    grants_by_month = group_by_month(op_grants)

    grants_by_month['hover'] = grants_by_month.apply(monthly_hover, axis=1)
    last_row = grants_by_month.iloc[len(grants_by_month)-1]
    last_month = last_row['date'].strftime('%B %Y')
    label = ''
    label += f"<b>${last_row.total_amount/1e6:,.1f} Million</b>"
    label += f"<br>{last_month}"
    grants_by_month['label'] = label

    month_grants_graph = Line(
        grants_by_month,
        x = 'date',
        y = 'total_amount',
        x_title = '',
        y_title = '',
        hover = 'hover',
        title = 'Granted Amount by Month',
        label = 'label',
        xanchor='left',
        dollars=True,
    )


    op_grants['cumulative_amount'] = op_grants['Amount'].cumsum()

    def cumulative_hover(row):
        result = row['hover']
        result += f"<br>${row.cumulative_amount:,.2f} total"
        return result

    op_grants['hover'] = op_grants.apply(cumulative_hover, axis=1)
    grants_total = op_grants['cumulative_amount'].tolist()[-1]
    op_grants['label'] = f"<b>${grants_total/1e9:,.2f} Billion</b><br>Total Grants"

    total_grants_graph = Line(
        op_grants,
        x = 'Date',
        y = 'cumulative_amount',
        x_title = '',
        y_title = '',
        hover = 'hover',
        title = 'Total Granted Amount',
        label = 'label',
        dollars=True,
    )

    return html.Div(
        [
            html.Div(
                html.H2('Open Philanthropy Grants Over Time'),
                className='section-title',
            ),
            get_instructions(),
            html.Div(
                html.Div(
                    [
                        html.Div(
                            month_grants_graph,
                            className='plot-container',
                        ),
                        html.Div(
                            total_grants_graph,
                            className='plot-container',
                        ),
                    ],
                    className='grid desk-cols-2 tab-cols-2',
                ),
                className='section-body'
            ),
            get_data_source('open_phil'),
        ],
        className = 'section',
        id='op-grants-growth',
    )
