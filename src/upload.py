import json
import base64
import boto3
import os
import io
from PIL import Image
import logging

# Set up logging
logging.getLogger().setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client("s3")
BUCKET = os.environ.get('IMAGE_BUCKET', 'aws-sam-cli-managed-default-samclisourcebucket-7cgg1brgpvvd')


def lambda_handler(event, context):
    try:
        logging.info(f"Event received: {json.dumps(event)[:500]}...")

        body = event.get("body")
        if not body:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Empty request body"}),
                "headers": {"Content-Type": "application/json"}
            }

        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Invalid JSON: {str(e)}"}),
                "headers": {"Content-Type": "application/json"}
            }

        filename = data.get("filename")
        base64_data = data.get("file")

        if not filename or not base64_data:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'filename' or 'file' in request"}),
                "headers": {"Content-Type": "application/json"}
            }

        # Strip data URI prefix if present
        if base64_data.startswith("data:"):
            base64_data = base64_data.split(",", 1)[1]

        try:
            file_bytes = base64.b64decode(base64_data)
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Invalid base64 encoding: {str(e)}"}),
                "headers": {"Content-Type": "application/json"}
            }

        # Validate image
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()  # Confirm it's a valid image
        except Exception as e:
            logging.error(f"Invalid image: {filename} | {str(e)}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"{filename} is not a valid image.",
                    "first_bytes": str(file_bytes[:20])
                }),
                "headers": {"Content-Type": "application/json"}
            }

        # Upload to S3
        try:
            s3.put_object(Bucket=BUCKET, Key=filename, Body=file_bytes)
            logging.info(f"Uploaded {filename} to bucket {BUCKET}")
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Failed to upload to S3: {str(e)}"}),
                "headers": {"Content-Type": "application/json"}
            }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "Upload successful", "filename": filename})
        }

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unexpected error: {str(e)}"}),
            "headers": {"Content-Type": "application/json"}
        }
