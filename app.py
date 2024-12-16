from flask import Flask, jsonify, request
import boto3
from botocore.exceptions import ClientError
import os

app = Flask(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',  # Change this to your preferred region
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

# Sample table name - you'll need to create this table in DynamoDB
TABLE_NAME = 'Items'
table = dynamodb.Table(TABLE_NAME)

@app.route('/items', methods=['GET'])
def get_items():
    try:
        response = table.scan()
        items = response.get('Items', [])
        return jsonify(items)
    except ClientError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<string:item_id>', methods=['GET'])
def get_item(item_id):
    try:
        response = table.get_item(Key={'id': item_id})
        item = response.get('Item')
        if item:
            return jsonify(item)
        return jsonify({'error': 'Item not found'}), 404
    except ClientError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items', methods=['POST'])
def create_item():
    try:
        item = request.json
        table.put_item(Item=item)
        return jsonify(item), 201
    except ClientError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<string:item_id>', methods=['PUT'])
def update_item(item_id):
    try:
        item = request.json
        item['id'] = item_id
        table.put_item(Item=item)
        return jsonify(item)
    except ClientError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<string:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        table.delete_item(Key={'id': item_id})
        return '', 204
    except ClientError as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)