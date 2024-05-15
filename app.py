# Sort locations within each group based on counts
sorted_location_groups = {}
for group, locations in location_groups.items():
    sorted_locations = sorted(locations, key=lambda loc: location_counts.get(loc, 0), reverse=True)
    sorted_location_groups[group] = sorted_locations

# Create a list to hold all sorted locations
all_sorted_locations = []

# Initialize counter for unique keys
key_counter = 0

# Populate the select box in the sidebar with sorted locations
for group, sorted_locations in sorted_location_groups.items():
    # Generate a unique key based on group name and counter
    unique_key = f"pick_location_{group}_{key_counter}"
    selected_locations = st.sidebar.multiselect(f"Pick Location ({group})", sorted_locations, key=unique_key)
    all_sorted_locations.extend(selected_locations)
    
    # Increment counter
    key_counter += 1

filtered_survey = survey[survey['Location'].isin(all_sorted_locations)]
# Create an empty list to store data for the table
table_data = []

# Iterate over the keys in the location_groups dictionary
for group, locations in location_groups.items():
    # Filter the survey data for the current group and selected date range
    group_data = filtered_survey[(filtered_survey['Location'].isin(locations)) &
                                 (filtered_survey['timestamp'] >= selected_date_range[0]) &
                                 (filtered_survey['timestamp'] <= selected_date_range[1])]
    
    # Calculate the minimum value from the 'min_unit_price' column
    min_price = group_data['min_unit_price'].min()
    
    # Find the benchmark location (last 5 days reference)
    benchmark_location = filtered_survey[(filtered_survey['Location'].isin(locations)) &
                                          (filtered_survey['timestamp'] >= selected_date_range[1] - pd.DateOffset(days=5)) &
                                          (filtered_survey['timestamp'] <= selected_date_range[1])]
    benchmark_location = benchmark_location.iloc[0]['Location'] if not benchmark_location.empty else None
    
    # Append group name, minimum value, and benchmark location to the table data list
    table_data.append({'Group': group, 'Minimum Unit Price': min_price, 'Benchmark Location': benchmark_location})

# Create a DataFrame from the table data
table_df = pd.DataFrame(table_data)

# Display the DataFrame using st.table()
st.table(table_df)


visualize_price_by_location(filtered_survey, selected_date_range, selected_product, all_sorted_locations)
