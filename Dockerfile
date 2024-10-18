# Base CUDA image
# FROM cnstark/pytorch:2.0.1-py3.9.17-cuda11.8.0-ubuntu20.04
FROM python:3.9.6-slim-buster

LABEL maintainer="breakstring@hotmail.com"
LABEL version="dev-20240209"
LABEL description="Docker image for GPT-SoVITS"


# Install 3rd party apps
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata ffmpeg libsox-dev parallel aria2 git git-lfs && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy the rest of the application
COPY . /workspace

EXPOSE 8008

CMD ["sh", "-c", "./docker-installer.sh"]
