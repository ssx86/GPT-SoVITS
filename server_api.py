import gc
import os
import sys
import traceback
from typing import Generator

import torch.cuda

now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append("%s/GPT_SoVITS" % (now_dir))

import argparse
import subprocess
import wave
import signal
import numpy as np
import soundfile as sf
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import FastAPI, UploadFile, File
import uvicorn
from io import BytesIO
from tools.i18n.i18n import I18nAuto
from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
from GPT_SoVITS.TTS_infer_pack.text_segmentation_method import get_method_names as get_cut_method_names
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
i18n = I18nAuto()
cut_method_names = get_cut_method_names()

config_path = os.getenv("TTS_CONFIG")
port = os.getenv("PORT", 8008)
port = int(port)
host = os.getenv("BIND_HOST")

if config_path in [None, ""]:
    config_path = "./GPT_SoVITS/configs/tts_infer.yaml"

tts_config = TTS_Config(config_path)
if torch.cuda.is_available():
    tts_config.device = torch.device("cuda")
else:
    tts_config.device = torch.device('cpu')
print(tts_config)

app = FastAPI()


class TTSRequest(BaseModel):
    text: str = None
    text_lang: str = None
    ref_audio_path: str = None
    aux_ref_audio_paths: list = None
    prompt_lang: str = None
    prompt_text: str = ""
    top_k: int = 5
    top_p: float = 1
    temperature: float = 1
    text_split_method: str = "cut5"
    batch_size: int = 1
    batch_threshold: float = 0.75
    split_bucket: bool = True
    speed_factor: float = 1.0
    fragment_interval: float = 0.3
    seed: int = -1
    media_type: str = "wav"
    streaming_mode: bool = False
    parallel_infer: bool = True
    repetition_penalty: float = 1.35
    gpt_model_path: str = None
    vits_model_path: str = None


@app.post("/tts")
async def tts_post_endpoint(params: TTSRequest):
    data = params.dict()
    return await tts_handle(data)


async def tts_handle(req: dict):
    check_res = check_params(req)
    if check_res is not None:
        return check_res

    gpt_model = req.get("gpt_model_path")
    vits_model = req.get("vits_model_path")
    tts_config.t2s_weights_path = gpt_model
    tts_config.vits_weights_path = vits_model
    tts_pipeline = TTS(tts_config)

    media_type = req.get("media_type", "wav")
    try:
        tts_generator = tts_pipeline.run(req)
        sr, audio_data = next(tts_generator)
        audio_data = pack_audio(BytesIO(), audio_data, sr, media_type).getvalue()
        return Response(audio_data, media_type=f"audio/{media_type}")
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"tts failed", "Exception": str(e)})
    finally:
        del tts_pipeline
        gc.collect()


def check_params(req: dict):
    text: str = req.get("text", "")
    text_lang: str = req.get("text_lang", "")
    ref_audio_path: str = req.get("ref_audio_path", "")
    streaming_mode: bool = req.get("streaming_mode", False)
    media_type: str = req.get("media_type", "wav")
    prompt_lang: str = req.get("prompt_lang", "")
    text_split_method: str = req.get("text_split_method", "cut5")

    gpt_model = req.get("gpt_model_path")
    vits_model = req.get("vits_model_path")
    if (gpt_model is None) or (vits_model is None):
        return JSONResponse(status_code=400, content={"message": f"need file path"})
    if not os.path.exists(gpt_model):
        return JSONResponse(status_code=400, content={"message": f"gpt model not found"})
    if not os.path.exists(vits_model):
        return JSONResponse(status_code=400, content={"message": f"tts model not found"})

    if ref_audio_path in [None, ""]:
        return JSONResponse(status_code=400, content={"message": "ref_audio_path is required"})
    if text in [None, ""]:
        return JSONResponse(status_code=400, content={"message": "text is required"})
    if (text_lang in [None, ""]):
        return JSONResponse(status_code=400, content={"message": "text_lang is required"})
    elif text_lang.lower() not in tts_config.languages:
        return JSONResponse(status_code=400, content={
            "message": f"text_lang: {text_lang} is not supported in version {tts_config.version}"})
    if (prompt_lang in [None, ""]):
        return JSONResponse(status_code=400, content={"message": "prompt_lang is required"})
    elif prompt_lang.lower() not in tts_config.languages:
        return JSONResponse(status_code=400, content={
            "message": f"prompt_lang: {prompt_lang} is not supported in version {tts_config.version}"})
    if media_type not in ["wav", "raw", "ogg", "aac"]:
        return JSONResponse(status_code=400, content={"message": f"media_type: {media_type} is not supported"})
    elif media_type == "ogg" and not streaming_mode:
        return JSONResponse(status_code=400, content={"message": "ogg format is not supported in non-streaming mode"})

    if text_split_method not in cut_method_names:
        return JSONResponse(status_code=400,
                            content={"message": f"text_split_method:{text_split_method} is not supported"})

    return None


def pack_audio(io_buffer: BytesIO, data: np.ndarray, rate: int, media_type: str):
    if media_type == "ogg":
        io_buffer = pack_ogg(io_buffer, data, rate)
    elif media_type == "aac":
        io_buffer = pack_aac(io_buffer, data, rate)
    elif media_type == "wav":
        io_buffer = pack_wav(io_buffer, data, rate)
    else:
        io_buffer = pack_raw(io_buffer, data, rate)
    io_buffer.seek(0)
    return io_buffer


def pack_ogg(io_buffer:BytesIO, data:np.ndarray, rate:int):
    with sf.SoundFile(io_buffer, mode='w', samplerate=rate, channels=1, format='ogg') as audio_file:
        audio_file.write(data)
    return io_buffer


def pack_raw(io_buffer: BytesIO, data: np.ndarray, rate: int):
    io_buffer.write(data.tobytes())
    return io_buffer


def pack_wav(io_buffer: BytesIO, data: np.ndarray, rate: int):
    io_buffer = BytesIO()
    sf.write(io_buffer, data, rate, format='wav')
    return io_buffer


def pack_aac(io_buffer: BytesIO, data: np.ndarray, rate: int):
    process = subprocess.Popen([
        'ffmpeg',
        '-f', 's16le',  # 输入16位有符号小端整数PCM
        '-ar', str(rate),  # 设置采样率
        '-ac', '1',  # 单声道
        '-i', 'pipe:0',  # 从管道读取输入
        '-c:a', 'aac',  # 音频编码器为AAC
        '-b:a', '192k',  # 比特率
        '-vn',  # 不包含视频
        '-f', 'adts',  # 输出AAC数据流格式
        'pipe:1'  # 将输出写入管道
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = process.communicate(input=data.tobytes())
    io_buffer.write(out)
    return io_buffer


if __name__ == "__main__":
    try:
        uvicorn.run(app=app, host=host, port=port, workers=1)
    except Exception as e:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGTERM)
        exit(0)
