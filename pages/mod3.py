import streamlit as st
import json

# Load the data from mod3.json
with open('mod3.json', 'r') as json_file:
    mod3_data = json.load(json_file)

# Create a dropdown button to select an option
selected_option = st.selectbox("Select an option:", list(mod3_data.keys()))

# Store the selected value in the pdf_path variable
pdf_path = mod3_data[selected_option]

# Display the selected value
st.write(f"Selected PDF path: {pdf_path}")
