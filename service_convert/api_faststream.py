from loguru import logger
from moviepy.editor import VideoFileClip, AudioFileClip
from fastapi import FastAPI, HTTPException, UploadFile, status, Depends, File
from models.api_models import Word, DiarizedSegment, InputData, ConvertData
import asyncio
from utils.minio_utils import client, tmp_image_file
from config import config
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession


logger.add(
    "logs/service_convert_logs.log",
    level="INFO",
    format="{time} - {name} - {level} - {message} - {module}",
    rotation="50 MB",
    retention=10,
)
app = FastAPI()


@app.post("/check_convert/", status_code=status.HTTP_200_OK)
async def check_convert(data: ConvertData):
    order = data.value

    # TODO: order.file_path -- minio path, нужно сконвертить и положить в minio mp3
    filename = order.file_path
    if filename.endswith(".mp4"):
        new_name = filename.split(".") + ".mp3"
        video = VideoFileClip(filename)
        video.audio.write_audiofile(new_name)
        filename = new_name
    elif filename.endswith(".mp3") or filename.endswith(".wav"):
        AudioFileClip(filename).write_audiofile(filename)
    else:
        logger.error("Bad file format")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad file format"
        )

    async with tmp_image_file() as f:
        await client.put_object(
            bucket_name=config.MINIO_BUCKET,
            object_name=f"files/{filename}",
            file_path=f,
        )
    # TODO: write status to DB "converted"
    # TODO: call next service
