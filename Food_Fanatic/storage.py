"""Supabase Storage backend for durable public restaurant media."""

import mimetypes
from functools import cached_property
from urllib.parse import quote

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, Storage

from .imaging import compress_image


class CompressedFileSystemStorage(FileSystemStorage):
    """Local-development counterpart to the compression done on upload."""

    def _save(self, name, content):
        compressed = compress_image(content)
        return super()._save(name, compressed if compressed is not None else content)


class SupabaseStorage(Storage):
    """Store media in a public Supabase Storage bucket.

    The service-role key is only used by Django for uploads and deletions.  URLs
    returned to browsers contain no credentials and work because this bucket is
    intentionally public for restaurant menu photography.
    """

    def __init__(self, url=None, key=None, bucket_name=None, **kwargs):
        super().__init__(**kwargs)
        self.url_base = (url or "").rstrip("/")
        self.key = key or ""
        self.bucket_name = bucket_name or "foodfanatic-media"
        if not self.url_base or not self.key:
            raise ImproperlyConfigured(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for "
                "Supabase media storage."
            )

    @cached_property
    def client(self):
        # Keep this import lazy so local development does not require Supabase
        # unless the storage backend is actually enabled.
        from supabase import create_client

        return create_client(self.url_base, self.key)

    @property
    def bucket(self):
        return self.client.storage.from_(self.bucket_name)

    def _save(self, name, content):
        if hasattr(content, "seek"):
            content.seek(0)
        content_type = getattr(content, "content_type", None)
        if not content_type:
            content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"

        # Resize before upload. compress_image preserves the container format,
        # so the name and the content type stay accurate.
        compressed = compress_image(content)
        if compressed is not None:
            content = compressed

        self.bucket.upload(
            path=name,
            file=content.read(),
            file_options={
                "cache-control": "31536000",
                "content-type": content_type,
                "upsert": "false",
            },
        )
        return name

    def _open(self, name, mode="rb"):
        return ContentFile(self.bucket.download(name), name=name)

    def delete(self, name):
        self.bucket.remove([name])

    def exists(self, name):
        return self.bucket.exists(name)

    def listdir(self, path):
        objects = self.bucket.list(path, {"limit": 1000, "offset": 0})
        directories = []
        files = []
        for item in objects:
            name = item.get("name", "")
            if item.get("metadata") is None:
                directories.append(name)
            else:
                files.append(name)
        return directories, files

    def size(self, name):
        return self.bucket.info(name).get("metadata", {}).get("size", 0)

    def url(self, name):
        bucket = quote(self.bucket_name, safe="")
        object_name = quote(name, safe="/")
        return f"{self.url_base}/storage/v1/object/public/{bucket}/{object_name}"
