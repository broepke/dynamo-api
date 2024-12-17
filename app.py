import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError
from loguru import logger
import sys

# Configure Loguru
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Remove default logger
logger.remove()

# Add console logging with custom format
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add file logging with rotation
logger.add(
    os.path.join(log_directory, "dynamo-api.log"),
    rotation="10 MB",
    retention="1 week",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO"
)

app = FastAPI()

# Pydantic model for items
class Item(BaseModel):
    id: str
    # Making all other fields optional since DynamoDB is schema-less
    additional_properties: Dict[str, Any] = {}

    class Config:
        extra = "allow"  # Allows additional fields

# DynamoDB client setup as a dependency
def get_dynamodb():
    logger.info("Initializing DynamoDB connection")
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name="us-east-1",  # Change this to your preferred region
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
        return dynamodb.Table("Items")
    except Exception as e:
        logger.exception("Failed to initialize DynamoDB connection")
        raise

@app.get("/items", response_model=List[Dict[str, Any]])
async def get_items(table: Any = Depends(get_dynamodb)):
    logger.info("Handling GET request for all items")
    try:
        response = table.scan()
        items = response.get("Items", [])
        logger.success(f"Successfully retrieved {len(items)} items")
        return items
    except ClientError as e:
        logger.exception("DynamoDB error while fetching items")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error while fetching items")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/items/{item_id}")
async def get_item(item_id: str, table: Any = Depends(get_dynamodb)):
    logger.info(f"Handling GET request for item ID: {item_id}")
    try:
        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")
        if not item:
            logger.warning(f"Item not found with ID: {item_id}")
            raise HTTPException(status_code=404, detail="Item not found")
        logger.success(f"Successfully retrieved item: {item_id}")
        return item
    except ClientError as e:
        logger.exception(f"DynamoDB error while fetching item {item_id}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while fetching item {item_id}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/items/{item_id}/{property_name}")
async def get_item_property(
    item_id: str, property_name: str, table: Any = Depends(get_dynamodb)
):
    logger.info(f"Handling GET request for item ID: {item_id}, property: {property_name}")
    try:
        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")
        if not item:
            logger.warning(f"Item not found with ID: {item_id}")
            raise HTTPException(status_code=404, detail="Item not found")

        if property_name not in item:
            logger.warning(f"Property '{property_name}' not found for item {item_id}")
            raise HTTPException(
                status_code=404, detail=f"Property '{property_name}' not found"
            )

        logger.success(f"Successfully retrieved property {property_name} for item {item_id}")
        return {property_name: item[property_name]}
    except ClientError as e:
        logger.exception(f"DynamoDB error while fetching property {property_name} for item {item_id}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while fetching property {property_name} for item {item_id}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/items", status_code=201)
async def create_item(item: Dict[str, Any], table: Any = Depends(get_dynamodb)):
    logger.info(f"Handling POST request to create item with ID: {item.get('id')}")
    try:
        table.put_item(Item=item)
        logger.success(f"Successfully created item with ID: {item.get('id')}")
        return item
    except ClientError as e:
        logger.exception("DynamoDB error while creating item")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error while creating item")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/items/{item_id}")
async def update_item(
    item_id: str, item: Dict[str, Any], table: Any = Depends(get_dynamodb)
):
    logger.info(f"Handling PUT request to update item ID: {item_id}")
    try:
        item["id"] = item_id
        table.put_item(Item=item)
        logger.success(f"Successfully updated item: {item_id}")
        return item
    except ClientError as e:
        logger.exception(f"DynamoDB error while updating item {item_id}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error while updating item {item_id}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: str, table: Any = Depends(get_dynamodb)):
    logger.info(f"Handling DELETE request for item ID: {item_id}")
    try:
        table.delete_item(Key={"id": item_id})
        logger.success(f"Successfully deleted item: {item_id}")
        return None
    except ClientError as e:
        logger.exception(f"DynamoDB error while deleting item {item_id}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error while deleting item {item_id}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Dynamo API server")
    uvicorn.run(app, host="127.0.0.1", port=8000)
