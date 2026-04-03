from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ImageEntry:
    filename: str
    sha256: str
    size_bytes: int
    par2_filename: str
    b2_file_id: Optional[str] = None
    b2_par2_file_id: Optional[str] = None
    external_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "par2_filename": self.par2_filename,
            "b2_file_id": self.b2_file_id,
            "b2_par2_file_id": self.b2_par2_file_id,
            "external_path": self.external_path,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImageEntry":
        return cls(
            filename=d["filename"],
            sha256=d["sha256"],
            size_bytes=d["size_bytes"],
            par2_filename=d["par2_filename"],
            b2_file_id=d.get("b2_file_id"),
            b2_par2_file_id=d.get("b2_par2_file_id"),
            external_path=d.get("external_path"),
        )


@dataclass
class AlbumResult:
    year: str
    month: str
    day: str
    album_name: str
    added_at: str
    images: list[ImageEntry] = field(default_factory=list)
