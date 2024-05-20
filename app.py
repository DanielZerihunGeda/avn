import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import re
import requests
from io import StringIO
from map import *
from dotenv import load_dotenv
import os

#inittializing environment
load_dotenv()
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
st.title("DASHBOARD")
st.sidebar.title("SIDE BAR")
st.markdown("Select filters to visualize the dashboard")
st.sidebar.markdown("This application is a Streamlit app used to track pricing survey")
col = st.columns((1.5, 4.5, 2), gap='medium')
# Convert Google Sheets URL to CSV URL
url_1 = convert_google_sheet_url(st.secrets["url_1"])
url = convert_google_sheet_url(st.secrets["url"])
url_2 = convert_google_sheet_url(st.secrets["url_2"])
st.write(f"Converted URL: {url},{url_1},{url_2}") 

try:
    survey_0 = pd.read_csv(url)
    survey_1 = pd.read_csv(url_1)
    survey_2 = pd.read_csv(url_2)
    survey_2 = survey_2.rename(columns={'Buying Price': 'Unit Price','Location ': 'Location', 'Product List': 'Products List'})
    st.write("Data loaded successfully!")  # Debugging statement
except Exception as e:
    st.error(f"Failed to load data into DataFrame: {e}")
    st.stop()

# Convert timestamp to date only
survey_0['Timestamp'] = pd.to_datetime(survey_0['Timestamp'], format= "%m/%d/%Y %H:%M:%S").dt.date
survey_1['Timestamp'] = pd.to_datetime(survey_1['Timestamp'], format="%Y-%m-%d %H:%M:%S").dt.date
survey_2['Timestamp'] = pd.to_datetime(survey_2['Timestamp'], format= "%m/%d/%Y %H:%M:%S").dt.date

survey = concatenate_dfs(survey_0,survey_1,survey_2)

selected_date_range = st.sidebar.date_input("Select Date Range", 
                                            value=(pd.to_datetime('today') - pd.to_timedelta(7, unit='d'), 
                                                   pd.to_datetime('today')), 
                                            key="date_range")

# Convert selected_date_range to dates only
start_date = selected_date_range[0]
end_date = selected_date_range[1]

filtered_survey = survey[(survey['Timestamp'] >= start_date) & 
                         (survey['Timestamp'] <= end_date)]

available_products = filtered_survey['Products List'].unique()
available_locations = filtered_survey['Location'].unique()

selected_product = st.sidebar.selectbox("Select Product", available_products, key='unique_key_2')
price_metric = st.sidebar.radio("Select Price Metric", ['Minimum', 'Average'], key='price_metric')

end_date_data = survey[(survey['Products List'] == selected_product) & 
                       (survey['Timestamp'] == end_date)]


min_price_locations = {}
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
    "Farm": []
}
col = st.columns((5.5, 3), gap='medium')
with st.sidebar.expander("Show Analysis", expanded=False):
    for group, locations in location_groups.items():
        group_data = end_date_data[end_date_data['Location'].isin(locations)]
        if not group_data.empty:
            min_price = group_data['Unit Price'].min()
            avg_price = group_data['Unit Price'].mean()
            min_location = group_data.loc[group_data['Unit Price'].idxmin()]['Location']
            st.sidebar.markdown(f"**{group}** - Min: {min_price}, Avg: {avg_price}")
        else:
            min_location = None
            st.sidebar.markdown(f"**{group}** - No data available")
        min_price_locations[group] = min_location

cleaned_location_groups_with_counts = {group: [clean_location_name(loc, filtered_survey) for loc in locations] for group, locations in location_groups.items()}
reverse_location_mapping = {clean_location_name(loc, filtered_survey): loc for loc in survey['Location'].unique()}

all_sorted_locations = []
key_counter = 0
for group, sorted_locations in cleaned_location_groups_with_counts.items():
    is_expanded = key_counter == 0
    with st.sidebar.expander(f"Pick Location ({group})", expanded=is_expanded):
        unique_key = f"pick_location_{group}_{key_counter}"
        locations_with_prices = [f"{loc} " for loc in sorted_locations]
        selected_locations = st.multiselect("", locations_with_prices, key=unique_key)
        all_sorted_locations.extend([reverse_location_mapping[loc.split(' - ')[0]] for loc in selected_locations if loc.split(' - ')[0] in reverse_location_mapping])
    key_counter += 1

filtered_survey = survey[survey['Location'].isin(all_sorted_locations)]
individual_price = st.sidebar.number_input("set Individual price: ")
individual_price = st.sidebar.number_input("set Group Price: ")
bulk_price= st.sidebar.number_input("set Bulk Price: ")

with col[0]:
    visualize_price_by_location(filtered_survey, selected_date_range, selected_product, all_sorted_locations)
with col[1]:
    df = calculate_min_prices(survey, selected_date_range, location_groups)
    st.markdown(f"### Minimum and Average Price in {end_date.strftime('%Y-%m-%d')}")

    st.dataframe(df,
                 column_order=("Min Location","Products List", "Min Price", "Avg Price"),
                 hide_index=True,
                 width=None,
                 column_config={
                    "Min Location": st.column_config.TextColumn(
                        "Location", max_chars=5,default="st.",width='small'
                    ),
                    "Products List": st.column_config.TextColumn(
                        "Prodcut", max_chars=5,width='small'
                    ),
                    "Min Price": st.column_config.NumberColumn(
                        "Min Price",
                     ),"Avg Price": st.column_config.NumberColumn(
                        "Avg Price",
                     )}
                 )
