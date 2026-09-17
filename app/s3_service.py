import io
import zipfile
import boto3
from app.config import AWS_REGION, S3_BUCKET_NAME

s3_client = boto3.client("s3", region_name=AWS_REGION)


def upload_bytes_to_s3(file_bytes: bytes, s3_key: str, content_type: str) -> str:
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type
    )
    return s3_key


def download_bytes_from_s3(s3_key: str) -> bytes:
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
    return response["Body"].read()


def create_zip_package(polaroid_keys: list[str]) -> io.BytesIO:
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for s3_key in polaroid_keys:
            file_bytes = download_bytes_from_s3(s3_key)
            file_name = s3_key.split("/")[-1]
            zip_file.writestr(file_name, file_bytes)

    zip_buffer.seek(0)
    return zip_buffer