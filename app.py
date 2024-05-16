
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import re
from map import *

# Added Regular expression function to handle the name
def clean_location_name(location):

    location = re.sub(r'benchmark location \d+', '', location)
    location = re.sub(r'Distribution center \d+', '', location)
    location = location.strip()
    return location

st.title("DASHBOARD")
st.sidebar.title("SIDE BAR")
st.markdown("Select filters to visualize the dashboard")
st.sidebar.markdown("This application is a Streamlit app used to track pricing survey")

# Load the data
url = convert_google_sheet_url('https://docs.google.com/spreadsheets/d/1QJi3WJoBHQ9X92ezeTE8WHZM3gCQMJweOXmLmcw-phA/edit?usp=sharing')
survey = pd.read_csv(url)
survey['timestamp'] = pd.to_datetime(survey['timestamp'])

# Sidebar date range filterer
selected_date_range = st.sidebar.date_input("Select Date Range", 
                                            value=(pd.to_datetime('today') - pd.to_timedelta(7, unit='d'), 
                                                   pd.to_datetime('today')), 
                                            key="date_range")

#
filtered_survey = survey[(survey['timestamp'] >= pd.Timestamp(selected_date_range[0])) & 
                         (survey['timestamp'] <= pd.Timestamp(selected_date_range[1]))]

#
available_products = filtered_survey['Products List'].unique()
available_locations = filtered_survey['Location'].unique()


selected_product = st.sidebar.selectbox("Select Product", available_products, key='unique_key_2')

location_groups = {
    "Local Shops": ['benchmark location 1 Suk Bole', 'benchmark location 2 Suk Gulele',
       'benchmark location 3 Suk Yeka', 'benchmark location 4 Suk Arada',
       'benchmark location 5 Suk Lideta','benchmark location 6 Suk Kolfe',],
    "Supermarkets": [ 'benchmark location 1 supermarket Queens',
       'benchmark location 2 supermarket Purpose black',
       'benchmark location 1 supermarket Queens - per 5 pieces',],
    "Sunday Markets":['benchmark location 1 Sunday market Piaza','benchmark location 2 Sunday market Bole',
       'benchmark location 3 Sunday market Gerji'],
    "Distribution Centers":['Distribution center 1 Gerji', 'Distribution center 2 Garment',
       'Distribution center 3 02',
       'Distribution center Lemi kura/ Alem bank',
       'Distribution center 1 Gerji (Raw)',
       'Distribution center 2 Garment (Raw)',
       'Distribution center Lemi kura'],
     "Farm":[]  
}
cleaned_location_groups = {group: [clean_location_name(loc) for loc in locations] for group, locations in location_groups.items()}
reverse_location_mapping = {clean_location_name(loc): loc for loc in survey['Location'].unique()}
def clean_location_name(location, filtered_survey):
    cleaned_name = re.sub(r'benchmark location \d+', '', location)
    cleaned_name = re.sub(r'Distribution center \d+', '', cleaned_name)
    cleaned_name = cleaned_name.strip()
    count = filtered_survey[filtered_survey['Location'] == location].shape[0]
    return f"{cleaned_name} ({count})"
cleaned_location_groups_with_counts = {group: [clean_location_name(loc, filtered_survey) for loc in locations] for group, locations in location_groups.items()}
reverse_location_mapping = {clean_location_name(loc, filtered_survey): loc for loc in survey['Location'].unique()}
all_sorted_locations = []
key_counter = 0
for group, sorted_locations in cleaned_location_groups_with_counts.items():
    unique_key = f"pick_location_{group}_{key_counter}"
    selected_locations = st.sidebar.multiselect(f"Pick Location ({group})", sorted_locations, key=unique_key)
    all_sorted_locations.extend([reverse_location_mapping[loc] for loc in selected_locations if loc in reverse_location_mapping])
    key_counter += 1
filtered_survey = survey[survey['Location'].isin(all_sorted_locations)]
visualize_price_by_location(filtered_survey, selected_date_range, selected_product, all_sorted_locations)
calculate_min_prices(survey, selected_date_range, selected_product, location_groups)
