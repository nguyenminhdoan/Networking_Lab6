import boto3
import io
import os
from PIL import Image
from base64 import b64encode
import urllib.parse

s3 = boto3.client('s3')
BUCKET = os.environ.get('IMAGE_BUCKET', 'your-bucket-name')

def resize_image(image_data, width, height):
    img = Image.open(io.BytesIO(image_data))
    img = img.resize((int(width), int(height)))
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()

def lambda_handler(event, context):
    try:
        query = event['queryStringParameters']
        filename = query.get('filename')
        width = query.get('width')
        height = query.get('height')

        obj = s3.get_object(Bucket=BUCKET, Key=filename)
        file_content = obj['Body'].read()

        if width and height:
            file_content = resize_image(file_content, width, height)

        return {
            'statusCode': 200,
            'body': b64encode(file_content).decode('utf-8'),
            'isBase64Encoded': True,
            'headers': {'Content-Type': 'image/jpeg'}
        }
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}
