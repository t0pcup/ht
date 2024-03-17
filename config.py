import os

# import io
# from cryptography.fernet import Fernet
# import typing
from pydantic import AmqpDsn

# from functools import lru_cache

from pydantic_settings import BaseSettings
from starlette.config import Config

getenv = Config(".env")

CRYPT_KEY = None

# CRYPT_KEY=b'Bk89F_3rQedicU4wVqOzrRf_7C8kOf1n4MLTkTRVm-4='

# fernet = Fernet(CRYPT_KEY)

# class crypto_config(Config):

#     def _read_file(self, file_name: str) -> dict[str, str]:
#         file_values: typing.Dict[str, str] = {}
#         with open(file_name, 'rb') as f:
#             buffer = io.BytesIO(f.read())
#         buffer = io.BytesIO(fernet.decrypt(buffer.getvalue()))

#         for line in buffer.readlines():
#             line = line.decode('utf-8').strip()
#             if "=" in line and not line.startswith("#"):
#                 key, value = line.split("=", 1)
#                 key = key.strip()
#                 value = value.strip().strip("\"'")
#                 file_values[key] = value
#         return file_values

# getenv = crypto_config("/app/enc.env")


class GlobalConfig(BaseSettings):
    """
    Config from .env
    """

    # Global config
    LOGS_FOLDER: str = getenv(
        "LOGS_FOLDER", cast=str, default=os.environ.get("LOGS_FOLDER")
    )
    OUT_FOLDER: str = getenv(
        "OUT_FOLDER", cast=str, default=os.environ.get("OUT_FOLDER")
    )

    # Save to visual_results config
    WORK_LOCALLY: bool = getenv(
        "WORK_LOCALLY", cast=bool, default=os.environ.get("WORK_LOCALLY")
    )

    DROP_SCORE: float = getenv("DROP_SCORE", cast=float, default=0.5)

    # SUMMARIZE_PATH config
    SUMMARIZE_PATH: str = getenv(
        "SUMMARIZE_PATH",
        cast=str,
        default=os.environ.get("SUMMARIZE_PATH"),
    )

    # Triton url
    TRITON_URL: str = getenv(
        "TRITON_URL", cast=str, default=os.environ.get("TRITON_URL")
    )

    # MinIO config
    MINIO_HOST: str = getenv(
        "MINIO_HOST", cast=str, default=os.environ.get("MINIO_HOST")
    )
    MINIO_PORT: str = getenv(
        "MINIO_PORT", cast=str, default=os.environ.get("MINIO_PORT")
    )
    MINIO_USERNAME: str = getenv(
        "MINIO_USERNAME", cast=str, default=os.environ.get("MINIO_USERNAME")
    )
    MINIO_PASSWORD: str = getenv(
        "MINIO_PASSWORD", cast=str, default=os.environ.get("MINIO_PASSWORD")
    )
    MINIO_BUCKET: str = getenv(
        "MINIO_BUCKET", cast=str, default=os.environ.get("MINIO_BUCKET")
    )
    MINIO_MODELS_FOLDER: str = getenv(
        "MINIO_MODELS_FOLDER",
        cast=str,
        default=os.environ.get("MINIO_MODELS_FOLDER"),
    )
    MINIO_LOAD: bool = True
    MODEL_SIZE: str = getenv(
        "MODEL_SIZE", cast=str, default=os.environ.get("MODEL_SIZE")
    )  # "large-v2"
    HF_TOKEN: str = getenv(
        "HF_TOKEN", cast=str, default=os.environ.get("HF_TOKEN")
    )
    RU: str = getenv(
        "RU", cast=str, default=os.environ.get("RU")
    )
    DEVICE: str = getenv(
        "DEVICE", cast=str, default=os.environ.get("DEVICE")
    )
    BATCH_SIZE: int = getenv(
        "BATCH_SIZE", cast=int, default=os.environ.get("BATCH_SIZE")
    )
    COMPUTE_TYPE: str = getenv(
        "COMPUTE_TYPE", cast=str, default=os.environ.get("COMPUTE_TYPE")
    )


# @lru_cache()
def get_configuration():
    return GlobalConfig()


config = get_configuration()
