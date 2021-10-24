import plotly.express as px
import pandas as pd
from pandas.tseries.offsets import MonthEnd
import numpy as np
from dash import dcc
from dash import html
from dash import dash_table
from utils.plots.bar import Bar
from utils.subtitle import get_subtitle
from utils.plots.scatter import Scatter
from utils.plots.line import Line

op_grants = None
def get_op_grants():
    global op_grants
    if type(op_grants) != type(None):
        return op_grants

    op_grants = pd.read_csv('./data/openphil_grants.csv')
    op_grants['Amount'] = op_grants['Amount'].apply(
        lambda x: int(x[1:].replace(',','')) if type(x)==str else x
    )
    op_grants = op_grants.dropna()
    op_grants['Focus Area'] = op_grants['Focus Area'].apply(lambda x: x.replace('Artificial Intelligence', 'AI'))
    op_grants = op_grants[::-1]

    op_grants['Grant'] = op_grants['Grant']

    def normalize_orgname(orgname):
        if type(orgname) == str:
            orgname = orgname.strip()
        if orgname == 'Hellen Keller International':
            orgname = 'Helen Keller International'
        if orgname == 'Alliance for Safety and Justice':
            orgname = 'Alliance for Safety and Justice Action Fund'
        return orgname
    op_grants['Organization Name'] = op_grants['Organization Name'].apply(normalize_orgname)

    # for finding number of grants
    op_grants['grants'] = 1

    op_grants['Date'] = pd.to_datetime(op_grants['Date'], format='%m/%Y')
    op_grants = op_grants.sort_values(by='Date', ascending=False)
    op_grants['Date_readable'] = op_grants['Date'].dt.strftime('%B %Y')

    # hovertext
    def hover(row):
        grant = row['Grant']
        org = row['Organization Name']
        area = row['Focus Area']
        date = row['Date_readable']
        amount = row['Amount']
        return f'<b>{grant}</b><br>Date: {date}<br>Organization: {org}<br>Amount: ${amount:,.0f}'
    op_grants['hover'] = op_grants.apply(hover, axis=1)

    return op_grants


def org_bar_chart(op_grants):

    op_orgs = op_grants.groupby(by='Organization Name', as_index=False).sum()
    op_orgs = op_orgs.sort_values(by='Amount')
    op_orgs['x'] = op_orgs['Organization Name']
    # op_orgs['x'] = op_orgs['x'].apply(lambda x: x if len(x) < 30 else x[:27]+'...')
    op_orgs['y'] = op_orgs['Amount']
    op_orgs['text'] = op_orgs['Amount'].apply(lambda x: f'${x:,.0f}')

    # Some organization names get truncated to the same value.
    # This prevents that:
    for val in op_orgs['x'].unique():
        val_df = op_orgs[ op_orgs['x']==val ]
        for i in range(1, len(val_df)):
            index = val_df.iloc[i].name
            op_orgs.loc[index, 'x'] = op_orgs.loc[index, 'x'][:-3-i] + '...'

    def hover(row):
        org = row['Organization Name']
        amount = row['text']
        grants = row['grants']
        return f'<b>{org}</b><br>{grants} grants<br>{amount} total'
    op_orgs['hover'] = op_orgs.apply(hover, axis=1)

    op_orgs_truncated = op_orgs.iloc[len(op_orgs)-25:]

    return Bar(op_orgs_truncated, title='Top 30 Donee Organizations')


def cause_bar_chart(op_grants):

    op_causes = op_grants.groupby(by='Focus Area', as_index=False).sum()
    op_causes = op_causes.sort_values(by='Amount')
    op_causes['x'] = op_causes['Focus Area']
    op_causes['y'] = op_causes['Amount']
    op_causes['text'] = op_causes['Amount'].apply(lambda x: f'${x:,.0f}')

    def hover(row):
        area = row['Focus Area']
        amount = row['text']
        grants = row['grants']
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

# def grants_cumulative_scatter(op_grants):
#     fig = px.scatter(
#         op_grants,
#         x="Date",
#         y="Amount ($)",
#         # color="Focus Area",
#         # size='Amount',
#         hover_data=['Grant'],
#         log_y=True,
#         title='Cumulative Grants (log)',
#     )
#     fig.update_traces(
#         marker_color="#0c869b",
#         hovertext = op_grants['hover'],
#         hovertemplate = '%{hovertext}<extra></extra>',
#     )
#     fig.update_layout(
#         margin=dict(l=0, r=0, t=30, b=0),
#         xaxis=dict(
#             title='',
#         ),
#         yaxis=dict(
#             title='Amount ($)',
#         ),
#         title_x=0.5,
#         font=dict(
#             family="Raleway",
#             size=12,
#         )
#     )
#     return dcc.Graph(id='op-grants-cum-scatter', figure=fig),

# op_grants = op_grants[['Grant', 'Organization Name', 'Focus Area']]
# grants_table = dash_table.DataTable(
#     id = 'op_table',
#     columns = [{"name": i, "id": i} for i in op_grants.columns],
#     data = op_grants.to_dict('records'),
#     page_action='none',
#     fixed_rows={
#         'headers': True,
#     },
#     style_table={
#         'width': '100%',
#         'minWidth': '100%',
#         'maxWidth': '100%',
#     },
#     style_cell={
#         'whiteSpace': 'normal',
#         'height': 'auto',
#     },
#     style_cell_conditional=[
#         {'if': {'column_id': 'Grant'},
#          'width': '30%'},
#         {'if': {'column_id': 'Organization Name'},
#          'width': '20%'},
#         {'if': {'column_id': 'Focus Area'},
#          'width': '10%'},
#     ],
#     # style_cell={
#     #     # 'minWidth': 95,
#     #     'maxWidth': '30%',
#     #     'width': '100%',
#     # }
# )


def openphil_grants_scatter_section():

    op_grants = get_op_grants()

    return html.Div(
        [
            html.Div(
                html.H2('Open Philanthropy Grants'),
                className='section-title',
            ),
            get_subtitle('open_phil', hover='points', zoom=True),
            html.Div(
                [
                    html.Div(
                        grants_scatter(op_grants),
                        className='plot-container',
                    ),
                ],
                className='section-body'
            ),
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
            get_subtitle('open_phil'),
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

    grants_by_month = group_by_month(op_grants)

    def monthly_hover(row):
        month = row['date'].strftime('%B %Y')
        result = ''
        result += f"<b>{month}</b>"
        result += f"<br>{row.n_grants} grants"
        result += f"<br>${row.total_amount:,.2f} total value"
        return result

    grants_by_month['hover'] = grants_by_month.apply(monthly_hover, axis=1)
    last_row = grants_by_month.iloc[len(grants_by_month)-1]
    last_month = last_row['date'].strftime('%B %Y')
    label = ''
    label += f"<b>{last_month}</b>"
    label += f"<br>{last_row.n_grants} grants"
    label += f"<br>${last_row.total_amount/1e6:,.1f}M total"
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
    op_grants['label'] = f"<b>Total Grants</b><br>${grants_total/1e9:,.2f}B"

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
            get_subtitle('open_phil'),
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
        ],
        className = 'section',
        id='op-grants-growth',
    )
