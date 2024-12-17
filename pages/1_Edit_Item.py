import streamlit as st
import boto3
from botocore.exceptions import ClientError

# Configure the page
st.set_page_config(page_title="Edit Item", layout="wide")

# Add title and description
st.title("Edit Item")
st.markdown("Edit an existing item in the DynamoDB database")

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Items')

try:
    # Scan DynamoDB table to get all items
    response = table.scan()
    items = response.get('Items', [])
    
    if not items:
        st.warning("No items found in the database.")
    else:
        # Create a dropdown to select an item to edit
        item_names = {f"{item['id']} - {item['name']}": item for item in items}
        selected_item_key = st.selectbox(
            "Select an item to edit",
            options=list(item_names.keys()),
            format_func=lambda x: x.split(" - ")[1]  # Show only the name in the dropdown
        )
        
        if selected_item_key:
            selected_item = item_names[selected_item_key]
            
            # Create a form for editing the item
            with st.form("edit_item_form"):
                # Show the ID (disabled)
                st.text_input("Item ID", value=selected_item['id'], disabled=True, help="Unique identifier for the item")
                
                # Add editable fields with current values
                name = st.text_input("Name", value=selected_item['name'], help="Name of the item")
                description = st.text_area("Description", value=selected_item['description'], help="Description of the item")
                
                submitted = st.form_submit_button("Update Item")
                
                if submitted:
                    try:
                        # Create the updated item dictionary
                        updated_item = {
                            'id': selected_item['id'],
                            'name': name,
                            'description': description
                        }
                        
                        # Update item in DynamoDB
                        table.put_item(Item=updated_item)
                        
                        st.success("Item updated successfully!")
                        
                        # Rerun the app to refresh the data
                        st.rerun()
                        
                    except ClientError as e:
                        st.error(f"Error updating item in DynamoDB: {str(e)}")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

except ClientError as e:
    st.error(f"Error accessing DynamoDB: {str(e)}")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")