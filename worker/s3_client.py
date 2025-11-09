import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional


def get_s3_client():
    """Create and return an S3-compatible client (MinIO) configured from environment variables."""
    endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    access_key = os.getenv("S3_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("S3_SECRET_KEY", "minioadmin")
    bucket = os.getenv("S3_BUCKET", "audiogen-artifacts")

    print(f"Endpoint: {endpoint}")
    
    # Configure boto3 for MinIO (S3-compatible)
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        use_ssl=False  # MinIO typically runs without SSL in development
    )

    print(f"S3 client created")
    
    # Ensure bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket)
    except ClientError:
        # Bucket doesn't exist, create it
        try:
            s3_client.create_bucket(Bucket=bucket)
            print(f"Created bucket: {bucket}")
        except ClientError as e:
            print(f"Error creating bucket {bucket}: {str(e)}")
            raise
    
    return s3_client, bucket


def save_transcription_to_s3(content: str, song_id: str, song_name: str) -> Optional[str]:
    """Save MusicXML transcription content to S3/MinIO and return the object key.
    
    Args:
        content: MusicXML string content
        song_id: UUID of the song
        song_name: Name of the song (used in file path)
    
    Returns:
        Object key (path) in S3 bucket, or None if upload failed
    """
    try:
        s3_client, bucket = get_s3_client()
        # Generate object key: transcriptions/{song_id}/{song_name}.musicxml
        # Sanitize song_name for filesystem compatibility
        safe_song_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_song_name = safe_song_name.replace(' ', '_')
        object_key = f"transcriptions/{song_id}/{safe_song_name}.musicxml"
        print(f"Object key: {object_key}")
        
        # Upload content to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=content.encode('utf-8'),
            ContentType='application/xml'
        )
        
        # Construct URL (for MinIO, this will be the endpoint URL + bucket + key)
        endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
        url = f"{endpoint}/{bucket}/{object_key}"
        
        print(f"Saved transcription to S3: {url}")
        return url
        
    except Exception as e:
        print(f"Error saving transcription to S3: {str(e)}")
        return None

def get_transcription_from_s3(song_id: str, song_name: str) -> Optional[str]:
    """Get MusicXML transcription content from S3/MinIO and return the object key.
    
    Args:
        song_id: UUID of the song
        song_name: Name of the song (used in file path)
    Returns:
        Object key (path) in S3 bucket, or None if upload failed
    """
    try:
        s3_client, bucket = get_s3_client()
        safe_song_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_song_name = safe_song_name.replace(' ', '_')
        object_key = f"transcriptions/{song_id}/{safe_song_name}.musicxml"
        response = s3_client.get_object(Bucket=bucket, Key=object_key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error getting transcription from S3: {str(e)}")
        return None