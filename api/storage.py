import json
import os
import re
import uuid
from io import BytesIO
from pathlib import Path
from fastapi import HTTPException, UploadFile
from minio import Minio

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "chronicles")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm"}

def get_minio_client() -> Minio:
    return Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)

def media_url(stored_name: str | None, default_url: str) -> str:
    if not stored_name: return default_url
    if stored_name.startswith(("http://", "https://", "/")): return stored_name
    return f"{MINIO_PUBLIC_URL}/{MINIO_BUCKET}/{stored_name}"

def _latin_filename(original_name: str | None, suffix: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", Path(original_name or "media").stem.lower()).strip("-") or "media"
    return f"{stem}-{uuid.uuid4().hex[:12]}{suffix}"

async def upload_media(file: UploadFile, allowed: dict[str, str]) -> str:
    suffix = allowed.get(file.content_type or "")
    if suffix is None: raise HTTPException(status_code=422, detail="Недопустимый тип медиафайла")
    data = await file.read()
    if not data: raise HTTPException(status_code=422, detail="Медиафайл пуст")
    name = _latin_filename(file.filename, suffix)
    client = get_minio_client()
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
        client.set_bucket_policy(
            MINIO_BUCKET,
            json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"],
                }],
            }),
        )
    client.put_object(MINIO_BUCKET, name, BytesIO(data), len(data), content_type=file.content_type)
    return name
