import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import re
import requests
from io import StringIO
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import json
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from map import *

def clean_location_name(location, filtered_survey):
    if not isinstance(location, str):
        location = str(location)
    cleaned_name = re.sub(r'benchmark location \d+', '', location)
    cleaned_name = re.sub(r'Distribution center \d+', '', cleaned_name)
    cleaned_name = cleaned_name.strip()
    count = filtered_survey[filtered_survey['Location'] == location].shape[0]
    return f"{cleaned_name} ({count})"

def filter_df_by_date_and_products(df, selected_date_range, selected_products):
    start_date, end_date = selected_date_range
    mask_date = (df['Timestamp'] >= start_date) & (df['Timestamp'] <= end_date)
    mask_products = df['Products List'].apply(lambda x: any(item in x for item in selected_products))
    filtered_df = df[mask_date & mask_products]
    return filtered_df

def fetch_google_sheet_csv(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        csv_data = response.content.decode('utf-8')
        return csv_data
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

st.set_page_config(layout="wide")

st.title("ChipChip Product Pricing")

st.sidebar.markdown("Select filters to visualize the dashboard")

def fetch_data(sheet_name, worksheet_name):
    try:
        return read_gsheet_to_df(sheet_name, worksheet_name)
    except Exception as e:
        st.error(f"Failed to load {worksheet_name} into DataFrame: {e}")
        return None

sheets_and_worksheets = [
    ('chip', 'sunday'),
    ('chip', 'Localshops'),
    ('chip', 'Distribution'),
    ('chip', 'Farm_'),
    ('chip', 'chip_prices'),
    ('chip', 'volume')
]

# Fetch data concurrently
data_frames = {}
with ThreadPoolExecutor() as executor:
    future_to_sheet = {executor.submit(fetch_data, sheet, worksheet): worksheet for sheet, worksheet in sheets_and_worksheets}
    for future in as_completed(future_to_sheet):
        worksheet_name = future_to_sheet[future]
        try:
            data_frames[worksheet_name] = future.result()
        except Exception as e:
            st.error(f"Failed to load data from {worksheet_name}: {e}")

# Ensure loading and renaming of survey_3 are within try-except block
try:
    survey_0 = data_frames.get('sunday')
    survey_1 = data_frames.get('Localshops')
    survey_2 = data_frames.get('Distribution')
    survey_3 = data_frames.get('Farm_')
    chip_prices = data_frames.get('chip_prices')
    volume = data_frames.get('volume')

    if survey_2 is not None:
        survey_2 = survey_2.rename(columns={'Buying Price': 'Unit Price', 'Location ': 'Location', 'Product List': 'Products List'})
    if survey_3 is not None:
        survey_3 = survey_3.rename(columns={'Buying Price per Kg ': 'Unit Price', 'Product Origin': 'Location', 'Product List': 'Products List'})

except Exception as e:
    st.error(f"Failed to load data into DataFrame: {e}")
    st.stop()

survey_0['Timestamp'] = pd.to_datetime(survey_0['Timestamp'], format="%m/%d/%Y %H:%M:%S").dt.date
survey_1['Timestamp'] = pd.to_datetime(survey_1['Timestamp'], format="%Y-%m-%d %H:%M:%S").dt.date
survey_2['Timestamp'] = pd.to_datetime(survey_2['Timestamp'], format="%m/%d/%Y %H:%M:%S").dt.date
survey_3['Timestamp'] = pd.to_datetime(survey_3['Timestamp'], format="%m/%d/%Y %H:%M:%S").dt.date
chip_prices['Timestamp'] = pd.to_datetime(chip_prices['Timestamp'], format="%m/%d/%Y %H:%M").dt.date
survey = concatenate_dfs(survey_0, survey_1, survey_2, chip_prices)

default_start = pd.to_datetime('today') - pd.to_timedelta(7, unit='d')
default_end = pd.to_datetime('today')
start_date = st.sidebar.date_input("From", value=default_start, key="start_date")
end_date = st.sidebar.date_input("To", value=default_end, key="end_date")
selected_date_range = (start_date, end_date)

filtered_survey = survey[(survey['Timestamp'] >= start_date) & (survey['Timestamp'] <= end_date)]
available_products = filtered_survey['Products List'].unique()
available_locations = filtered_survey['Location'].unique()

selected_product = st.sidebar.selectbox("Select Product", available_products, key='unique_key_2')
end_date_data = survey[(survey['Products List'] == selected_product) & (survey['Timestamp'] == end_date)]
avg_min_chip_prices = individual_group_prices(chip_prices, selected_date_range, selected_product)
chip_volume = individual_group_prices_(volume, selected_date_range, selected_product)
combined = concatenate_dfs(survey, chip_prices)

location_groups = {
    "Local Shops": [],
    "Supermarkets": [],
    "Sunday Markets": [],
    "Distribution Centers":[],
    "Farm": survey_3["Location"].unique(),
    "ChipChip": []
}
for location in survey["Location"].unique():
    if re.search(r'suk', location, re.IGNORECASE):
        location_groups["Local Shops"].append(location)
    elif re.search(r'supermarket', location, re.IGNORECASE):
        location_groups["Supermarkets"].append(location)
    elif re.search(r'sunday', location, re.IGNORECASE):
        location_groups["Sunday Markets"].append(location)
    elif re.search(r'Distribution center', location, re.IGNORECASE):
        location_groups["Distribution Centers"].append(location)
    elif re.search(r'Chipchip', location, re.IGNORECASE):
        location_groups["ChipChip"].append(location)
    
cleaned_location_groups_with_counts = {group: [clean_location_name(loc, filtered_survey) for loc in locations] for group, locations in location_groups.items()}
reverse_location_mapping = {clean_location_name(loc, filtered_survey): loc for loc in survey['Location'].unique()}
all_sorted_locations = []
selected_groups_default = [list(location_groups.keys())[5], list(location_groups.keys())[3], list(location_groups.keys())[2]]
selected_groups = st.sidebar.multiselect("Select Location Groups for Comparison", options=list(location_groups.keys()), default=selected_groups_default)

key_counter = 0

with st.sidebar.form(key='price_form'):
    individual_price = st.number_input("Set Individual Price:", min_value=0.0, format="%.2f")
    group_price = st.number_input("Set Group Price:", min_value=0.0, format="%.2f")
    bulk_price = st.number_input("Set Bulk Price:", min_value=0.0, format="%.2f")
    submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        if individual_price == 0 and group_price == 0 and bulk_price == 0:
            st.warning("Please set at least one price.")
        else:
            current_time = datetime.now()
            data = {
                'Individual Price': [individual_price],
                'Group Price': [group_price],
                'Bulk Price': [bulk_price],
                'Timestamp': [current_time.strftime("%Y-%m-%d")],
                'Products List': selected_product
            }
            df = pd.DataFrame(data)
            append_df_to_gsheet('chip', 'set_price', df)
            st.success('Data submitted successfully!')

for group, sorted_locations in cleaned_location_groups_with_counts.items():
    is_expanded = key_counter == 0
    with st.sidebar.expander(f"Pick Location ({group})", expanded=is_expanded):
        unique_key = f"pick_location_{group}_{key_counter}"
        locations_with_prices = [f"{loc} " for loc in sorted_locations]
        selected_locations = st.multiselect("", locations_with_prices, key=unique_key)
        all_sorted_locations.extend([reverse_location_mapping[loc.split(' - ')[0]] for loc in selected_locations if loc.split(' - ')[0] in reverse_location_mapping])
    key_counter += 1

filtered_survey = survey[survey['Location'].isin(all_sorted_locations)]
visualize_price_by_location(filtered_survey, selected_date_range, selected_product, all_sorted_locations)
df = calculate_min_prices(survey, selected_date_range, selected_product, location_groups)
df1 = calculate_prices_by_location(survey, selected_date_range, selected_product, location_groups)

# Display various sections with collapsible tables
sections = ["Local Shops", "Supermarkets", "Sunday Markets", "Distribution Centers", "Farm"]
for section in sections:
    text = f"{section} Overview"
    html_string = f"""
    <span style="font-weight: bold; color: red;">{text}</span>
    """
    st.write(html_string, unsafe_allow_html=True)
    st.write(df[section])
    collapsible_table(section, df1[section])
    st.write("<hr style='border-top: 2px solid white; margin: 10px 0;'>", unsafe_allow_html=True)

text = f"chipchip Price Overview"
html_string = f"""
    <span style="font-weight: bold; color: red;">{text}</span>
    """
st.write(html_string, unsafe_allow_html=True)

st.write(avg_min_chip_prices)
st.write(chip_volume)
plot_min_price_trends(combined, selected_date_range, selected_product, location_groups, selected_groups)
