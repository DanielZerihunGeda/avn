import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import altair as alt
def convert_google_sheet_url(url):
    # Regular expression to match and capture the necessary part of the URL
    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'

    # Replace function to construct the new URL for CSV export
    # If gid is present in the URL, it includes it in the export URL, otherwise, it's omitted
    replacement = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'

    # Replace using regex
    new_url = re.sub(pattern, replacement, url)

    return new_url
def visualize_price_by_location(df, selected_date_range, selected_product, selected_locations):
    start_date, end_date = selected_date_range
    
    # Convert start_date and end_date to datetime objects
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Convert 'timestamp' column to datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filter DataFrame for the selected date range and product
    filtered_data = df[
        (df['timestamp'] >= start_date) & 
        (df['timestamp'] <= end_date) & 
        (df['Products List'] == selected_product) &
        (df['Location'].isin(selected_locations))
    ]
    
    # Display the title for the chart
    st.markdown(f"### Price Visualization for {selected_product} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Check if the filtered data is empty
    if filtered_data.empty:
        st.markdown("No data available for the selected parameters.")
        return
    
    # Calculate average price
    filtered_data['average_price'] = (filtered_data['Min_unit_price'] + filtered_data['Max_unit_price']) / 2
    
    # Create Altair chart with enhancements
    chart = alt.Chart(filtered_data).mark_line(interpolate='basis').encode(
        x=alt.X('timestamp:T', axis=alt.Axis(title='Date')),
        y=alt.Y('average_price:Q', title='Average Price', scale=alt.Scale(zero=False)),
        color='Location:N',
        tooltip=['timestamp:T', 'Location:N', 'average_price:Q']
    ).properties(
        width=600,
        height=400,
        title=f'Average Price Trends of {selected_product}'
    ).configure_axis(
        grid=True
    ).configure_legend(
        orient='top'
    ).interactive()
    
    # Display the chart in the Streamlit app
    st.altair_chart(chart, use_container_width=True)

