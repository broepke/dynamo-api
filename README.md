# Flask DynamoDB API

A RESTful API built with Flask that uses AWS DynamoDB as its backend database.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up AWS credentials:
Export your AWS credentials as environment variables:
```bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
```

3. Create DynamoDB table:
- Table Name: Items
- Partition Key: id (String)

## API Endpoints

### Get all items
```
GET /items
```

### Get a specific item
```
GET /items/<item_id>
```

### Create a new item
```
POST /items
Content-Type: application/json

{
    "id": "unique_id",
    "name": "item_name",
    "description": "item_description"
}
```

### Update an item
```
PUT /items/<item_id>
Content-Type: application/json

{
    "name": "updated_name",
    "description": "updated_description"
}
```

### Delete an item
```
DELETE /items/<item_id>
```

## Running the API

Start the Flask development server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Example Usage

Create an item:
```bash
curl -X POST http://localhost:5000/items \
  -H "Content-Type: application/json" \
  -d '{"id": "1", "name": "Test Item", "description": "This is a test item"}'
```

Get all items:
```bash
curl http://localhost:5000/items
```

Get a specific item:
```bash
curl http://localhost:5000/items/1
```

Update an item:
```bash
curl -X PUT http://localhost:5000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Item", "description": "This is an updated item"}'
```

Delete an item:
```bash
curl -X DELETE http://localhost:5000/items/1
