"""Ownership and size checks for binary media inputs."""

from contextlib import contextmanager
import io
import os
from typing import BinaryIO, Iterator, Union

MediaInput = Union[str, os.PathLike[str], bytes, bytearray, BinaryIO]
MAX_IMAGE_BYTES = 32 * 1024 * 1024
MAX_VIDEO_BYTES = 500 * 1024 * 1024
VIDEO_CONTENT_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
}


@contextmanager
def open_media(source: MediaInput) -> Iterator[tuple[BinaryIO, str | None]]:
    if isinstance(source, (str, os.PathLike)):
        path = os.fspath(source)
        with open(path, "rb") as file:
            yield file, os.path.basename(path)
    elif isinstance(source, (bytes, bytearray)):
        with io.BytesIO(source) as file:
            yield file, None
    elif callable(getattr(source, "read", None)):
        name = getattr(source, "name", None)
        yield source, os.fspath(name) if isinstance(name, (str, os.PathLike)) else None
    else:
        raise ValueError("Provide a file path, bytes, or an open binary file")


def image_bytes(file: BinaryIO) -> bytes:
    data = file.read(MAX_IMAGE_BYTES + 1)
    if not isinstance(data, bytes):
        raise ValueError("Image input must contain binary bytes")
    if not data:
        raise ValueError("Image input cannot be empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image input exceeds the 32 MiB limit")
    return data


def video_details(file: BinaryIO, name: str | None) -> tuple[str, str]:
    if not isinstance(name, str) or not name:
        raise ValueError(
            "filename is required for video bytes or a stream without a filename"
        )
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    extension = os.path.splitext(name)[1].lower()
    if (
        not name.isprintable()
        or len(name) > 255
        or extension not in VIDEO_CONTENT_TYPES
    ):
        raise ValueError("Video filename must end in .mp4, .mov, or .webm")
    try:
        position = file.tell()
        file.seek(0, os.SEEK_END)
        remaining = file.tell() - position
        file.seek(position)
        binary = file.read(0)
    except (OSError, AttributeError) as exc:
        raise ValueError(
            "Video input must be a seekable binary file; file paths and bytes are also supported"
        ) from exc
    if not isinstance(binary, bytes):
        raise ValueError("Video input must contain binary bytes")
    if not 0 < remaining <= MAX_VIDEO_BYTES:
        raise ValueError("Video input must be nonempty and at most 500 MiB")
    return name, VIDEO_CONTENT_TYPES[extension]
