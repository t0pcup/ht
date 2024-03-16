import os
import uuid
from typing import List
from tqdm import tqdm
from loguru import logger
from moviepy.editor import VideoFileClip, AudioFileClip
from faststream.rabbit import RabbitQueue
from faststream.rabbit.fastapi import RabbitRouter
from fastapi import FastAPI, HTTPException, UploadFile, status, Depends, File
from models.api_models import Word, DiarizedSegment, InputData
from utils.minio_utils import MinioLoader, save_upload_file_to_minio
from miniopy_async import Minio
import asyncio
from contextlib import asynccontextmanager, contextmanager
from uuid import uuid4
import json
from datetime import time
from config import config
import aiohttp
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io
import msgpack
from service_asr import whisperx

client = Minio(
    "host.docker.internal:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)


logger.add(
    "logs/service_convert_logs.log",
    level="INFO",
    format="{time} - {name} - {level} - {message} - {module}",
    rotation="50 MB",
    retention=10,
)

app = FastAPI()

model = whisperx.load_model(config.MODEL_SIZE, config.DEVICE, compute_type=config.COMPUTE_TYPE, language=config.RU)
model_a, metadata = whisperx.load_align_model(language_code=config.RU, device=config.DEVICE)
diarize_model = whisperx.DiarizationPipeline(use_auth_token=config.HF_TOKEN, device=config.DEVICE)
# router = RabbitRouter(config.rabbitmq_url)
# app = FastAPI(lifespan=router.lifespan_context)
# rabbit_input_queue = RabbitQueue(
#     name=config.RABBITMQ_ASR_INPUT_QUEUE, durable=True
# )


async def get_obj(minio_path: str):
    # скачать файл в формате mp3
    audio_path = "".join(minio_path.split("/")[:-1])
    await client.fget_object(config.MINIO_BUCKET, minio_path, audio_path)

    yield audio_path


# @router.subscriber(rabbit_input_queue)
# async def queue(data: InputData):
#     data.data_path
#     raise HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail="Wrong service name",
#     )

# app.include_router(router)


@asynccontextmanager
async def tmp_image_file():
    """Генерирует уникальный путь до временного файла, при выходе удаляет файл."""
    os.makedirs("tmp", exist_ok=True)
    fp = f"tmp/{uuid4()}.mp3"
    try:
        yield fp
    finally:
        if os.path.exists(fp):
            os.remove(fp)


@app.post("/check_convert/", status_code=status.HTTP_200_OK)
async def check_convert(file: UploadFile = File(...)):
    # audio = whisperx.load_audio(file.filename)

    # result = model.transcribe(audio, batch_size=config.BATCH_SIZE, language=config.RU)
    # logger.info(f"Segmented to {len(result['segments'])} raw lines")

    filename = file.filename
    if filename.endswith(".mp4"):
        new_name = filename.split(".") + ".mp3"
        video = VideoFileClip(filename)
        video.audio.write_audiofile(new_name)
        filename = new_name
    elif filename.endswith(".mp3") or filename.endswith(".wav"):
        AudioFileClip(filename).write_audiofile(filename)
    else:
        return status.HTTP_400_BAD_REQUEST

    async with tmp_image_file() as f:
        # logger.info(f)
        # f.write(file.read())
        # logger.info(f.filepath)
        await client.put_object(
            bucket_name=config.MINIO_BUCKET,
            object_name=f"files/{filename}",
            file_path=f,
        )
