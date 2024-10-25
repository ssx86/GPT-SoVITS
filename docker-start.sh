#!/bin/bash -l

python -m venv /venv
. /venv/bin/activate
#

python -m pip install --upgrade pip -i https://mirrors.volces.com/pypi/simple/
pip install -r requirements.txt -v -i https://mirrors.volces.com/pypi/simple/

chmod +x /workspace/Docker/download.sh
/workspace/Docker/download.sh
python /workspace/GPT_SoVITS/download.py

# Set up environment variables
ENV=${ENV:-"dev"}
workers=${workers:-"2"}
port=8008

echo "Application instance launch on port $port."
ENV=${ENV} uvicorn server_api:app --host=0.0.0.0 --port=$port --workers=$workers
