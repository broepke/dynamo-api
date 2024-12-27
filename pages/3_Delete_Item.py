import streamlit as st
import requests

# Configure the page
st.set_page_config(page_title="Delete Item", layout="wide")

# Add title and description
st.title("Delete Item")
st.markdown("Delete an existing item from the database")

# Configure API URL
API_URL = "https://api.dataknowsall.com"  # Update this if your Flask API is running on a different URL

try:
    # Get all items from API
    response = requests.get(f"{API_URL}/items")
    response.raise_for_status()
    items = response.json()
    
    if not items:
        st.warning("No items found in the database.")
    else:
        # Create a dropdown to select an item to delete
        item_names = {f"{item['id']} - {item['name']}": item for item in items}
        selected_item_key = st.selectbox(
            "Select an item to delete",
            options=list(item_names.keys()),
            format_func=lambda x: x.split(" - ")[1]  # Show only the name in the dropdown
        )
        
        if selected_item_key:
            selected_item = item_names[selected_item_key]
            
            # Display item details
            st.subheader("Item Details")
            st.text(f"ID: {selected_item['id']}")
            st.text(f"Name: {selected_item['name']}")
            
            # Add a delete confirmation
            st.warning("⚠️ Warning: This action cannot be undone!")
            if st.button("Delete Item", type="primary"):
                try:
                    # Delete item using API
                    response = requests.delete(f"{API_URL}/items/{selected_item['id']}")
                    response.raise_for_status()
                    
                    st.success("Item deleted successfully!")
                    
                    # Rerun the app to refresh the data
                    # st.rerun()
                    
                except requests.RequestException as e:
                    st.error(f"Error deleting item: {str(e)}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

except requests.RequestException as e:
    st.error(f"Error accessing API: {str(e)}")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
