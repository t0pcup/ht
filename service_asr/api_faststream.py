from typing import List
from tqdm import tqdm
from loguru import logger
from config import config
from fastapi import FastAPI, HTTPException, status
from models.api_models import DiarizedSegment, InputData
from utils.whisper_utils import whisp
from miniopy_async import Minio

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
app = FastAPI()


async def get_obj(minio_path: str):
    # TODO: скачать файл в формате mp3 локально
    audio_path = "".join(minio_path.split("/")[:-1])
    await client.fget_object(config.MINIO_BUCKET, minio_path, audio_path)

    yield audio_path


@app.post("/transcribe_file/")
async def transcribe_file(data: InputData) -> List[DiarizedSegment]:
    try:
        audio_path = await get_obj(data.data_path)
    except Exception as e:
        # TODO: write status to DB "error"
        logger.error(f"Segmentation whisperx error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    try:
        audio = whisp.module.load_audio(audio_path)
        result = whisp.model.transcribe(
            audio, batch_size=config.BATCH_SIZE, language=config.RU
        )
        logger.info(f"Segmented to {len(result['segments'])} raw lines")
    except Exception as e:
        # TODO: write status to DB "error"
        logger.error(f"Segmentation whisperx error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    try:
        logger.info("Aligning...")
        result = whisp.module.align(
            result["segments"],
            whisp.align_model,
            whisp.metadata,
            audio,
            config.DEVICE,
            return_char_alignments=False,
        )
        logger.info("Aligned")
    except Exception as e:
        # TODO: write status to DB "error"
        logger.error(f"Alignment whisperx error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    try:
        logger.info("Diarizing...")
        diarize_segments = whisp.diarize_model(audio)
        result = whisp.module.assign_word_speakers(diarize_segments, result)[
            "segments"
        ]
        segments = []
        for line in tqdm(result, desc="Formatting"):
            if "words" in line:
                del line["words"]
            segments.append(DiarizedSegment(**line))

        logger.info(f"Speakers assigned for {len(segments)} segments")
        # TODO: write status to DB "ready"
        # TODO: segments should be written to DataBase
        return segments
    except Exception as e:
        # TODO: write status to DB "error"
        logger.error(f"Diarizing whisperx error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# @router.subscriber(rabbit_input_queue)
# async def queue(data: InputData):
#     data.data_path
#     raise HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail="Wrong service name",
#     )

# app.include_router(router)
