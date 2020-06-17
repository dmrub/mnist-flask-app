#!/usr/bin/env python3
import base64
import io
import os
import re
import sys
import json
import requests
import pprint

import PIL.Image
import PIL.ImageOps
import numpy as np
from flask import Flask, Response, render_template, request, url_for, jsonify, current_app, g
from flask_reverse_proxy import ReverseProxied

sys.path.append(os.path.abspath("./model"))
from load import *

app = Flask(__name__, instance_relative_config=True)
app.wsgi_app = ReverseProxied(app.wsgi_app)
logger = app.logger

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY=os.urandom(24),
    LOG_FILE=os.path.join(app.instance_path, 'mnist-app.log'),
    FILE_FOLDER=os.path.join(app.instance_path, 'files'),
    TF_SERVING_URI=os.environ.get('TF_SERVING_URI', None),
    PORT=os.environ.get('PORT', 5000),
    MAX_CONTENT_LENGTH=100 * 1024 * 1024  # Maximal 100 Mb for files
))
app.config.from_envvar('MNIST_APP_SETTINGS', silent=True)

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_NOT_IMPLEMENTED = 501


def error_response(message, status_code=HTTP_INTERNAL_SERVER_ERROR):
    response = jsonify({'message': message})
    response.status_code = status_code
    return response


def bad_request(message):
    return error_response(message=message, status_code=HTTP_BAD_REQUEST)


def not_found(message):
    return error_response(message=message, status_code=HTTP_NOT_FOUND)


def not_implemented(message):
    return error_response(message=message, status_code=HTTP_NOT_IMPLEMENTED)

@app.errorhandler(requests.exceptions.ConnectionError)
def on_request_exception(error):
    return error_response(message=str(error), status_code=HTTP_INTERNAL_SERVER_ERROR)


global MODEL
if app.config['TF_SERVING_URI']:
    print('Use TF Serving URI: {}'.format(app.config['TF_SERVING_URI']))
else:
    MODEL = init()


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/predict/', methods=['GET', 'POST'])
def predict():
    # get data from drawing canvas and save as image
    x = convert_base64_image_to_nparray(request.get_data())

    if app.config['TF_SERVING_URI']:
        print('Use TF serving: {}'.format(app.config['TF_SERVING_URI']))
        x = x.reshape(28, 28, 1) / 255.0
        instances = [x.tolist()]
        data = json.dumps({"signature_name": "serving_default", "instances": instances})
        print('Data: {} ... {}'.format(data[:50], data[len(data) - 52:]))

        headers = {"content-type": "application/json"}
        json_response = requests.post(app.config['TF_SERVING_URI'],
                                      data=data,
                                      headers=headers)
        json_response.raise_for_status()
        predictions = [np.argmax(p) for p in json.loads(json_response.text)['predictions']]
        response = repr(predictions)
        print(response)
    else:
        # reshape image data for use in neural network
        print('Use local model')
        x = x.reshape(1, 28, 28, 1)
        out = MODEL.predict(x)
        print(out)
        print(np.argmax(out, axis=1))
        response = np.array_str(np.argmax(out, axis=1))

    return response


def convert_base64_image_to_nparray(request_data):
    # parse canvas bytes and save as output.png
    imgstr = re.search(b'base64,(.*)', request_data).group(1)
    image_data = base64.decodebytes(imgstr)
    image = PIL.Image.open(io.BytesIO(image_data))
    image = PIL.ImageOps.invert(image.convert('L').resize((28, 28), resample=PIL.Image.BICUBIC))
    # image.show()
    array = np.asarray(image, dtype='float32')
    # print(array.tolist())
    # with open('output.png', 'wb') as output:
    #    output.write(image_data)
    return array


@app.route("/api/debug/flask/", methods=["GET"])
def debug_flask():
    import urllib

    output = ['Rules:']
    for rule in current_app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        if rule.methods:
            methods = ','.join(rule.methods)
        else:
            methods = 'GET'
        url = url_for(rule.endpoint, **options)
        line = urllib.parse.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    output.append('')
    output.append('Request environment:')
    for k, v in request.environ.items():
        output.append("{0}: {1}".format(k, pprint.pformat(v, depth=5)))

    output.append('')
    output.append('Request vars:')
    output.append("request.path: {}".format(request.path))
    output.append("request.full_path: {}".format(request.full_path))
    output.append("request.script_root: {}".format(request.script_root))
    output.append("request.url: {}".format(request.url))
    output.append("request.base_url: {}".format(request.base_url))
    output.append("request.host_url: {}".format(request.host_url))
    output.append("request.url_root: {}".format(request.url_root))
    output.append('')

    return Response('\n'.join(output), mimetype='text/plain')


if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    print('Running on port {}'.format(port))
    app.run(host='0.0.0.0', port=port)
