import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from map import *
url = convert_google_sheet_url('https://docs.google.com/spreadsheets/d/1QJi3WJoBHQ9X92ezeTE8WHZM3gCQMJweOXmLmcw-phA/edit?usp=sharing')
survey = pd.read_csv(url)

st.title("DASHBOARD")
st.sidebar.title("SIDE BAR")
st.markdown("Select filters to visualize the dashboard")
st.sidebar.markdown(" This application is a Streamlit app used to analyze KPI of ChipChip")
# Convert 'created_at' to datetime and 'location' to a tuple of floats (latitude, longitude)
# Convert 'created_at' to datetime and 'location' to a tuple of floats (latitude, longitude)
selected_date_range = st.sidebar.date_input("Select Date Range", 
                                           value=(pd.to_datetime('today') - pd.to_timedelta(7, unit='d'), 
                                                  pd.to_datetime('today')), 
                                           key="date_range")
start_date = selected_date_range[0]
end_date = selected_date_range[1]

if start_date and end_date:
    if start_date > end_date:
        st.sidebar.error("Please select a valid date range.")
    else:
        # Rest of your code for selecting product and benchmark locations
        visualize_price_by_location(survey, selected_date_range, selected_product, choice)
else:
    st.sidebar.info("Please select both start and end dates.")


selected_product = st.sidebar.selectbox("Select Product", 
                                        ('Red Onion Grade A  Restaurant q', 'Red Onion Grade B',
       ' Red Onion Grade C', 'Potatoes', 'Potatoes Restaurant quality',
       'Tomatoes Grade B', 'Tomatoes Grade A', 'Carrot', 'Chilly Green',
       ' Chilly Green (Elfora)', 'Beet root', 'White Cabbage', 'Avocado',
       'Strawberry', 'Papaya', 'Courgette', 'Cucumber', 'Garlic',
       'Ginger', 'Pineapple', 'Mango', 'Lemon', 'Apple',
       'Valencia Orange', 'Yerer Orange', 'Avocado Shekaraw'),
                                        key='unique_key_2')

st.sidebar.subheader("Benchmark Locations")
choice = st.sidebar.multiselect("Pick Location", ('benchmark location 1 Sunday market Piaza',
       'benchmark location 2 Sunday market Bole',
       'benchmark location 3 Sunday market Gerji',
       'benchmark location 1 Suk Bole', 'benchmark location 2 Suk Gulele',
       'benchmark location 3 Suk Yeka', 'benchmark location 4 Suk Arada',
       'benchmark locatio_by_location 5 Suk Lideta',
       'benchmark location 1 supermarket Queens',
       'benchmark location 2 supermarket Purpose black',
       'benchmark location 1 supermarket Queens - per 5 pieces',
       'benchmark location 4 Sunday market Kolfe',
       'benchmark location 6 Suk Kolfe',
       'benchmark location 3 supermarket Freshcorner',
       'Distribution center 1 Gerji', 'Distribution center 2 Garment',
       'Distribution center 3 02 ',
       'Distribution center Lemi kura/ Alem bank',
       'Distribution center 1 Gerji (Raw)',
       'Distribution center 2 Garment (Raw)',
       'Distribution center Lemi kura'), key='unique_key_1')

visualize_price_by_location(survey, selected_date_range, selected_product, choice)
