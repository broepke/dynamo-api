import streamlit as st
import pandas as pd
import requests

# Configure the page
st.set_page_config(page_title="Items Dashboard", layout="wide")

# Add title and description
st.title("Items Dashboard")
st.markdown("View and manage items from the database")

# Configure API URL
API_URL = "https://bse2pkr2m1.execute-api.us-east-1.amazonaws.com/default"

# Fetch items from API
try:
    response = requests.get(f"{API_URL}/items")
    response.raise_for_status()  # Raise an exception for bad status codes
    items = response.json()
    
    if items:
        # Convert items to DataFrame
        df = pd.DataFrame(items)
        # Display items in a table
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No items found in the database.")
        
except requests.RequestException as e:
    st.error(f"Error accessing API: {str(e)}")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
