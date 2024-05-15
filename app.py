import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from map import *

st.title("DASHBOARD")
st.sidebar.title("SIDE BAR")
st.markdown("Select filters to visualize the dashboard")
st.sidebar.markdown("This application is a Streamlit app used to track pricing survey")

# Load data
url = convert_google_sheet_url('https://docs.google.com/spreadsheets/d/1QJi3WJoBHQ9X92ezeTE8WHZM3gCQMJweOXmLmcw-phA/edit?usp=sharing')
survey = pd.read_csv(url)

# Convert 'timestamp' column to datetime (if not already done)
survey['timestamp'] = pd.to_datetime(survey['timestamp'])

# Sidebar date picker for selecting date range
selected_date_range = st.sidebar.date_input("Select Date Range", 
                                           value=(pd.to_datetime('today') - pd.to_timedelta(7, unit='d'), 
                                                  pd.to_datetime('today')), 
                                           key="date_range")

# Filter data based on the selected date range
filtered_survey = survey[(survey['timestamp'] >= pd.Timestamp(selected_date_range[0])) & 
                         (survey['timestamp'] <= pd.Timestamp(selected_date_range[1]))]

# Extract unique products and locations
available_products = filtered_survey['Products List'].unique()
available_locations = filtered_survey['Location'].unique()

# Sidebar select boxes
selected_product = st.sidebar.selectbox("Select Product", available_products, key='unique_key_2')
# Define groups of locations
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

all_locations = []

for group, locations in location_groups.items():
    selected_locations = st.sidebar.multiselect(f"Pick Location ({group})", locations)
    all_locations.extend(selected_locations)

# Filter data based on selected locations
filtered_survey = survey[survey['Location'].isin(all_locations)]


# Visualize data
visualize_price_by_location(filtered_survey, selected_date_range, selected_product, selected_locations)
