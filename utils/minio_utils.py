import io
import json
import os
from contextlib import asynccontextmanager

# import cv2 as cv
import pandas as pd
import urllib3
from urllib3.util.retry import Retry
from miniopy_async import Minio
from PIL import Image


client = Minio(
    "host.docker.internal:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)


@asynccontextmanager
async def tmp_image_file():
    """Генерирует уникальный путь до временного файла, при выходе удаляет файл."""
    os.makedirs("tmp", exist_ok=True)
    fp = f"tmp/{1}.mp3"  # TODO: generate name
    try:
        yield fp
    finally:
        if os.path.exists(fp):
            os.remove(fp)
