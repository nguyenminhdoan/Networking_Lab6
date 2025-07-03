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
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Invalid JSON: {str(e)}"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        if not isinstance(data, list):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Expected a list of files."}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        results = []

        for item in data:
            filename = item.get("filename")
            base64_data = item.get("file")

            if not filename or not base64_data:
                results.append({
                    "filename": filename,
                    "error": "Missing 'filename' or 'file'"
                })
                continue

            if base64_data.startswith("data:"):
                base64_data = base64_data.split(",", 1)[1]

            try:
                file_bytes = base64.b64decode(base64_data)
            except Exception as e:
                results.append({
                    "filename": filename,
                    "error": f"Invalid base64 encoding: {str(e)}"
                })
                continue

            try:
                with Image.open(io.BytesIO(file_bytes)) as img:
                    img.verify()
            except Exception as e:
                results.append({
                    "filename": filename,
                    "error": f"Invalid image: {str(e)}"
                })
                continue

            try:
                s3.put_object(Bucket=BUCKET, Key=filename, Body=file_bytes)
                results.append({
                    "filename": filename,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "filename": filename,
                    "error": f"Failed to upload to S3: {str(e)}"
                })

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"results": results})
        }

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unexpected error: {str(e)}"}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }
