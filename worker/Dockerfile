FROM python:3.8-slim

# System dependencies for audio/MIDI processing
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        fluidsynth \
        fluid-soundfont-gm \
        build-essential \
        libasound2-dev \
        portaudio19-dev \
        libjack-dev \
        llvm-dev \
        && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY worker/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY worker /app/worker
COPY audio.mp3 /app/audio.mp3
COPY sample.mp3 /app/sample.mp3

CMD ["python", "worker/transcribe.py"]