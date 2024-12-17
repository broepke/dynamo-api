import streamlit as st
import boto3
from botocore.exceptions import ClientError
import uuid

# Configure the page
st.set_page_config(page_title="Add New Item", layout="wide")

# Add title and description
st.title("Add New Item")
st.markdown("Add a new item to the DynamoDB database")

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Items')

# Create a form for adding new items
with st.form("add_item_form"):
    # Generate a random UUID for the ID field
    item_id = str(uuid.uuid4())
    st.text_input("Item ID", value=item_id, disabled=True, help="Unique identifier for the item")
    
    # Add required fields
    name = st.text_input("Name", help="Name of the item")
    description = st.text_area("Description", help="Description of the item")

    submitted = st.form_submit_button("Add Item")
    
    if submitted:
        try:
            # Create the item dictionary
            item = {
                'id': item_id,
                'name': name,
                'description': description
            }
            
            # Add item to DynamoDB
            table.put_item(Item=item)
            
            st.success("Item added successfully!")
            
            # Clear the form by rerunning the app
            st.rerun()
            
        except ClientError as e:
            st.error(f"Error adding item to DynamoDB: {str(e)}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")