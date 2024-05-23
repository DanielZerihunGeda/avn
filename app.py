import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import re
import requests
from io import StringIO
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
from dotenv import load_dotenv
import os
from map import *


def clean_location_name(location, filtered_survey):
    cleaned_name = re.sub(r'benchmark location \d+', '', location)
    cleaned_name = re.sub(r'Distribution center \d+', '', cleaned_name)
    cleaned_name = cleaned_name.strip()
    count = filtered_survey[filtered_survey['Location'] == location].shape[0]
    return f"{cleaned_name} ({count})"

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

url_1 = convert_google_sheet_url(st.secrets["url_1"])
url = convert_google_sheet_url(st.secrets["url"])
url_2 = convert_google_sheet_url(st.secrets["url_2"])
url_3 = convert_google_sheet_url(st.secrets["url_3"])
#url_4 = convert_google_sheet_url('https://docs.google.com/spreadsheets/d/1QJi3WJoBHQ9X92ezeTE8WHZM3gCQMJweOXmLmcw-phA/edit#gid=1966377483')
#st.write(f"Converted URL: {url},{url_1},{url_2},{url_3}") 

try:
    survey_0 = pd.read_csv(url)
    survey_1 = pd.read_csv(url_1)
    survey_2 = pd.read_csv(url_2)
    survey_3 = pd.read_csv(url_3)
    survey_2 = survey_2.rename(columns={'Buying Price': 'Unit Price','Location ': 'Location', 'Product List': 'Products List'})
    survey_3 = survey_3.rename(columns={'Buying Price per Kg ': 'Unit Price','Product Origin ':'Location','Product List':'Products List'})
   # survey_4 =  pd.read_csv(url_4)
    st.write("Data loaded successfully!") 
except Exception as e:
    st.error(f"Failed to load data into DataFrame: {e}")
    st.stop()

survey_0['Timestamp'] = pd.to_datetime(survey_0['Timestamp'], format= "%m/%d/%Y %H:%M:%S").dt.date
survey_1['Timestamp'] = pd.to_datetime(survey_1['Timestamp'], format="%Y-%m-%d %H:%M:%S").dt.date
survey_2['Timestamp'] = pd.to_datetime(survey_2['Timestamp'], format= "%m/%d/%Y %H:%M:%S").dt.date
survey_3['Timestamp'] = pd.to_datetime(survey_3['Timestamp'], format="%Y-%m-%d %H:%M:%S").dt.date
survey = concatenate_dfs(survey_0, survey_1, survey_2, survey_3)

default_start = pd.to_datetime('today') - pd.to_timedelta(7, unit='d')
default_end = pd.to_datetime('today')
start_date = st.sidebar.date_input(
    "From", 
    value=default_start, 
    key="start_date"
)
end_date = st.sidebar.date_input(
    "To", 
    value=default_end, 
    key="end_date"
)
selected_date_range = (start_date, end_date)
start_date = selected_date_range[0]
end_date = selected_date_range[1]

filtered_survey = survey[(survey['Timestamp'] >= start_date) & 
                         (survey['Timestamp'] <= end_date)]
available_products = filtered_survey['Products List'].unique()
available_locations = filtered_survey['Location'].unique()

selected_product = st.sidebar.selectbox("Select Product", available_products, key='unique_key_2')
end_date_data = survey[(survey['Products List'] == selected_product) & 
                       (survey['Timestamp'] == end_date)]

location_groups = {
    "Local Shops": ['benchmark location 1 Suk Bole', 'benchmark location 2 Suk Gulele',
                    'benchmark location 3 Suk Yeka', 'benchmark location 4 Suk Arada',
                    'benchmark location 5 Suk Lideta','benchmark location 6 Suk Kolfe'],
    "Supermarkets": ['benchmark location 1 supermarket Queens',
                     'benchmark location 2 supermarket Purpose black',
                     'benchmark location 1 supermarket Queens - per 5 pieces'],
    "Sunday Markets": ['benchmark location 1 Sunday market Piaza', 'benchmark location 2 Sunday market Bole',
                       'benchmark location 3 Sunday market Gerji'],        
    "Distribution Centers": ['Distribution center 1 Gerji', 'Distribution center 2 Garment',
                             'Distribution center 3 02', 'Distribution center Lemi kura/ Alem bank',
                             'Distribution center 1 Gerji (Raw)', 'Distribution center 2 Garment (Raw)',
                             'Distribution center Lemi kura'],
    "Farm":['Mekele', 'Kobo', 'Dansha'],
    "ChipChip":['Current daily volume (day prior) Yazz',
       'Current daily volume (day prior) Chipchip']
}

cleaned_location_groups_with_counts = {group: [clean_location_name(loc, filtered_survey) for loc in locations] for group, locations in location_groups.items()}
reverse_location_mapping = {clean_location_name(loc, filtered_survey): loc for loc in survey['Location'].unique()}
all_sorted_locations = []
selected_groups = st.sidebar.multiselect(
        "Select Location Groups for Comparision ",
        options=list(location_groups.keys()),
        default=list(location_groups.keys())
    )
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
            # Create a DataFrame with the submitted data
            current_time = datetime.now()
            data = {
                'Individual Price': [individual_price],
                'Group Price': [group_price],
                'Bulk Price': [bulk_price],
                'Timestamp': [current_time.strftime("%Y-%m-%d %H:%M:%S")]
            }
            df = pd.DataFrame(data)
            
            # Path to your credentials file
                  # Replace with the path to your credentials file
            
                        # Append the data to the Google Sheet
            append_df_to_gsheet('bekele','Sheet2', df)
            
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

text = "Local shops Overview"
html_string = f"""
<span style="font-weight: bold; color: red;">{text}</span>
"""
st.write(html_string, unsafe_allow_html=True)
st.write(df["Local Shops"])
collapsible_table("Local Shops",df1["Local Shops"])

text = "Supermarkets Overview"
html_string = f"""
<span style="font-weight: bold; color: red;">{text}</span>
"""
st.write(html_string, unsafe_allow_html=True)
st.write(df["Supermarkets"])
collapsible_table("Supermarkets",df1["Supermarkets"])

text = "Sunday Markets Overview"
html_string = f"""
<span style="font-weight: bold; color: red;">{text}</span>
"""
st.write(html_string, unsafe_allow_html=True)
st.write(df["Sunday Markets"])
collapsible_table("Sunday Markets",df1["Sunday Markets"])

text = "Farm Overview"
html_string = f"""
<span style="font-weight: bold; color: red;">{text}</span>
"""
st.write(html_string, unsafe_allow_html=True)
st.write(df["Farm"])
collapsible_table("Farm", df1["Farm"])
plot_min_price_trends(survey, selected_date_range, selected_product, location_groups, selected_groups)


