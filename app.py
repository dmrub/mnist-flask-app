#!/usr/bin/env python3
import base64
import io
import os
import re
import sys

import PIL.Image
import PIL.ImageOps
import numpy as np
from flask import Flask, render_template, request

sys.path.append(os.path.abspath("./model"))
from load import *

app = Flask(__name__)
global model, graph
model = init()


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/predict/', methods=['GET', 'POST'])
def predict():
    # get data from drawing canvas and save as image
    x = convert_base64_image_to_nparray(request.get_data())

    # reshape image data for use in neural network
    x = x.reshape(1, 28, 28, 1)
    out = model.predict(x)
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
    #image.show()
    array = np.asarray(image, dtype='float32')
    #print(array.tolist())
    #with open('output.png', 'wb') as output:
    #    output.write(image_data)
    return array


if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
