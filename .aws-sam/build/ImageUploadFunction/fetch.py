import json
import base64
import os
import boto3
import io
from PIL import Image
import logging

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client("s3")
BUCKET = os.environ.get("IMAGE_BUCKET", "aws-sam-cli-managed-default-samclisourcebucket-7cgg1brgpvvd")

def lambda_handler(event, context):
    try:
        # Get query parameters
        params = event.get("queryStringParameters") or {}
        filename = params.get("filename")
        width = params.get("width")
        height = params.get("height")

        if not filename:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'filename' parameter"}),
                "headers": {"Content-Type": "application/json"}
            }

        # Fetch original image from S3
        try:
            s3_response = s3.get_object(Bucket=BUCKET, Key=filename)
            original_image = s3_response["Body"].read()
        except Exception as e:
            logger.error(f"S3 fetch error: {str(e)}")
            return {
                "statusCode": 404,
                "body": json.dumps({"error": f"File '{filename}' not found"}),
                "headers": {"Content-Type": "application/json"}
            }

        # Resize image if needed
        if width or height:
            try:
                with Image.open(io.BytesIO(original_image)) as img:
                    width = int(width) if width else img.width
                    height = int(height) if height else img.height
                    img = img.resize((width, height))
                    buffer = io.BytesIO()
                    img.save(buffer, format=img.format)
                    buffer.seek(0)
                    image_bytes = buffer.read()
            except Exception as e:
                logger.error(f"Resize error: {str(e)}")
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": f"Failed to resize image: {str(e)}"}),
                    "headers": {"Content-Type": "application/json"}
                }
        else:
            image_bytes = original_image

        # Return image as Base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "filename": filename,
                "image_base64": base64_image
            }),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
