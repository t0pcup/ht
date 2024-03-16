import os
import uuid
from typing import List
from tqdm import tqdm
from loguru import logger
from service_asr import whisperx
from config import config
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
import aiohttp
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io
import msgpack

client = Minio(
    "host.docker.internal:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

logger.add(
    "logs/service_asr_logs.log",
    level="INFO",
    format="{time} - {name} - {level} - {message} - {module}",
    rotation="50 MB",
    retention=10,
)

model = whisperx.load_model(config.MODEL_SIZE, config.DEVICE, compute_type=config.COMPUTE_TYPE, language=config.RU)
model_a, metadata = whisperx.load_align_model(language_code=config.RU, device=config.DEVICE)
diarize_model = whisperx.DiarizationPipeline(use_auth_token=config.HF_TOKEN, device=config.DEVICE)
# minio_loader = MinioLoader()

app = FastAPI()
# router = RabbitRouter(config.rabbitmq_url)
# app = FastAPI(lifespan=router.lifespan_context)
# rabbit_input_queue = RabbitQueue(
#     name=config.RABBITMQ_ASR_INPUT_QUEUE, durable=True
# )


async def get_obj(minio_path: str):
    # скачать файл в формате mp3 локально
    audio_path = "".join(minio_path.split("/")[:-1])
    await client.fget_object(config.MINIO_BUCKET, minio_path, audio_path)

    yield audio_path


@app.post("/transcribe_file/")
async def transcribe_file(data: InputData) -> List[DiarizedSegment]:
    # filename = file.filename
    # logger.info(f"Received file {filename}")

    # if filename.endswith(".mp4"):
    #     new_name = filename.replace(".mp4", ".mp3")
    #     video = VideoFileClip(filename)
    #     video.audio.write_audiofile(new_name)
    #     filename = new_name
    # elif filename.endswith(".mp3") or filename.endswith(".wav"):
    #     AudioFileClip(filename).write_audiofile(filename)
    # else:
    #     return status.HTTP_400_BAD_REQUEST

    try:
        audio_path = await get_obj(data.data_path)
    except Exception as e:
        logger.error(f"Segmentation whisperx error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    # # logger.info(os.path.isfile(filename))
    # file_tmp_path = ""
    # with open(filename, mode="rb") as f:
    #     logger.info(f)
    #     logger.info(type(f))
    #     fb = f.read()
    #     minio_loader = MinioLoader()
    #     minio_loader.upload_bytes_file(
    #         "audio/" + filename, fb, len(fb), minio_loader.minio_bucket
    #     )

    try:
        audio = whisperx.load_audio(audio_path)
        result = model.transcribe(audio, batch_size=config.BATCH_SIZE, language=config.RU)
        logger.info(f"Segmented to {len(result['segments'])} raw lines")
    except Exception as e:
        logger.error(f"Segmentation whisperx error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    try:
        logger.info("Aligning...")
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            config.DEVICE,
            return_char_alignments=False,
        )
        logger.info("Aligned")
    except Exception as e:
        logger.error(f"Alignment whisperx error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    try:
        logger.info("Diarizing...")
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)["segments"]
        segments = []
        for line in tqdm(result, desc="Formatting"):
            if "words" in line:
                del line["words"]
            segments.append(DiarizedSegment(**line))

        logger.info(f"Speakers assigned for {len(segments)} segments")
        return segments
    except Exception as e:
        logger.error(f"Diarizing whisperx error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# @router.subscriber(rabbit_input_queue)
# async def queue(data: InputData):
#     data.data_path
#     raise HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail="Wrong service name",
#     )

# app.include_router(router)
