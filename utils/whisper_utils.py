from loguru import logger
from config import config
import whisperx


class Whisp:
    module = whisperx
    model = whisperx.load_model(
        config.MODEL_SIZE,
        config.DEVICE,
        compute_type=config.COMPUTE_TYPE,
        language=config.RU,
    )
    align_model, metadata = whisperx.load_align_model(
        language_code=config.RU, device=config.DEVICE
    )
    diarize_model = whisperx.DiarizationPipeline(
        use_auth_token=config.HF_TOKEN, device=config.DEVICE
    )


whisp = Whisp()
logger.info("Models initiated")
