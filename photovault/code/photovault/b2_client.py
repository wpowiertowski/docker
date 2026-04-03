from pathlib import Path

from b2sdk.v2 import B2Api, InMemoryAccountInfo


class B2Client:
    def __init__(self, key_id: str, app_key: str, bucket_name: str):
        """Initialise b2sdk InMemoryAccountInfo + authorize."""
        info = InMemoryAccountInfo()
        self._api = B2Api(info)
        self._api.authorize_account("production", key_id, app_key)
        self._bucket = self._api.get_bucket_by_name(bucket_name)

    def upload_file(self, local_path: Path, b2_path: str) -> str:
        """Upload file, return b2 file_id."""
        file_info = self._bucket.upload_local_file(
            local_file=str(local_path),
            file_name=b2_path,
        )
        return file_info.id_

    def download_file(self, b2_path: str, local_path: Path) -> None:
        """Download file from B2 to local path."""
        local_path.parent.mkdir(parents=True, exist_ok=True)
        download = self._bucket.download_file_by_name(b2_path)
        download.save_to(str(local_path))

    def list_files(self, prefix: str) -> list[str]:
        """List files under a B2 prefix."""
        return [
            f.file_name
            for f, _ in self._bucket.ls(folder_to_list=prefix, recursive=True)
        ]
