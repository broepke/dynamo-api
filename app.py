from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError
import os

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
    dynamodb = boto3.resource(
        "dynamodb",
        region_name="us-east-1",  # Change this to your preferred region
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    return dynamodb.Table("Items")


@app.get("/items", response_model=List[Dict[str, Any]])
async def get_items(table: Any = Depends(get_dynamodb)):
    try:
        response = table.scan()
        return response.get("Items", [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/items/{item_id}")
async def get_item(item_id: str, table: Any = Depends(get_dynamodb)):
    try:
        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/items/{item_id}/{property_name}")
async def get_item_property(
    item_id: str, property_name: str, table: Any = Depends(get_dynamodb)
):
    try:
        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        if property_name not in item:
            raise HTTPException(
                status_code=404, detail=f"Property '{property_name}' not found"
            )

        return {property_name: item[property_name]}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/items", status_code=201)
async def create_item(item: Dict[str, Any], table: Any = Depends(get_dynamodb)):
    try:
        table.put_item(Item=item)
        return item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/items/{item_id}")
async def update_item(
    item_id: str, item: Dict[str, Any], table: Any = Depends(get_dynamodb)
):
    try:
        item["id"] = item_id
        table.put_item(Item=item)
        return item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: str, table: Any = Depends(get_dynamodb)):
    try:
        table.delete_item(Key={"id": item_id})
        return None
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
