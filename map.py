import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import altair as alt
import re
import numpy as np
from io import StringIO
from google.oauth2.service_account import Credentials
import json
from datetime import datetime, timedelta
import gspread
#sheet loading based on sheet and workbook name
def read_gsheet_to_df(sheet_name, worksheet_name):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials_info = {
        "type": st.secrets["google_credentials"]["type"],
        "project_id": st.secrets["google_credentials"]["project_id"],
        "private_key_id": st.secrets["google_credentials"]["private_key_id"],
        "private_key": st.secrets["google_credentials"]["private_key"],
        "client_email": st.secrets["google_credentials"]["client_email"],
        "client_id": st.secrets["google_credentials"]["client_id"],
        "auth_uri": st.secrets["google_credentials"]["auth_uri"],
        "token_uri": st.secrets["google_credentials"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
    }
    credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)

    client = gspread.authorize(credentials)

    try:
        spreadsheet = client.open(sheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found.")
        return None

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Worksheet '{worksheet_name}' not found in spreadsheet '{sheet_name}'.")
        return None

    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df
def visualize_price_by_location(df, selected_date_range, selected_product, selected_locations): 
    start_date, end_date = selected_date_range 
    start_date = pd.to_datetime(start_date) 
    end_date = pd.to_datetime(end_date) 
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])  
    
    filtered_data = df[ 
        (df['Timestamp'] >= start_date) &  
        (df['Timestamp'] <= end_date) &  
        (df['Products List'] == selected_product) & 
        (df['Location'].isin(selected_locations)) 
    ] 
    
    st.markdown(f"### Price Visualization for {selected_product} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}") 
    
    if filtered_data.empty: 
        st.markdown("No data available for the selected parameters.") 
        return 
    
    # Calculate average price or use 'Unit Price' directly if no average calculation is needed
    filtered_data = filtered_data.assign(average_price=lambda x: x['Unit Price'])
    
    if len(filtered_data) == 1:
        st.markdown("Only one data point available for the selected parameters.")
        st.write(filtered_data)
        return
    
    chart = alt.Chart(filtered_data).mark_line(interpolate='basis').encode( 
        x=alt.X('yearmonthdate(Timestamp):T', axis=alt.Axis(title='Date')), 
        y=alt.Y('average_price:Q', title='Average Price', scale=alt.Scale(zero=False)), 
        color=alt.Color('Location:N', legend=alt.Legend(title='Location', orient='right', labelLimit=400)), 
        tooltip=['yearmonthdate(Timestamp):T', 'Location:N', 'average_price:Q'] 
    ).properties( 
        width=600, 
        height=400, 
        title=f'Average Price Trends of {selected_product}' 
    ).configure_axis( 
        grid=True 
    ).configure_legend( 
        labelFontSize=10, 
        titleFontSize=12 
    ).interactive() 
    
    st.altair_chart(chart, use_container_width=True)
#CHIP INDIVIDUAL AND GROUP PRICES   
def individual_group_prices(df, selected_date_range, selected_product):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%m/%d/%Y %H:%M')
    df_filtered = df[(df['Timestamp'] >= pd.to_datetime(selected_date_range[0], format='%m/%d/%Y')) &
                     (df['Timestamp'] <= pd.to_datetime(selected_date_range[1], format='%m/%d/%Y'))]
    df_filtered = df_filtered[df_filtered['Products List'] == selected_product]
    pivot_df = df_filtered.pivot_table(index='Location', columns='Timestamp', values='Unit Price', aggfunc='mean')
    grouped_df = pivot_df.groupby('Location').sum()
    grouped_df['Total'] = grouped_df.sum(axis=1)
    return pivot_df
def individual_group_prices_(df, selected_date_range, selected_product):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%m/%d/%Y %H:%M')
    df_filtered = df[(df['Timestamp'] >= pd.to_datetime(selected_date_range[0], format='%m/%d/%Y')) &
                     (df['Timestamp'] <= pd.to_datetime(selected_date_range[1], format='%m/%d/%Y'))]
    df_filtered = df_filtered[df_filtered['Products List'] == selected_product]
    pivot_df = df_filtered.pivot_table(index='Location', columns='Timestamp', values='Volume', aggfunc='mean')
    grouped_df = pivot_df.groupby('Location').sum()
    grouped_df['Total'] = grouped_df.sum(axis=1)
    return grouped_df
