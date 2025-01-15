import streamlit as st
import pandas as pd
import requests

# Configure the page
st.set_page_config(page_title="Items Dashboard", layout="wide")

# Initialize session state
if 'cursor' not in st.session_state:
    st.session_state.cursor = None

# Configure API URL
API_URL = "https://api.dataknowsall.com"

# Sidebar controls
with st.sidebar:
    st.title("API Controls")
    
    # API version selector
    api_version = st.radio(
        "API Version",
        ["Base", "V1"],
        help="Select which API version to use"
    )
    
    # Limit control (only for V1)
    limit = None
    if api_version == "V1":
        limit = st.number_input(
            "Items per request",
            min_value=1,
            max_value=100,
            value=10,
            help="Number of items to fetch per request (V1 API only)"
        )

# Add title and description
st.title("Items Dashboard")
st.markdown("View and manage items from the database")

# Fetch items from API
try:
    if api_version == "Base":
        # Base API call
        response = requests.get(f"{API_URL}/items")
        response.raise_for_status()
        items = response.json()
    else:
        # V1 API call with cursor-based pagination
        response = requests.get(
            f"{API_URL}/v1/items",
            params={
                "limit": limit,
                "cursor": st.session_state.cursor
            }
        )
        response.raise_for_status()
        data = response.json()
        items = data["items"]
        st.session_state.cursor = data.get("next_cursor")
    
    if items:
        # Convert items to DataFrame
        df = pd.DataFrame(items)
        df = df[["id", "name", "description"]]
        
        # Display items in a table
        st.dataframe(df, use_container_width=True)
        
        # Navigation controls (only for V1)
        if api_version == "V1":
            col1, col2 = st.columns([4, 1])
            
            with col2:
                if st.session_state.cursor:
                    if st.button("Load More →"):
                        st.rerun()
                elif len(items) >= limit:
                    st.info("All items loaded")
                else:
                    st.info("No more items")
    else:
        st.info("No items found in the database.")
        
except requests.RequestException as e:
    st.error(f"Error accessing API: {str(e)}")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
