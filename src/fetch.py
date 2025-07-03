import json
import base64
import os
import boto3
import io
from PIL import Image
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
BUCKET = os.environ.get("IMAGE_BUCKET", "aws-sam-cli-managed-default-samclisourcebucket-7cgg1brgpvvd")

def lambda_handler(event, context):
    try:
        params = event.get("queryStringParameters") or {}
        filenames_param = params.get("filenames")
        width = params.get("width")
        height = params.get("height")

        if not filenames_param:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'filenames' parameter"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        filenames = [f.strip() for f in filenames_param.split(",") if f.strip()]
        try:
            width = int(width) if width else None
            height = int(height) if height else None
        except ValueError:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Width and height must be integers"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        results = []

        for filename in filenames:
            try:
                s3_response = s3.get_object(Bucket=BUCKET, Key=filename)
                image_data = s3_response["Body"].read()
                image_bytes = io.BytesIO(image_data)
                image = Image.open(image_bytes)
                image_format = image.format if image.format else "JPEG"

                if width or height:
                    resized = image.resize((width or image.width, height or image.height))
                    output_buffer = io.BytesIO()
                    resized.save(output_buffer, format=image_format)
                    output_buffer.seek(0)
                    encoded = base64.b64encode(output_buffer.getvalue()).decode()
                else:
                    encoded = base64.b64encode(image_data).decode()

                results.append({
                    "filename": filename,
                    "format": image_format,
                    "image_base64": encoded,
                      "width": resized.width if width or height else image.width,
                    "height": resized.height if width or height else image.height
                })

            except Exception as e:
                logger.warning(f"Failed to process {filename}: {str(e)}")
                results.append({
                    "filename": filename,
                    "error": f"Could not fetch or process this image: {str(e)}"
                })

        return {
            "statusCode": 200,
            "body": json.dumps({"images": results}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }
