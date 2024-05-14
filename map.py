import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import altair as alt
import re
def convert_google_sheet_url(url):
    # Regular expression to match and capture the necessary part of the URL
    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'

    # Replace function to construct the new URL for CSV export
    # If gid is present in the URL, it includes it in the export URL, otherwise, it's omitted
    replacement = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'

    # Replace using regex
    new_url = re.sub(pattern, replacement, url)

    return new_url

    
def visualize_min_price_per_each_category(df, selected_date_range, selected_locations):
    start_date, end_date = selected_date_range 

    # Convert start_date and end_date to datetime objects 
    start_date = pd.to_datetime(start_date) 
    end_date = pd.to_datetime(end_date)

    # Convert 'timestamp' column to datetime format 
    df['timestamp'] = pd.to_datetime(df['timestamp']) 
    # Filter DataFrame for the selected date range and product 

    # Filter DataFrame for the selected date range and locations
    filtered_data = df[
          (df['timestamp'] >= start_date) &
          (df['timestamp'] <= end_date) &
          (df['Location'].isin(selected_locations))
          # (if selected_categories == "Suk":
          #       df.loc[np.where((df['Location'].values == category_location_map[0]
          #  elif selected_categories == "Super Market":
          #       df.loc[np.where((df['Location'].values == category_location_map[1]
          #  else:
          #       df.loc[np.where((df['Location'].values == category_location_map[2])
       ]
    category_location_map = {
            "Suk":["benchmark location 1 Suk Bole","benchmark location 3 Suk Yeka","benchmark location 6 Suk Kolfe","benchmark location 2 Suk Gulele","benchmark location 4 Suk Arada"],
            "Sunday Market":["benchmark location 1 Sunday market Piaza", "benchmark location 2 Sunday market Bole", "benchmark location 3 Sunday market Gerji","benchmark location 4 Sunday market Kolfe"],
            "Super Market":["benchmark location 3 supermarket Freshcorner","benchmark location 1 supermarket Queens","benchmark location 2 supermarket Purpose black","benchmark location 1 supermarket Queens"],
        }
    
    
  
    # Minimum price per category
    if not filtered_data.empty:  # Check if data is empty
        # Create a dictionary for category assignment (assuming unique locations)

        category_mapping = {loc: category for loc, category in category_location_map, selected_locations)}
        filtered_data["Category"] = filtered_data["Location"].apply(lambda loc: category_mapping.get(loc))
        
        # Minimum price per category using groupby
        min_prices_per_category = filtered_data.groupby("Category")["Min_unit_price"].min().reset_index()  
    else:
        min_prices_per_category = pd.DataFrame(columns=["Category", "Min_unit_price"])  # Empty DataFrame if no data
    
    return min_prices_per_category


   

       
        

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

    # Calculate average price using .assign()
    filtered_data = filtered_data.assign(average_price=lambda x: (x['Min_unit_price'] + x['Max_unit_price']) / 2)

    # Create Altair chart with side legend for full string display
    chart = alt.Chart(filtered_data).mark_line(interpolate='basis').encode( 
        x=alt.X('timestamp:T', axis=alt.Axis(title='Date')), 
        y=alt.Y('average_price:Q', title='Average Price', scale=alt.Scale(zero=False)), 
        color=alt.Color('Location:N', legend=alt.Legend(title='Location', orient='right', labelLimit=400)), 
        tooltip=['timestamp:T', 'Location:N', 'average_price:Q'] 
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

    # Display the chart in the Streamlit app 
    st.altair_chart(chart, use_container_width=True)
