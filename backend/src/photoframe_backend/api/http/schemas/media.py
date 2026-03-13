from pydantic import BaseModel


class MediaUploadOut(BaseModel):
    url: str


__all__ = ["MediaUploadOut"]
