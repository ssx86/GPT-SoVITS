# Base CUDA image
# FROM cnstark/pytorch:2.0.1-py3.9.17-cuda11.8.0-ubuntu20.04
FROM cnstark/pytorch:2.0.1-py3.9.17-cuda11.8.0-ubuntu20.04


# Install 3rd party apps
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

WORKDIR /workspace
COPY sources.list .

RUN cat sources.list > temp.txt && \
    cat /etc/apt/sources.list >> temp.txt && \
    cat temp.txt > /etc/apt/sources.list && \
    rm temp.txt && \
    cat /etc/apt/sources.list



RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata ffmpeg libsox-dev parallel aria2 git git-lfs python3-numpy python3-scipy && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*


# Copy the rest of the application
COPY . /workspace

EXPOSE 8008

CMD ["sh", "-c", "./docker-start.sh"]
