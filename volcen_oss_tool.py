import os
import json

import tos
from typing_extensions import Self
import functools


def volcen_oss_error_catch(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except tos.exceptions.TosClientError as e:
            # 操作失败，捕获客户端异常，一般情况为非法请求参数或网络异常
            print('volcen oss request fail with client error, message:{}, cause: {}'.format(e.message, e.cause))
        except tos.exceptions.TosServerError as e:
            # 操作失败，捕获服务端异常，可从返回信息中获取详细错误信息
            print('volcen oss request fail with server error, code: {}'.format(e.code))
            # request id 可定位具体问题，强烈建议日志中保存
            print('volcen oss request error with request id: {}'.format(e.request_id))
            print('volcen oss request error with message: {}'.format(e.message))
            print('volcen oss request error with http code: {}'.format(e.status_code))
            print('volcen oss request error with ec: {}'.format(e.ec))
            print('volcen oss request error with request url: {}'.format(e.request_url))
        except Exception as e:
            print('volcen oss request fail with unknown error: {}'.format(e))
            raise e
        return None
    return wrapper


class VolcenOssTool:
    def __init__(self):
        self.client = None
        self.bucket = os.getenv("VolcenOSSBucket")

    def connect(self):
        self.client = tos.TosClientV2(
            os.getenv("VolcenOSSAccessKey"),
            os.getenv("VolcenOSSSecretKey"),
            os.getenv("VolcenOSSEndpoint"),
            os.getenv("VolcenOSSRegion"),
        )

    def close(self):
        self.client.close()
        self.client = None

    @volcen_oss_error_catch
    def upload(self, key: str, file: bytes):
        response = self.client.put_object(self.bucket, key, content=file)
        print('success, request id {}'.format(response.request_id))
        return True

    @volcen_oss_error_catch
    def download(self, key: str):
        response_stream = self.client.get_object(self.bucket, key)
        return response_stream

    @volcen_oss_error_catch
    def download_large_file(self, key: str, path: str):
        rate_limiter = tos.RateLimiter(rate=5 * 1024 * 1024, capacity=10 * 1024 * 1024)
        self.client.download_file(
            self.bucket, key, path, part_size=1024 * 1024 * 20, task_num=4, rate_limiter=rate_limiter
        )
        return True

    @volcen_oss_error_catch
    def video_snapshot(self, key: str):
        image_name = self.get_video_snapshot_key(key)
        object_stream = self.client.get_object(
            bucket=self.bucket,
            key=key,
            process="video/snapshot,t_300",
            save_bucket=self.bucket,
            save_object=image_name
        )
        return image_name, object_stream.read()

    @volcen_oss_error_catch
    def get_video_info(self, key: str) -> dict:
        data = self.client.get_object(
            bucket=self.bucket,
            key=key,
            process="video/info",
        )
        return json.loads(data)

    @staticmethod
    def get_video_snapshot_key(key: str):
        return f"{(key.split('.')[0])}-snapshot.jpg"

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
