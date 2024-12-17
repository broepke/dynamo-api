import streamlit as st
import boto3
import pandas as pd
from botocore.exceptions import ClientError

# Configure the page
st.set_page_config(page_title="Items Dashboard", layout="wide")

# Add title and description
st.title("Items Dashboard")
st.markdown("View and manage items from the DynamoDB database")

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Items')

# Fetch items from DynamoDB
try:
    response = table.scan()
    items = response.get('Items', [])
    
    if items:
        # Convert items to DataFrame
        df = pd.DataFrame(items)
        # Display items in a table
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No items found in the database.")
        
except ClientError as e:
    st.error(f"Error accessing DynamoDB: {str(e)}")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")