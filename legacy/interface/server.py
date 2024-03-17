import asyncio
import base64
import csv
import json
import logging
import os
import sqlite3
import uuid
from sqlite3 import Error
from datetime import datetime
import dlib
import imutils
import numpy as np
import requests
from quart import Quart, request, stream_with_context, Response
from quart_cors import cors
from vowpalwabbit import pyvw
import itertools

from db import DatabaseManager
from ml import MLProcessor
from fil import FileProcessor
from ap import AdminProcessor


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)
app = cors(app, allow_origin="*")
app.sse_stream = asyncio.Queue()
app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000

admin_processor = AdminProcessor(app, 'client')
admin_processor.setup_routes()
db_manager = DatabaseManager()
db_manager.initialize_db()
ml_processor = MLProcessor(db_manager)
file_processor = FileProcessor(db_manager, app.sse_stream)

@app.route("/uploadImageOrVideo", methods=["POST"])
async def uploadImageOrVideo():
    return await file_processor.handle_upload_image_or_video_or_gif(request)

@app.route("/uploadSwappedImage", methods=["POST"])
async def uploadSwappedImage():
    return await file_processor.handle_upload_swapped_image(request)

@app.route('/mmr', methods=['GET'])
async def get_mmr():
    return await ml_processor.handle_mmr()

@app.route('/prediction', methods=['POST'])
async def prediction():
    return await ml_processor.handle_prediction(request)

@app.route('/feedback', methods=['POST'])
async def feedback():
    return await ml_processor.handle_feedback(request)

@app.route('/retrain', methods=['POST'])
async def retrain():
    return await ml_processor.handle_retrain()

@app.route('/model', methods=['GET'])
async def model():
    return await ml_processor.handle_model()

@app.route("/stream")
async def stream():
    async def event_stream():
        while True:
            data = await app.sse_stream.get()
            yield f"data: {data}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)