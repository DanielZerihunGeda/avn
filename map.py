import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import altair as alt
import re
from io import StringIO
def convert_google_sheet_url(url):
    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'
    replacement = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'
    new_url = re.sub(pattern, replacement, url)
    return new_url
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

def calculate_min_prices(df, selected_date_range, location_groups=None):
    results_df = pd.DataFrame(columns=['Group', 'Products List', 'Min Price', 'Avg Price', 'Min Location'])
    
    for group, locations in location_groups.items():
        group_data = df[(df['Timestamp'] >= selected_date_range[0]) & (df['Timestamp'] <= selected_date_range[1]) & 
                        (df['Location'].isin(locations))]
        
        if not group_data.empty:
            for product in group_data['Products List'].unique():
                product_data = group_data[group_data['Products List'] == product]
                min_price = product_data['Unit Price'].min()
                avg_price = product_data['Unit Price'].mean()
                min_location = product_data.loc[product_data['Unit Price'].idxmin()]['Location']
                results_df.loc[len(results_df)] = [group, product, min_price, avg_price, min_location]
    
    return results_df

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
