import mimetypes
import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]
SUPABASE_STORAGE_BUCKET = os.environ["SUPABASE_STORAGE_BUCKET"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY,
)


def upload_file(file_path: str, storage_path: str) -> None:
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    with open(file_path, "rb") as file:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            path=storage_path,
            file=file,
            file_options={
                "upsert": "true",
                "content-type": content_type,
            },
        )


def delete_file(storage_path: str) -> None:
    supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove(
        [storage_path]
    )


def list_files() -> list[str]:
    response = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).list()

    return [
        item["name"]
        for item in response
        if item.get("name")
    ]