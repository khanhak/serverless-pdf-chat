#!/usr/bin/bash
cd backend
# Your AWS SAM stack name
STACK_NAME="serverless-rizzpiss"

#Create samconfig.toml
echo "version = 0.1" > samconfig.toml
echo "[default.deploy.parameters]" >> samconfig.toml
echo "stack_name = \"$STACK_NAME\"" >> samconfig.toml
echo "resolve_s3 = true" >> samconfig.toml
echo "s3_prefix = \"$STACK_NAME\"" >> samconfig.toml
echo "region = \"us-east-1\"" >> samconfig.toml
echo "confirm_changeset = true" >> samconfig.toml
echo "capabilities = \"CAPABILITY_IAM\"" >> samconfig.toml
echo "disable_rollback = false" >> samconfig.toml
echo "parameter_overrides = \"Frontend=\\\"local\\\" Repository=\\\"\\\"\"" >> samconfig.toml
echo "image_repositories = []" >> samconfig.toml


#create bucket
# random_string=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
# s3_bucket_name="serverless-pdf-chat-bucket${random_string}"

sam build --parallel
# Deploy SAM application
sam deploy --stack-name $STACK_NAME --region "us-east-1" --no-confirm-changeset

# # Fetch Cognito information
api_endpoint=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayBaseUrl'].OutputValue" --output text)
user_pool_id=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='CognitoUserPool'].OutputValue" --output text)
user_pool_client_id=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='CognitoUserPoolClient'].OutputValue" --output text)

#create & confirm sample cognito user
aws cognito-idp sign-up   --region "us-east-1"   --client-id $user_pool_client_id   --username a@a.com   --password qwertyuiop
aws cognito-idp admin-confirm-sign-up   --region "us-east-1"   --user-pool-id $user_pool_id   --username a@a.com

# # Create .env.development file in root/frontend
echo "VITE_REGION=us-east-1" > ../frontend/.env.development
echo "VITE_API_ENDPOINT=$api_endpoint" >> ../frontend/.env.development
echo "VITE_USER_POOL_ID=$user_pool_id" >> ../frontend/.env.development
echo "VITE_USER_POOL_CLIENT_ID=$user_pool_client_id" >> ../frontend/.env.development

cd ../frontend/
npm run dev