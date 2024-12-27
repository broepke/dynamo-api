pip install -r requirements.txt -t ./package


cp app.py ./package/


cd package && zip -r ../lambda.zip . && cd ..


aws lambda update-function-code --function-name DynamoAPI --zip-file fileb://lambda.zip