import concurrent.futures
import logging
import os
import tempfile
from typing import TYPE_CHECKING, Optional, Tuple

import tracklab
import tracklab.util
from tracklab.sdk.lib.paths import LogicalPath

if TYPE_CHECKING:
    from tracklab.sdk.artifacts.artifact_manifest import ArtifactManifest
    from tracklab.sdk.artifacts.artifact_saver import SaveFn
    from tracklab.sdk.internal import file_stream, internal_api
    from tracklab.sdk.internal.settings_static import SettingsStatic


logger = logging.getLogger(__name__)


class FilePusher:
    """File pusher stub for local logging.
    
    This class provides a minimal interface to maintain compatibility
    with the rest of the codebase, but doesn't actually upload files
    since this is a local logging library.
    """

    MAX_UPLOAD_JOBS = 64

    def __init__(
        self,
        api: "internal_api.Api",
        file_stream: "file_stream.FileStreamApi",
        settings: Optional["SettingsStatic"] = None,
    ) -> None:
        self._api = api
        self._tempdir = tempfile.TemporaryDirectory("tracklab")

    def get_status(self) -> Tuple[bool, None]:
        """Get status - always returns not running for local logging."""
        return False, None

    def print_status(self, prefix: bool = True) -> None:
        """Print status - no-op for local logging."""
        pass

    def file_counts_by_category(self) -> dict:
        """Get file counts - returns empty dict for local logging."""
        return {}

    def file_changed(self, save_name: LogicalPath, path: str, copy: bool = True):
        """File changed notification - no-op for local logging."""
        pass

    def store_manifest_files(
        self,
        manifest: "ArtifactManifest",
        artifact_id: str,
        save_fn: "SaveFn",
    ) -> None:
        """Store manifest files - no-op for local logging."""
        pass

    def commit_artifact(
        self,
        artifact_id: str,
        *,
        finalize: bool = True,
        before_commit: Optional[callable] = None,
        result_future: "concurrent.futures.Future[None]",
    ):
        """Commit artifact - immediately completes for local logging."""
        if result_future:
            result_future.set_result(None)

    def finish(self, callback: Optional[callable] = None):
        """Finish - immediately calls callback for local logging."""
        if callback:
            callback()

    def join(self) -> None:
        """Join - just cleans up tempdir for local logging."""
        self._tempdir.cleanup()

    def is_alive(self) -> bool:
        """Check if alive - always returns False for local logging."""
        return False