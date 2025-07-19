"""File operations related API methods."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from tracklab.apis.normalize import normalize_exceptions
from tracklab.sdk.lib.hashutil import B64MD5, md5_file_b64

logger = logging.getLogger(__name__)


class FilesMixin:
    """File operations related API methods."""
    
    @normalize_exceptions
    def create_run_files_introspection(self) -> bool:
        """Check if server supports create run files.
        
        For local TrackLab, returns True.
        """
        return True
        
    @normalize_exceptions
    def upload_urls(
        self,
        project: str,
        files: List[str],
        entity: Optional[str] = None,
        run: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Optional[str]]:
        """Get upload URLs for files.
        
        For local TrackLab, returns local file paths.
        """
        upload_headers = {}
        file_info = {}
        
        for file_path in files:
            file_info[file_path] = {
                "uploadUrl": f"file://{os.path.abspath(file_path)}",
                "uploadHeaders": [],
            }
            
        return file_info, upload_headers, None
        
    @normalize_exceptions
    def download_urls(
        self,
        project: str,
        files: Optional[List[str]] = None,
        entity: Optional[str] = None,
        run: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]], Optional[str]]:
        """Get download URLs for files.
        
        For local TrackLab, returns local file paths.
        """
        file_info = []
        download_headers = {}
        
        if files:
            for file_name in files:
                file_info.append({
                    "name": file_name,
                    "url": f"file://{file_name}",
                    "size": 0,
                    "mimetype": "application/octet-stream",
                })
                
        return file_info, download_headers, None
        
    @normalize_exceptions
    def download_url(
        self,
        project: str,
        file: str,
        entity: Optional[str] = None,
        run: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Get download URL for a single file.
        
        For local TrackLab, returns local file path.
        """
        file_info = {
            "name": file,
            "url": f"file://{file}",
            "size": 0,
            "mimetype": "application/octet-stream",
        }
        return file_info, {}
        
    @normalize_exceptions
    def download_file(self, url: str) -> Tuple[int, requests.Response]:
        """Initiate a streaming download.
        
        For local TrackLab, returns mock response.
        """
        # Create a mock response
        response = requests.Response()
        response.status_code = 200
        response._content = b""
        return 0, response
        
    @normalize_exceptions
    def download_write_file(
        self,
        response: requests.Response,
        file: Any,
        progress_callback: Optional[Any] = None,
    ) -> None:
        """Download and write file content.
        
        For local TrackLab, this is a no-op.
        """
        pass
        
    def upload_file_azure(
        self, url: str, file: Any, extra_headers: Dict[str, str]
    ) -> requests.Response:
        """Upload file to Azure.
        
        For local TrackLab, returns mock response.
        """
        response = requests.Response()
        response.status_code = 200
        return response
        
    def upload_multipart_file_chunk(
        self,
        url: str,
        file: Any,
        part_number: int,
        offset: int,
        content_length: int,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload a chunk of a multipart file.
        
        For local TrackLab, returns mock ETag.
        """
        return f"etag-{part_number}"
        
    def upload_file(
        self,
        url: str,
        file: Any,
        callback: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Upload a file.
        
        For local TrackLab, this is a no-op.
        """
        logger.info(f"Local file upload: {url}")
        
    @staticmethod
    def file_current(fname: str, md5: B64MD5) -> bool:
        """Checksum a file and compare the md5 with the known md5."""
        if os.path.exists(fname):
            return md5_file_b64(fname) == md5
        return False
        
    @normalize_exceptions
    def pull(
        self, project: str, run: Optional[str] = None, entity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Pull files from a run.
        
        For local TrackLab, returns empty list.
        """
        return []
        
    @normalize_exceptions
    def push(
        self,
        files: List[str],
        entity: Optional[str] = None,
        project: Optional[str] = None,
        description: Optional[str] = None,
        force: bool = True,
        progress_fn: Optional[Any] = None,
    ) -> Optional[str]:
        """Push files to a run.
        
        For local TrackLab, returns None.
        """
        logger.info(f"Local file push: {len(files)} files")
        return None