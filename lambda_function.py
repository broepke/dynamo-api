import os
import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError
from mangum import Mangum

# Configure logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Lambda automatically captures logs from stdout/stderr and sends to CloudWatch
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI()


@app.get("/")
async def root():
    logger.info("Root path accessed")
    logger.info(f"FastAPI root_path: {app.root_path}")
    return {
        "routes": [{"path": route.path, "name": route.name} for route in app.routes]
    }


@app.get("/health")
async def health():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}


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
        # Let Lambda use its IAM role
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        return dynamodb.Table("Items")
    except Exception as e:
        logger.error(
            f"Failed to initialize DynamoDB connection: {str(e)}", exc_info=True
        )
        raise


@app.get("/items", response_model=List[Dict[str, Any]])
async def get_items(table: Any = Depends(get_dynamodb)):
    logger.info("Handling GET request for all items")
    # Add request path logging
    logger.info("FastAPI root_path: %s", app.root_path)
    logger.info("FastAPI routes: %s", [route.path for route in app.routes])
    try:
        response = table.scan()
        items = response.get("Items", [])
        logger.info(f"Successfully retrieved {len(items)} items")
        return items
    except ClientError as e:
        logger.error(f"DynamoDB error while fetching items: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while fetching items: {str(e)}", exc_info=True)
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
        logger.info(f"Successfully retrieved item: {item_id}")
        return item
    except ClientError as e:
        logger.error(
            f"DynamoDB error while fetching item {item_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error while fetching item {item_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/items/{item_id}/{property_name}")
async def get_item_property(
    item_id: str, property_name: str, table: Any = Depends(get_dynamodb)
):
    logger.info(
        f"Handling GET request for item ID: {item_id}, property: {property_name}"
    )
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

        logger.info(
            f"Successfully retrieved property {property_name} for item {item_id}"
        )
        return {property_name: item[property_name]}
    except ClientError as e:
        logger.error(
            f"DynamoDB error while fetching property {property_name} for item {item_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error while fetching property {property_name} for item {item_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/items", status_code=201)
async def create_item(item: Dict[str, Any], table: Any = Depends(get_dynamodb)):
    logger.info(f"Handling POST request to create item with ID: {item.get('id')}")
    try:
        table.put_item(Item=item)
        logger.info(f"Successfully created item with ID: {item.get('id')}")
        return item
    except ClientError as e:
        logger.error(f"DynamoDB error while creating item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while creating item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/items/{item_id}")
async def update_item(
    item_id: str, item: Dict[str, Any], table: Any = Depends(get_dynamodb)
):
    logger.info(f"Handling PUT request to update item ID: {item_id}")
    try:
        item["id"] = item_id
        table.put_item(Item=item)
        logger.info(f"Successfully updated item: {item_id}")
        return item
    except ClientError as e:
        logger.error(
            f"DynamoDB error while updating item {item_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error while updating item {item_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: str, table: Any = Depends(get_dynamodb)):
    logger.info(f"Handling DELETE request for item ID: {item_id}")
    try:
        table.delete_item(Key={"id": item_id})
        logger.info(f"Successfully deleted item: {item_id}")
        return None
    except ClientError as e:
        logger.error(
            f"DynamoDB error while deleting item {item_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error while deleting item {item_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


# Create Lambda handler with API Gateway v2 configuration
handler = Mangum(app, lifespan="off", api_gateway_base_path="/default")

# Export the handler as lambda_handler for AWS Lambda
lambda_handler = handler
