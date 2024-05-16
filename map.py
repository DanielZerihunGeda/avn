import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import altair as alt
import re
def convert_google_sheet_url(url):
    # Regular expression to match and capture the necessary part of the URL
    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'
    replacement = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'
    new_url = re.sub(pattern, replacement, url)
    return new_url
def visualize_price_by_location(df, selected_date_range, selected_product, selected_locations): 
    start_date, end_date = selected_date_range 
    start_date = pd.to_datetime(start_date) 
    end_date = pd.to_datetime(end_date) 
    df['timestamp'] = pd.to_datetime(df['timestamp'])  
    filtered_data = df[ 
        (df['timestamp'] >= start_date) &  
        (df['timestamp'] <= end_date) &  
        (df['Products List'] == selected_product) & 
        (df['Location'].isin(selected_locations)) 
    ] 
    st.markdown(f"### Price Visualization for {selected_product} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}") 
    if filtered_data.empty: 
        st.markdown("No data available for the selected parameters.") 
        return 
    filtered_data = filtered_data.assign(average_price=lambda x: (x['Min_unit_price'] + x['Max_unit_price']) / 2)
    chart = alt.Chart(filtered_data).mark_line(interpolate='basis').encode( 
        x=alt.X('yearmonthdate(timestamp):T', axis=alt.Axis(title='Date')), 
        y=alt.Y('average_price:Q', title='Average Price', scale=alt.Scale(zero=False)), 
        color=alt.Color('Location:N', legend=alt.Legend(title='Location', orient='right', labelLimit=400)), 
        tooltip=['yearmonthdate(timestamp):T', 'Location:N', 'average_price:Q'] 
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
def calculate_min_prices(df, selected_date_range, selected_product = None, location_groups = None):
    _, end_date = selected_date_range
    end_date = pd.to_datetime(end_date)
    end_date_data = df[df['timestamp'] == end_date]
    results = []
    for group_name, locations in location_groups.items():
        if locations: 
            group_data = end_date_data[
                (end_date_data['Products List'] == selected_product) &
                (end_date_data['Location'].isin(locations))
            ]
            if not group_data.empty:
                min_price = group_data['Price'].min()
                min_location = group_data[group_data['Price'] == min_price]['Location'].iloc[0]
                results.append({
                    'Group': group_name,
                    'Minimum Price': min_price,
                    'Product Item': selected_product,
                    'End Date': end_date.strftime('%Y-%m-%d'),
                    'Exact Location': min_location
                })
    results_df = pd.DataFrame(results)
    st.table(results_df)
