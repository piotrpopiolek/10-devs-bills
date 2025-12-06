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
        self.use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY)
        
        if self.use_supabase:
            try:
                self.supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
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
        Upload raw file content (bytes) and return URL and hash.
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
                self.supabase_client.storage.from_(bucket_name).upload(
                    path=file_path,
                    file=file_content,
                    file_options={"content-type": content_type}
                )
                public_url = self.supabase_client.storage.from_(bucket_name).get_public_url(file_path)
                logger.info(f"File uploaded to Supabase: {file_path}")
                return public_url, file_hash
            except Exception as e:
                logger.error(f"Failed to upload to Supabase: {e}", exc_info=True)
                # Fallback or re-raise? Re-raising to let caller know
                raise e
        else:
            # Local upload
            full_path = self.local_storage_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file_content)
            logger.info(f"File uploaded locally: {full_path}")
            return f"/uploads/bills/{file_path}", file_hash
    
    def calculate_expiration_date(self, months: int = 6) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=months * 30)

_storage_service: Optional[StorageService] = None

def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service

