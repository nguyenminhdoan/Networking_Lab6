import json
import base64
import boto3
import os

s3 = boto3.client('s3')
BUCKET = os.environ.get('IMAGE_BUCKET', 'your-bucket-name')

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        file_data = base64.b64decode(body["file"])
        filename = body["filename"]
        s3.put_object(Bucket=BUCKET, Key=filename, Body=file_data)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Upload successful", "filename": filename})
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