def create_data_entry_form_and_return_csv():
    with st.form(key='data_entry_form'):
        st.write("Inside the form")
        url = convert_google_sheet_url('https://docs.google.com/spreadsheets/d/1QJi3WJoBHQ9X92ezeTE8WHZM3gCQMJweOXmLmcw-phA/edit?usp=sharing')
        survey = pd.read_csv(url)
        col1, col2 = st.columns(2)
        options = col1.selectbox("select product",tuple(survey['Products List'].unique()))
        date_input = col2.date_input(label='Enter a date')
        st.write("insert price for each benchmarks")
        number_inputs = {}
        for i in survey['Location'].unique():
            number_inputs[i]=st.number_input(label = f'{i}')
        submitted = st.form_submit_button('Submit')
        if submitted:
            form_data = {
                'Text': [text_input],
                'Number': [number_input],
                'Date': [date_input],
                'Time': [time_input]
            }
            df = pd.DataFrame(form_data)
            csv = df.to_csv(index=False)
            csv_buffer = StringIO(csv)
            st.download_button(
                label="Download data as CSV",
                data=csv_buffer,
                file_name='form_data.csv',
                mime='text/csv',
            )
def concatenate_dfs(*dfs):
    concatenated_df = pd.concat(dfs, ignore_index=True)
    return concatenated_df
def display_max_dates_per_location_group(df, timestamp_col, location_groups):
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    results = []
    for group_name, locations in location_groups.items():
        group_data = df[df['Location'].isin(locations)]
        if not group_data.empty:
            max_date = group_data[timestamp_col].max()
            results.append({
                'Group': group_name,
                'Max Date': max_date.strftime('%Y-%m-%d'),
                'Locations': ", ".join(locations)
            })
    results_df = pd.DataFrame(results)
    st.table(results_df)
expander_icon_css = """
<style>
details[open] summary::before {
    content: '−';
}
summary::before {
    content: '+';
    padding-right: 5px;
}
summary {
    font-size: 18px;
    font-weight: bold;
}
</style>
"""
def collapsible_table(title, dataframe):
    # Inject custom CSS with the '+' icon
    st.markdown(expander_icon_css, unsafe_allow_html=True)
    
    # Create the expander and add the DataFrame as a table to it
    with st.expander(title):
        st.dataframe(dataframe)
def calculate_min_prices(data, selected_date_range, selected_product, location_groups):
    # Ensure 'Timestamp' is a datetime and normalize to remove time
    data['Timestamp'] = pd.to_datetime(data['Timestamp']).dt.normalize()
    
    # Filter data for the selected product and date range
    product_data = data[(data['Products List'] == selected_product) &
                        (data['Timestamp'] >= pd.to_datetime(selected_date_range[0])) &
                        (data['Timestamp'] <= pd.to_datetime(selected_date_range[1]))]
    
    if product_data.empty:
        return {group: pd.DataFrame() for group in location_groups}

    date_range = pd.date_range(start=selected_date_range[0], end=selected_date_range[1])
    
    # Create a DataFrame for each group
    group_dfs = {}
    for group, locations in location_groups.items():
        metrics = ['Avg_Price', 'Min_Price', 'Min_Location']
        multi_index = pd.MultiIndex.from_tuples([(group, metric) for metric in metrics], names=['Group', 'Metric'])
        group_df = pd.DataFrame(index=multi_index, columns=date_range)
        for date in date_range:
            day_data = product_data[(product_data['Timestamp'] == date) & 
                                    (product_data['Location'].isin(locations))]
            if not day_data.empty:
                group_df.loc[(group, 'Avg_Price'), date] = day_data['Unit Price'].mean()
                group_df.loc[(group, 'Min_Price'), date] = day_data['Unit Price'].min()
                min_location = day_data.loc[day_data['Unit Price'].idxmin(), 'Location']
                group_df.loc[(group, 'Min_Location'), date] = min_location

        group_dfs[group] = group_df
    
    return group_dfs

