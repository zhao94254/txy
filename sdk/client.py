#!/usr/bin/env python
# @Author  : pengyun

import time
from urllib import parse

import requests

from sdk.auth import Auth

try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass


class CredInfo:
    """用户身份信息"""

    def __init__(self, appid, secret_id, secret_key):
        self.appid = appid
        self.secret_id = secret_id
        self.secret_key = secret_key


class CosInfo:
    def __init__(self, region=None, hostname=None, download_hostname=None, *args, **kwargs):
        self._hostname = None
        self._download_hostname = None

        region_dict = {
            'shanghai': 'sh',
            'guangzhou': 'gz',
            'tianjing': 'tj',
            'singapore': 'sgp',
        }
        if region in region_dict:
            self._hostname = region_dict[region] + '.file.myqcloud.com'
            self._download_hostname = 'cos' + region_dict[region] + '.myqcloud.com'
        elif region in region_dict.values():
            self._hostname = region + '.file.myqcloud.com'
            self._download_hostname = 'cos' + region + '.myqcloud.com'
        else:
            if hostname and download_hostname:
                self._hostname = hostname
                self._download_hostname = download_hostname
            else:
                raise ValueError(
                    "region or [hostname, download_hostname] must be set, and region should be sh/gz/tj/sgp")

    @property
    def hostname(self):
        return self._hostname

    @property
    def download_hostname(self):
        return self._download_hostname


class UploadFileRequest:
    """
    :param bucket_name:  bucket的名称
    :param cos_path: cos的绝对路径(目的路径), 从bucket根/开始
    :param local_path: 上传的本地文件路径(源路径)
    :param biz_attr: 文件的属性
    :param insert_only: 是否覆盖写, 0覆盖, 1不覆盖,返回错误
    """

    def __init__(self, bucket_name, cos_path, local_path='', biz_attr='', insert_only=1):
        self.bucket_name = bucket_name
        self.cos_path = cos_path
        self.local_path = local_path
        self.biz_attr = biz_attr
        self.insert_attr = insert_only
        self.expired = 180


def build_url(hostname, appid, bucket, cospath):
    endpoint = 'http://' + hostname + '/files/v2'
    cospath = parse.quote(cospath.encode('utf8'), '~/')
    url = '{}/{}/{}{}'.format(endpoint, appid, bucket, cospath)
    return url


class FileOp:
    def __init__(self, cred):
        self.cred = cred

    def upload_file(self, request):
        """ 直接传输的时二进制文件 """
        assert isinstance(request, UploadFileRequest)
        bucket = request.bucket_name
        cos_path = request.cos_path
        # Todo add to config
        expired = int(time.time())
        auth = Auth(self.cred)

        sign = auth.sign_more(bucket, cos_path, expired)

        http_header = dict()
        http_header['Authorization'] = sign
        # Todo

    def sign_auth(self, request):
        assert isinstance(request, UploadFileRequest)
        bucket = request.bucket_name
        cos_path = request.cos_path
        # Todo add to config
        expired = int(time.time()) + request.expired
        auth = Auth(self.cred)
        return auth.sign_more(bucket, cos_path, expired)

    def get_folder(self, request, url):
        auth = Auth(self.cred)
        bucket = request.bucket_name
        cos_path = request.cos_path
        expired = int(time.time()) + request.expired
        sign = auth.sign_more(bucket, cos_path, expired)

        http_header = dict()
        http_header['Authorization'] = sign
        http_header['User-Agent'] = 'cos-python-sdk-v4'

        http_body = dict()
        http_body['op'] = 'stat'
        timeout = 30
        session = requests.session()
        return session.get(url, verify=False, headers=http_header, params=http_body, timeout=timeout)


class CosClient:
    def __init__(self, appid, secret_id, secret_key, region='shanghai'):
        self._cred = CredInfo(appid, secret_id, secret_key)
        self.hostname = CosInfo(region).hostname
        self.file = FileOp(self._cred)

    def get_sign(self, bucket, cos_path):
        request = UploadFileRequest(bucket, cos_path)
        sign = self.file.sign_auth(request)
        return sign

    def build(self, bucket, cos_path):
        return build_url(self.hostname, self._cred.appid, bucket, cos_path)

    def get_folder(self, bucket, cos_path):
        cos_path = '/{}/'.format(cos_path)
        url = self.build(bucket, cos_path)
        request = UploadFileRequest(bucket, cos_path)
        response = self.file.get_folder(request, url)
        return response.json(), response.status_code
