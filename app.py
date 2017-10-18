#!/usr/bin/env python
# @Author  : pengyun


from flask import Flask, request, jsonify, render_template
from sdk.client import CosClient
import time

# 腾讯云设置
appid = 'appid'
secret_id = 'secret_id'
secret_key = 'secret_key'
region = "region"
bucket = u'bucket'
cos_path = '/' # 要操作的子目录

client = CosClient(appid, secret_id, secret_key, region)

app = Flask(__name__)


def get_sign(filename):
    """ 使用 时间戳来当文件的名字"""
    end = '.' + filename.split('.')[-1]
    timestamp = str(int(time.time()))
    filename = timestamp + end
    path = cos_path + filename
    sign = client.get_sign(bucket, path)
    path = client.build(bucket, path)
    return sign, path


@app.route('/api/sign', methods=['GET', 'POST'])
def sign():
    """
    由于用户上传过来的文件的名字 和  真正保存的名字不同，应该保存在数据库中。
    当用户
    :return:
    """
    filename = request.json['filename']
    sign, url = get_sign(filename)
    return jsonify({'sign': sign, 'url': url})


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
