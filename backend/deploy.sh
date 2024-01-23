#!/usr/bin/bash

# Your AWS SAM stack name
STACK_NAME="serverless-pdf-chat"

#create bucket
random_string=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
s3_bucket_name="serverless-pdf-chat-bucket${random_string}"

# aws s3 mb s3://${s3_bucket_name}
# echo "s3_bucket = ${s3_bucket_name}" >> .samconfig.toml

# Deploy SAM application
sam deploy --config-file samconfig.toml --stack-name "serverless-pdf-chat" --template-file template.yaml --region "us-east-1" --no-confirm-changeset

# # Fetch Cognito information
api_endpoint=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayBaseUrl'].OutputValue" --output text)
user_pool_id=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='CognitoUserPool'].OutputValue" --output text)
user_pool_client_id=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='CognitoUserPoolClient'].OutputValue" --output text)

# # Create .env.development file in root/frontend
echo "VITE_REGION=us-east-1" > ../frontend/.env.development
echo "VITE_API_ENDPOINT=$api_endpoint" >> ../frontend/.env.development
echo "VITE_USER_POOL_ID=$user_pool_id" >> ../frontend/.env.development
echo "VITE_USER_POOL_CLIENT_ID=$user_pool_client_id" >> ../frontend/.env.development

cd ../frontend/
npm run dev