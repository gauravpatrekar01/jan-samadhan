import boto3
from botocore.exceptions import ClientError
from config import settings
import logging
import uuid
import os

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def generate_presigned_url(self, file_name: str, file_type: str, expiration=3600):
        """Generate a presigned URL for direct client upload to S3."""
        object_name = f"uploads/{uuid.uuid4()}-{file_name}"
        try:
            response = self.s3_client.generate_presigned_post(
                self.bucket_name,
                object_name,
                Fields={"Content-Type": file_type},
                Conditions=[{"Content-Type": file_type}],
                ExpiresIn=expiration
            )
            return {
                "url": response["url"],
                "fields": response["fields"],
                "file_url": f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
            }
        except ClientError as e:
            logger.error(f"S3 Error: {e}")
            return None

    def upload_file(self, file_content, file_name, folder="complaints"):
        """Utility for backend-side upload if needed."""
        object_name = f"{folder}/{uuid.uuid4()}-{file_name}"
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_content
            )
            return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}")
            return None

s3_service = S3Service()
