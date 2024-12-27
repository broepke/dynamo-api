#!/bin/bash

# Remove existing files
rm -rf package lambda.zip lvenv

# Create and activate virtual environment
python3.9 -m venv lvenv
source lvenv/bin/activate

# Create package directory
mkdir -p package

# Install dependencies
pip install -r requirements.txt --target ./package

# Copy lambda function to package directory
cp lambda_function.py ./package/

# Create deployment package
cd package && zip -r ../lambda.zip . && cd ..

# Cleanup
deactivate
rm -rf lvenv

# Update Lambda function
aws lambda update-function-code --function-name DynamoAPI --zip-file fileb://lambda.zip