def calculate_prices_by_location(data, selected_date_range, selected_product, location_groups):
    data['Timestamp'] = pd.to_datetime(data['Timestamp']).dt.normalize()
    product_data = data[(data['Products List'] == selected_product) &
                        (data['Timestamp'] >= pd.to_datetime(selected_date_range[0])) &
                        (data['Timestamp'] <= pd.to_datetime(selected_date_range[1]))]
    if product_data.empty:
        return {group: pd.DataFrame() for group in location_groups}
    date_range = pd.date_range(start=selected_date_range[0], end=selected_date_range[1])
    group_dfs = {}
    for group, locations in location_groups.items(): 
        multi_index = pd.MultiIndex.from_product([[group], locations], names=['Group', 'Location'])
        group_df = pd.DataFrame(index=multi_index, columns=date_range)
        for location in locations:
            location_data = product_data[product_data['Location'] == location]
            for date in date_range:
                date_data = location_data[location_data['Timestamp'] == date]
                if not date_data.empty:
                    group_df.loc[(group, location), date] = date_data['Unit Price'].iloc[0]
                else:
                    group_df.loc[(group, location), date] = np.nan
        group_dfs[group] = group_df
    return group_dfs
def append_df_to_gsheet(sheet_name, worksheet_name, df):
    # Define the scope
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # Get credentials from Streamlit secrets
    credentials_info = {
        "type": st.secrets["google_credentials"]["type"],
        "project_id": st.secrets["google_credentials"]["project_id"],
        "private_key_id": st.secrets["google_credentials"]["private_key_id"],
        "private_key": st.secrets["google_credentials"]["private_key"],
        "client_email": st.secrets["google_credentials"]["client_email"],
        "client_id": st.secrets["google_credentials"]["client_id"],
        "auth_uri": st.secrets["google_credentials"]["auth_uri"],
        "token_uri": st.secrets["google_credentials"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
    }
    credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)

    client = gspread.authorize(credentials)

    try:
        spreadsheet = client.open(sheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found.")
        return

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Worksheet '{worksheet_name}' not found in spreadsheet '{sheet_name}'.")
        return

    existing_data = worksheet.get_all_records()
    existing_df = pd.DataFrame(existing_data)
    combined_df = pd.concat([existing_df, df], ignore_index=True)
    
    # Clear existing data in the worksheet
    worksheet.clear()
    
    # Update the worksheet with the combined data
    worksheet.update([combined_df.columns.values.tolist()] + combined_df.values.tolist())

def calculate_min_prices_for_viz(data, selected_date_range, selected_product, location_groups, selected_groups):
    # Ensure 'Timestamp' is a datetime and normalize to remove time
    data['Timestamp'] = pd.to_datetime(data['Timestamp']).dt.normalize()
    
    # Filter data for the selected product and date range
    product_data = data[(data['Products List'] == selected_product) &
                        (data['Timestamp'] >= pd.to_datetime(selected_date_range[0])) &
                        (data['Timestamp'] <= pd.to_datetime(selected_date_range[1]))]
    
    if product_data.empty:
        return pd.DataFrame(columns=['Date', 'Location Group', 'Min_Price'])
    
    date_range = pd.date_range(start=selected_date_range[0], end=selected_date_range[1])
    
    # Create a DataFrame to collect min prices for the selected groups
    records = []
    for group in selected_groups:
        if group not in location_groups:
            continue
        locations = location_groups[group]
        for date in date_range:
            day_data = product_data[(product_data['Timestamp'] == date) & 
                                    (product_data['Location'].isin(locations))]
            if not day_data.empty:
                min_price = day_data['Unit Price'].min()
                records.append({'Date': date, 'Location Group': group, 'Min_Price': min_price})
    
    return pd.DataFrame(records)

# Function to plot minimum price trends
def plot_min_price_trends(data, selected_date_range, selected_product, location_groups, selected_groups):
    # Calculate minimum prices for visualization
    min_price_data = calculate_min_prices_for_viz(data, selected_date_range, selected_product, location_groups, selected_groups)
    
    if min_price_data.empty:
        st.error("No data available for the selected criteria.")
        return
    
    # Create the Altair chart with both line and point marks
    line = alt.Chart(min_price_data).mark_line().encode(
        x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('Min_Price:Q', title='Minimum Price'),
        color='Location Group:N',
        tooltip=['Date:T', 'Location Group:N', 'Min_Price:Q']
    )
    
    points = line.mark_point().encode(
        opacity=alt.value(1),
        size=alt.value(50)
    )
    
    chart = line + points
    
    chart = chart.properties(
        title=f"Minimum Prices Trend for {selected_product}",
        width=800,
        height=400
    ).interactive()
    
    # Display the chart using Streamlit
    st.altair_chart(chart)
