import logging
import json
import base64
from fastapi import FastAPI, HTTPException, Depends, APIRouter, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
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

# Create v1 router
v1_router = APIRouter(prefix="/v1")


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


# Pydantic models
class Item(BaseModel):
    id: str
    # Making all other fields optional since DynamoDB is schema-less
    additional_properties: Dict[str, Any] = {}

    class Config:
        extra = "allow"  # Allows additional fields


class PaginatedResponse(BaseModel):
    items: List[Dict[str, Any]]
    next_cursor: Optional[str] = None


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


# Original routes
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


# V1 routes
@v1_router.get(
    "/items",
    response_model=PaginatedResponse,
    summary="Retrieve paginated list of items",
    description="""
Fetch a paginated list of items from the DynamoDB table.
- Use the `limit` parameter to specify the number of items to fetch.
- Use the `cursor` parameter for pagination, to fetch the next set of items.
""",
)
async def get_items_v1(
    limit: int = Query(
        10, ge=1, le=100, description="Number of items to fetch (1-100)"
    ),
    cursor: Optional[str] = Query(
        None, description="Pagination cursor for fetching the next set of items"
    ),
    table: Any = Depends(get_dynamodb),
):
    logger.info(
        f"Handling GET request for items with limit {limit} and cursor {cursor}"
    )
    try:
        scan_kwargs = {"Limit": limit}

        if cursor:
            try:
                last_evaluated_key = json.loads(
                    base64.b64decode(cursor.encode()).decode()
                )
                scan_kwargs["ExclusiveStartKey"] = last_evaluated_key
            except Exception as e:
                logger.error(f"Invalid cursor format: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid cursor format")

        response = table.scan(**scan_kwargs)
        items = response.get("Items", [])

        next_cursor = None
        if "LastEvaluatedKey" in response:
            next_cursor = base64.b64encode(
                json.dumps(response["LastEvaluatedKey"]).encode()
            ).decode()

        logger.info(f"Successfully retrieved {len(items)} items")
        return PaginatedResponse(items=items, next_cursor=next_cursor)
    except ClientError as e:
        logger.error(f"DynamoDB error while fetching items: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while fetching items: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@v1_router.get("/items/{item_id}")
async def get_item_v1(item_id: str, table: Any = Depends(get_dynamodb)):
    return await get_item(item_id, table)


@v1_router.get("/items/{item_id}/{property_name}")
async def get_item_property_v1(
    item_id: str, property_name: str, table: Any = Depends(get_dynamodb)
):
    return await get_item_property(item_id, property_name, table)


@v1_router.post("/items", status_code=201)
async def create_item_v1(item: Dict[str, Any], table: Any = Depends(get_dynamodb)):
    return await create_item(item, table)


@v1_router.put("/items/{item_id}")
async def update_item_v1(
    item_id: str, item: Dict[str, Any], table: Any = Depends(get_dynamodb)
):
    return await update_item(item_id, item, table)


@v1_router.delete("/items/{item_id}", status_code=204)
async def delete_item_v1(item_id: str, table: Any = Depends(get_dynamodb)):
    return await delete_item(item_id, table)


# Include v1 router in the main app
app.include_router(v1_router)

# Create Lambda handler with API Gateway v2 configuration
handler = Mangum(app, lifespan="off", api_gateway_base_path="/default")

# Export the handler as lambda_handler for AWS Lambda
lambda_handler = handler
