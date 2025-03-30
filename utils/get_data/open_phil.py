import requests
import os
import pandas as pd
from datetime import datetime
from io import StringIO
from bs4 import BeautifulSoup

def download_grants():
    # IMPORTANT: This URL may need to be updated manually if Open Philanthropy changes their data access method
    # The nonce in the URL may expire, requiring a new one to be obtained from their website
    openphil_url = 'https://www.openphilanthropy.org/wp-admin/admin-ajax.php?action=generate_grants&nonce=76f5319a09'
    print('Downloading Open Philanthropy grants...')
    try:
        # Set up headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/csv,application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        # Download the CSV file
        response = requests.get(openphil_url, headers=headers)
        response.raise_for_status()
        
        # Return the CSV content
        return response.text
        
    except Exception as e:
        print(f"Error downloading grants: {e}")
        print("Note: The URL may need to be updated with a new nonce from Open Philanthropy's website")
        return None

def save_grants():
    data_dir = os.path.abspath('./assets/data/')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    grants_raw = download_grants()
    if grants_raw is None:
        print("Failed to download grants data")
        return False

    try:
        # Parse the CSV data
        df = pd.read_csv(StringIO(grants_raw))
        print(f'Latest OP grant date: {df["Date"].max() if "Date" in df.columns else "Unknown"}')
        
        # Save to CSV
        grants_path = os.path.join(data_dir, 'openphil_grants.csv')
        df.to_csv(grants_path, index=False)
        print(f"Successfully saved grants data to {grants_path}")
        return True
    except Exception as e:
        print(f"Error processing grants data: {e}")
        return False

def process_grants(grants_df):
    if grants_df is None or grants_df.empty:
        return None

    try:
        # Clean amount column
        grants_df['Amount'] = grants_df['Amount'].apply(
            lambda x: int(str(x).replace('$', '').replace(',', '')) if pd.notnull(x) else 0
        )

        # Normalize organization names
        def normalize_orgname(orgname):
            if pd.isnull(orgname):
                return ''
            orgname = str(orgname).strip()
            if orgname == 'Hellen Keller International':
                orgname = 'Helen Keller International'
            if orgname == 'Alliance for Safety and Justice':
                orgname = 'Alliance for Safety and Justice Action Fund'
            return orgname
        grants_df['Organization Name'] = grants_df['Organization Name'].apply(normalize_orgname)

        # Process dates
        grants_df['Date'] = pd.to_datetime(grants_df['Date'], format='%B %Y')
        grants_df = grants_df.sort_values(by='Date', ascending=False)
        grants_df['Date_readable'] = grants_df['Date'].dt.strftime('%B %Y')

        # Add hover text
        def hover(row):
            grant = row['Grant']
            org = row['Organization Name']
            area = row['Focus Area']
            date = row['Date_readable']
            amount = row['Amount']
            return f'<b>{grant}</b><br>Date: {date}<br>Organization: {org}<br>Amount: ${amount:,.0f}'
        grants_df['hover'] = grants_df.apply(hover, axis=1)

        # Add grants count
        grants_df['grants'] = 1

        return grants_df
    except Exception as e:
        print(f"Error processing grants: {e}")
        return None

def group_by_month(grants_df):

    min_date = grants_df['Date'].min()
    max_date = grants_df['Date'].max()
    dates = pd.date_range(start=min_date, end=max_date, freq='M')

    grants_by_month = pd.DataFrame(columns=[
        'date',
        'total_amount',
        'n_grants',
    ])

    for i, date in enumerate(dates):
        grants_by_month_i = grants_df.loc[ grants_df['Date'] == date ]
        grants_by_month.loc[i, 'date'] = date
        grants_by_month.loc[i, 'total_amount'] = grants_by_month_i['Amount'].sum()
        grants_by_month.loc[i, 'n_grants'] = len(grants_by_month_i)

    return grants_by_month

def group_by_org(grants_df):
    orgs_df = op_grants.groupby(by='Organization Name', as_index=False).sum()
    orgs_df = orgs_df.sort_values(by='Amount')

def group_by_focus_area(grants_df):
    orgs_df = op_grants.groupby(by='Organization Name', as_index=False).sum()
    orgs_df = orgs_df.sort_values(by='Amount')
