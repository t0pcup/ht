FROM python:3.9.16-slim-bullseye

ARG APP_FOLDER=/app

WORKDIR /app

RUN /usr/local/bin/python -m pip install --upgrade pip

RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

RUN apt-get update && apt update && apt install git -y

RUN pip install git+https://github.com/m-bain/whisperx.git

RUN git clone https://github.com/m-bain/whisperX.git && cd whisperX && pip install -e .

COPY requirements.txt requirements.txt

ARG APP_USER=otp_user
ARG APP_GROUP=otp_group
ARG APP_USER_UID=999

RUN groupadd --gid ${APP_USER_UID} --system ${APP_GROUP} && \
    useradd --uid ${APP_USER_UID} \
            --gid ${APP_GROUP} \
            --no-create-home \
            --system \
            --shell /bin/false \
            ${APP_USER}

RUN apt install ffmpeg -y && apt install --no-install-recommends -y \
        libgl1 \
        gcc \
        libglib2.0-0 \
    && apt clean && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade -r requirements.txt

# RUN python -m pytorch_lightning.utilities.upgrade_checkpoint ../root/.cache/torch/whisperx-vad-segmentation.bin

# COPY src/ src/

# COPY . .

COPY service_asr/. .
COPY service_convert/. .
