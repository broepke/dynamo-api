# DynamoDB API Lambda Function

A FastAPI-based Lambda function that provides a RESTful API interface to DynamoDB.

## Setup and Deployment

### Prerequisites

- Python 3.9
- AWS CLI configured with appropriate credentials
- A DynamoDB table named "Items" (or update the table name in the code)

### Deployment Steps

1. Clone the repository
2. Install dependencies locally (if needed):
   ```bash
   pip install -r requirements_local.txt
   ```
3. Make the deploy script executable:
   ```bash
   chmod +x deploy.sh
   ```
4. Deploy to AWS Lambda:
   ```bash
   ./deploy.sh
   ```

The deploy script will:
- Create a clean package directory
- Install dependencies
- Package the Lambda function with dependencies
- Update the Lambda function code

## IAM Permissions

The Lambda function needs permissions to access DynamoDB. Add this inline policy to your Lambda function's execution role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:DeleteItem",
                "dynamodb:Scan",
                "dynamodb:Query",
                "dynamodb:UpdateItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/Items"
        }
    ]
}
```

To add the policy:
1. Go to AWS Lambda console
2. Click on your function
3. Go to "Configuration" > "Permissions"
4. Click on the IAM role link
5. In IAM console, click "Add permissions" > "Create inline policy"
6. Switch to JSON editor and paste the policy above
7. Name it (e.g., "DynamoDBAccess") and create the policy

## Testing

### Test Events

The function can be tested using API Gateway v2 formatted test events. Here are examples for different operations:

#### GET All Items
```json
{
  "version": "2.0",
  "routeKey": "GET /items",
  "rawPath": "/items",
  "rawQueryString": "",
  "headers": {
    "accept": "*/*",
    "content-length": "0",
    "host": "your-api-id.execute-api.region.amazonaws.com",
    "user-agent": "curl/7.64.1",
    "x-amzn-trace-id": "Root=1-5e6722a7-cc56xmpl46db7ae02d4da47dd",
    "x-forwarded-for": "1.2.3.4",
    "x-forwarded-port": "443",
    "x-forwarded-proto": "https"
  },
  "requestContext": {
    "accountId": "123456789012",
    "apiId": "api-id",
    "domainName": "your-api-id.execute-api.region.amazonaws.com",
    "domainPrefix": "your-api-id",
    "http": {
      "method": "GET",
      "path": "/items",
      "protocol": "HTTP/1.1",
      "sourceIp": "1.2.3.4",
      "userAgent": "curl/7.64.1"
    },
    "requestId": "JKJaXmPLvHcESHA=",
    "routeKey": "GET /items",
    "stage": "$default",
    "time": "10/Mar/2024:13:40:52 +0000",
    "timeEpoch": 1583856052000
  },
  "isBase64Encoded": false
}
```

#### POST New Item
```json
{
  "version": "2.0",
  "routeKey": "POST /items",
  "rawPath": "/items",
  "rawQueryString": "",
  "headers": {
    "accept": "application/json",
    "content-type": "application/json",
    "content-length": "39",
    "host": "your-api-id.execute-api.region.amazonaws.com",
    "user-agent": "curl/7.64.1",
    "x-amzn-trace-id": "Root=1-5e6722a7-cc56xmpl46db7ae02d4da47dd",
    "x-forwarded-for": "1.2.3.4",
    "x-forwarded-port": "443",
    "x-forwarded-proto": "https"
  },
  "requestContext": {
    "accountId": "123456789012",
    "apiId": "api-id",
    "domainName": "your-api-id.execute-api.region.amazonaws.com",
    "domainPrefix": "your-api-id",
    "http": {
      "method": "POST",
      "path": "/items",
      "protocol": "HTTP/1.1",
      "sourceIp": "1.2.3.4",
      "userAgent": "curl/7.64.1"
    },
    "requestId": "JKJaXmPLvHcESHA=",
    "routeKey": "POST /items",
    "stage": "$default",
    "time": "10/Mar/2024:13:40:52 +0000",
    "timeEpoch": 1583856052000
  },
  "body": "{\"id\": \"test-item-1\", \"name\": \"Test Item\"}",
  "isBase64Encoded": false
}
```

To use these test events:
1. Go to AWS Lambda console
2. Select your function
3. Click the "Test" tab
4. Click "Create new event"
5. Give it a name (e.g., "GetItemsTest" or "CreateItemTest")
6. Paste the appropriate JSON
7. Click "Save" and "Test"

## API Endpoints
**Note**: In order for the API gateway to work, each of the following Routes need to be added explicitly in the API Gateway console and attached to the Lambda function.

- GET /items - List all items
- GET /items/{item_id} - Get a specific item
- GET /items/{item_id}/{property_name} - Get a specific property of an item
- POST /items - Create a new item
- PUT /items/{item_id} - Update an item
- DELETE /items/{item_id} - Delete an item

## Logging

The function uses Loguru for logging, configured to:
- Write logs to CloudWatch
- Store rotating logs in /tmp/logs (Lambda's writable directory)
- Include timestamps, log levels, and detailed context

## Dependencies

Key dependencies (see requirements.txt for versions):
- fastapi - Web framework
- pydantic - Data validation
- mangum - AWS Lambda/API Gateway integration
- boto3 - AWS SDK (included in Lambda runtime)
