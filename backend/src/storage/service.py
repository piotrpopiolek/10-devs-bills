import hashlib
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status
from supabase import create_client, Client
from src.config import settings

logger = logging.getLogger(__name__)

# Max file size: 20MB (Telegram allows up to 20MB for photos, 50MB for docs)
MAX_FILE_SIZE = 20 * 1024 * 1024

class StorageService:
    """
    Service for handling file uploads to Supabase Storage.
    Falls back to local storage if Supabase is not configured.
    """
    
    def __init__(self):
        self.supabase_client: Optional[Client] = None
        # Backend always prefers Service Role key for full access (bypass RLS)
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
        self.use_supabase = bool(settings.SUPABASE_URL and self.key)
        
        if self.use_supabase:
            try:
                self.supabase_client = create_client(
                    settings.SUPABASE_URL,
                    self.key
                )
                logger.info("Supabase Storage client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to local storage.")
                self.use_supabase = False
        
        # Local storage directory (fallback)
        if not self.use_supabase:
            self.local_storage_path = Path("uploads/bills")
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using local storage at {self.local_storage_path}")
    
    async def calculate_file_hash(self, file_content: bytes) -> str:
        """
        Calculate SHA256 hash of file content.
        """
        return hashlib.sha256(file_content).hexdigest()
    
    def generate_file_path(self, user_id: int, file_hash: str, extension: str) -> str:
        """
        Generate file path for storage: bills/{user_id}/{hash}.{ext}
        """
        return f"bills/{user_id}/{file_hash[:16]}.{extension}"
    
    async def upload_file_content(self, file_content: bytes, user_id: int, extension: str = "jpg", content_type: str = "image/jpeg") -> tuple[str, str]:
        """
        Upload raw file content (bytes) and return storage path and hash.
        Used by Telegram Bot service.
        """
        if len(file_content) > MAX_FILE_SIZE:
             raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024):.0f}MB")

        file_hash = await self.calculate_file_hash(file_content)
        file_path = self.generate_file_path(user_id, file_hash, extension)
        
        if self.use_supabase:
            if not self.supabase_client:
                 raise RuntimeError("Supabase client not initialized")
                 
            try:
                bucket_name = settings.SUPABASE_STORAGE_BUCKET
                # Use upsert=true to overwrite existing files
                self.supabase_client.storage.from_(bucket_name).upload(
                    path=file_path,
                    file=file_content,
                    file_options={"content-type": content_type, "upsert": "true"}
                )
                # Return the internal storage path, NOT the public URL
                # Access will be granted via signed URLs
                logger.info(f"File uploaded to Supabase: {file_path}")
                return file_path, file_hash
            except Exception as e:
                logger.error(f"Failed to upload to Supabase: {e}", exc_info=True)
                raise e
        else:
            # Local upload
            full_path = self.local_storage_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file_content)
            logger.info(f"File uploaded locally: {full_path}")
            # Return relative path consistent with storage path concept
            return str(file_path).replace("\\", "/"), file_hash
    
    def get_signed_url(self, file_path: str, expiry_seconds: int = 3600) -> str:
        """
        Generate a signed URL for a file in Supabase Storage.
        Valid for `expiry_seconds` (default 1 hour).
        """
        if not self.use_supabase:
             # Fallback for local storage (assuming static file serving)
             # This requires static mounting in main.py
             return f"{settings.WEB_APP_URL}/uploads/bills/{file_path}"

        if not self.supabase_client:
            return ""
            
        try:
            bucket_name = settings.SUPABASE_STORAGE_BUCKET
            response = self.supabase_client.storage.from_(bucket_name).create_signed_url(
                path=file_path,
                expires_in=expiry_seconds
            )
            return response['signedURL']
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}", exc_info=True)
            return ""
    
    def calculate_expiration_date(self, months: int = 6) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=months * 30)

_storage_service: Optional[StorageService] = None

def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
