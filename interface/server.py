# import requests
# from quart import Quart, request, send_file, Response
# import json
# import copy
# from datetime import datetime
# import moment
# import asyncio
# import os
# from time import sleep
# import uuid
# from quart_cors import cors
# import python_pachyderm
# import google.auth
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# import json
# import mimetypes
# import threading
# import base64
# import csv
# import sqlite3
# from sqlite3 import Error
# from vowpalwabbit import pyvw


# app = Quart(__name__)
# app = cors(app, allow_origin="*")
# app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000

# # Add this line to create a dictionary to store events for each job
# job_events = {}
# job_files = {}

# def format_vw_example(row):
#     image_id, prediction, feedback, _ = row
#     return f"{feedback} {image_id}| {prediction}"

# # Database setup
# def create_connection():
#     conn = None
#     db_file = 'mmr.db' # Modify this path to your database file

#     try:
#         conn = sqlite3.connect(db_file)
#         if conn:
#             print(sqlite3.version)
#     except Error as e:
#         print(e)
#     return conn

# def create_table(conn):
#     try:
#         sql_create_table = """ CREATE TABLE IF NOT EXISTS predictions (
#                                             id integer PRIMARY KEY,
#                                             image_id text NOT NULL,
#                                             prediction text NOT NULL,
#                                             feedback text
#                                         ); """
#         if conn is not None:
#             c = conn.cursor()
#             c.execute(sql_create_table)
#     except Error as e:
#         print(e)

# def insert_prediction(conn, prediction):
#     sql = ''' INSERT INTO predictions(image_id,prediction)
#               VALUES(?,?) '''
#     cur = conn.cursor()
#     cur.execute(sql, prediction)
#     return cur.lastrowid

# def insert_feedback(conn, feedback):
#     sql = ''' UPDATE predictions
#               SET feedback = ?
#               WHERE image_id = ? '''
#     cur = conn.cursor()
#     cur.execute(sql, feedback)
#     conn.commit()

# # When you make a prediction
# def save_prediction(image_id, prediction):
#     database = create_connection()
#     create_table(database)
    
#     prediction_tuple = (image_id, json.dumps(prediction))
#     insert_prediction(database, prediction_tuple)

# # When you receive feedback
# def save_feedback(image_id, feedback):
#     database = create_connection()

#     feedback_tuple = (feedback, image_id)
#     insert_feedback(database, feedback_tuple)

# def fetch_feedback(conn):
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM predictions WHERE feedback IS NOT NULL")

#     rows = cur.fetchall()

#     return rows

# def retrain_model():
#     database = create_connection()
#     feedback_rows = fetch_feedback(database)
    
#     # Format the feedback and existing data in a way that VW can understand
#     # You need to convert feedback, action (prediction), and context (features) into VW format
#     formatted_data = [format_vw_example(row) for row in feedback_rows]
    
#     # Add the new data to your existing data and retrain the model
#     vw = pyvw.vw("--cb 4")
#     for example in formatted_data:
#         vw.learn(example)
    
#     # Save the new model
#     vw.save_model('new_model.vw')

# def load_model():
#     vw = pyvw.vw("--cb 4 -i new_model.vw")
#     return vw

# def get_sheet_data():
#     try:
#         rows = []
#         # read from mmr.csv locally, along with headers
#         with open('mmr.csv', newline='') as csvfile:
#             reader = csv.reader(csvfile, delimiter=',')
#             for row in reader:
#                 oneRow = {}
#                 oneRow["url"] = row[0]
#                 oneRow["x_scale"] = row[1]
#                 oneRow["y_scale"] = row[2]
#                 oneRow["x_location"] = row[3]
#                 oneRow["y_location"] = row[4]
#                 oneRow["rotation"] = row[5]
#                 rows.append(oneRow)

#         return rows
#     except HttpError as error:
#         print(f"An error occurred: {error}")
#         return None

# def sheet_data_to_json(sheet_data):
#     if not sheet_data:
#         return []

#     headers = [header.lower() for header in sheet_data[0]]
#     json_data = [dict(zip(headers, row)) for row in sheet_data[1:]]

#     return json_data


# @app.route('/sheet-data', methods=['GET'])
# async def get_sheet_data_json():
#     sheet_data = get_sheet_data()
#     return json.dumps(sheet_data)

# @app.route("/uploadImageOrVideo", methods=["POST"])
# async def uploadImageOrVideo():
#     jobs = []
#     print("Number of files:", len(await request.files))
#     for field_name, file_storage in (await request.files).items():
#         selectedMilady = (await request.form)["selectedMilady"]
#         xScale = (await request.form)["xScale"]
#         yScale = (await request.form)["yScale"]
#         xLocation = (await request.form)["xLocation"]
#         yLocation = (await request.form)["yLocation"]
#         print("Selected Milady:", selectedMilady)
#         print("Field name: " + field_name)
#         print("File name: " + file_storage.filename)
#         print("X-Scale: " + xScale)
#         print("Y-Scale: " + yScale)
#         print("xLocation: " + xLocation)
#         print("yLocation: " + yLocation)
#         content_type = file_storage.content_type

#         if content_type is None:
#             return json.dumps({"error": "Invalid file type"})

#         is_image = content_type.startswith("image")
#         is_video = content_type.startswith("video")

#         print("Is image:", is_image)
#         print("Is video:", is_video)

#         if not (is_image or is_video):
#             return json.dumps({"error": "File is neither image nor video"})
        
#         if(is_image):
#             print("Image")
#             # Your image processing logic here

#             t = file_storage.filename.split(".")
#             ext = t.pop()
#             print("Extension: " + ext)
#             new_job_id = str(uuid.uuid4())
#             jobs.append(new_job_id)
#             print(new_job_id)
#             actual_file = file_storage.read()
#             # create a directory to store the blend files
#             if not os.path.exists("/tmp/blends"):
#                 os.makedirs("/tmp/blends")
#             with open("/tmp/blends/" + new_job_id + '.' + ext, "wb") as reader:
#                 reader.write(actual_file)
#             print("Size: " + str(len(actual_file)))

#             imgswap = new_job_id + "-imgswap"

#             clientCreateRepo = f"pachctl create repo {imgswap}"
#             print("running: " + clientCreateRepo)
#             os.system(clientCreateRepo)
            

#             putFileRepo = f"pachctl put file {imgswap}@master:/{new_job_id}.{ext} -f /tmp/blends/{new_job_id}.{ext}"
#             print("running: " + putFileRepo)
#             os.system(putFileRepo)
#             os.remove("/tmp/blends/" + new_job_id + '.' + ext)

#             processed = new_job_id + "-img-prcsd"
#             clientCreateRepo = f"pachctl create repo {processed}"
#             print("running: " + clientCreateRepo)
#             os.system(clientCreateRepo)

#             print("xScale: " + xScale)
#             print("yScale: " + yScale)
#             print("xLocation: " + xLocation)
#             print("yLocation: " + yLocation)

#             jsonPipeline = {}
#             jsonPipeline["pipeline"] = {}
#             jsonPipeline["pipeline"]["name"] = processed
#             jsonPipeline["input"] = {}
#             jsonPipeline["input"]["pfs"] = {}
#             jsonPipeline["input"]["pfs"]["glob"] = "/*"
#             jsonPipeline["input"]["pfs"]["repo"] = imgswap
#             jsonPipeline["transform"] = {}
#             jsonPipeline["transform"]["cmd"] = ["python3", "/face_swapper.py", f"{imgswap}", f"{selectedMilady}", "https://api.matrixmilady.com/uploadSwappedImage", f"{xScale}", f"{yScale}", f"{xLocation}", f"{yLocation}", f"{rotation}"]
#             jsonPipeline["transform"]["image"] = "laneone/edith-images:221df1ab01c548a29be649f0e92ea06c"
#             jsonPipeline["transform"]["image_pull_secrets"] = ["laneonekey"]

#             createPipeline = f"pachctl create pipeline -f - <<EOF\n{json.dumps(jsonPipeline)}\nEOF"
#             print("running: " + createPipeline)
#             os.system(createPipeline)

#             job_events[new_job_id] = asyncio.Event()

#             job_files[new_job_id] = f"/tmp/swappedimage/{new_job_id}.jpg"

#     # Wait for all events to be set
#     await asyncio.gather(*(job_events[job].wait() for job in jobs))
#     # Clear events from the dictionary
#     for job in jobs:
#         del job_events[job]


#     # Check for the processed image file and return the base64 encoded content
#     base64_encoded_images = {}
#     for job_id in jobs:
#         file_path = job_files[job_id]
#         while not os.path.exists(file_path):
#             await asyncio.sleep(1)  # Check every 1 second

#         with open(file_path, "rb") as image_file:
#             encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
#             base64_encoded_images[job_id] = encoded_string

#     # Save the prediction when a prediction is made
#     save_prediction(new_job_id, prediction)

#     return json.dumps(base64_encoded_images)

# @app.route("/uploadSwappedImage", methods=["POST"])
# async def uploadSwappedImage():
#     jobs = []
#     print("Number of files:", len(await request.files))
#     for field_name, file_storage in (await request.files).items():
#         print("Field name: " + field_name)
#         print("File name: " + file_storage.filename)
#         prejobid = file_storage.filename.split(".")[0]
#         actual_file = file_storage.read()
#         print("Size: " + str(len(actual_file)))
#         # create a directory to store the blend files
#         if not os.path.exists("/tmp/swappedimage"):
#             os.makedirs("/tmp/swappedimage")
        
#         with open("/tmp/swappedimage/" + prejobid + ".jpg", "wb") as reader:
#             reader.write(actual_file)
        
#         imgswap = prejobid + "-imgswap"
#         processed = prejobid + "-img-prcsd"
#         # client.delete_repo(processed)
#         clientDeleteProcessed = f"pachctl delete repo {processed}"
#         print("running: " + clientDeleteProcessed)
#         os.system(clientDeleteProcessed)
#         # client.delete_pipeline(processed)
#         clientDeletePipeline = f"pachctl delete pipeline {processed}"
#         print("running: " + clientDeletePipeline)
#         os.system(clientDeletePipeline)

#         # client.delete_repo(imgswap)
#         clientDeleteImgswap = f"pachctl delete repo {imgswap}"
#         print("running: " + clientDeleteImgswap)
#         os.system(clientDeleteImgswap)
#         print("Cleaned up job " + prejobid)

#     # Set the event for this job, signaling that it's complete
#     job_events[prejobid].set()

#     return "Ack! milady 🫡"
        
# app.run(host="0.0.0.0", ssl_context=("adhoc"))

# import asyncio
# import base64
# import csv
# import json
# import logging
# import os
# import sqlite3
# import uuid
# from sqlite3 import Error
# from datetime import datetime
# import dlib
# import imutils
# import numpy as np

# import requests
# from quart import Quart, request
# from quart_cors import cors
# from vowpalwabbit import pyvw

# logging.basicConfig(level=logging.INFO)

# app = Quart(__name__)
# app = cors(app, allow_origin="*")
# app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000

# job_events = {}
# job_files = {}


# class DatabaseManager:
#     def __init__(self, db_file='mmr.db'):
#         self.db_file = db_file
#         self.conn = self.create_connection()
#         self.create_table()

#     def create_connection(self):
#         conn = None
#         try:
#             conn = sqlite3.connect(self.db_file)
#             if conn:
#                 logging.info(sqlite3.version)
#         except Error as e:
#             logging.error(e)
#         return conn

#     def create_table(self):
#         sql_create_table = """ CREATE TABLE IF NOT EXISTS predictions (
#                                     id integer PRIMARY KEY,
#                                     image_id text NOT NULL,
#                                     prediction text NOT NULL,
#                                     face_landmarks text NOT NULL,
#                                     feedback text
#                                 ); """
#         if self.conn is not None:
#             c = self.conn.cursor()
#             c.execute(sql_create_table)

#     def insert_prediction(self, prediction):
#         sql = ''' INSERT INTO predictions(image_id,prediction)
#                   VALUES(?,?) '''
#         cur = self.conn.cursor()
#         cur.execute(sql, prediction)
#         return cur.lastrowid

#     def insert_feedback(self, feedback):
#         sql = ''' UPDATE predictions
#                   SET feedback = ?
#                   WHERE image_id = ? '''
#         cur = self.conn.cursor()
#         cur.execute(sql, feedback)
#         self.conn.commit()

#     def fetch_feedback(self):
#         cur = self.conn.cursor()
#         cur.execute("SELECT * FROM predictions WHERE feedback IS NOT NULL")
#         rows = cur.fetchall()
#         return rows


# class ImageProcessor:
#     def __init__(self, database_manager: DatabaseManager):
#         self.db_manager = database_manager

#     def save_prediction(self, image_id, prediction, face_landmarks):
#         prediction_tuple = (image_id, json.dumps(prediction), face_landmarks)
#         self.db_manager.insert_prediction(prediction_tuple)

#     def save_feedback(self, image_id, feedback, face_landmarks):
#         feedback_tuple = (feedback, image_id, face_landmarks)
#         self.db_manager.insert_feedback(feedback_tuple)

#     def retrain_model(self):
#         feedback_rows = self.db_manager.fetch_feedback()  # make sure this fetches the face landmarks too
#         formatted_data = [self.format_vw_example(row) for row in feedback_rows]
#         vw = pyvw.vw("--cb 4")
#         for example in formatted_data:
#             vw.learn(example)
#         vw.save_model('new_model.vw')

#     def load_model(self):
#         vw = pyvw.vw("--cb 4 -i new_model.vw")
#         return vw

#     @staticmethod
#     def format_vw_example(row):
#         image_id, prediction, feedback, face_landmarks = row
#         # concatenate face landmarks as a string with spaces
#         face_landmarks_string = ' '.join(map(str, face_landmarks))
#         return f"{feedback} {image_id}| {prediction} |f {face_landmarks_string}"

#     @staticmethod
#     def get_sheet_data():
#         try:
#             rows = []
#             with open('mmr.csv', newline='') as csvfile:
#                 reader = csv.reader(csvfile, delimiter=',')
#                 for row in reader:
#                     oneRow = {}
#                     oneRow["url"] = row[0]
#                     oneRow["xScale"] = row[1]
#                     oneRow["yScale"] = row[2]
#                     oneRow["xLocation"] = row[3]
#                     oneRow["yLocation"] = row[4]
#                     oneRow["rotation"] = row[5]
#                     rows.append(oneRow)
#             return rows
#         except Exception as error:
#             logging.error(f"An error occurred: {error}")
#             return None
        
# class FileProcessor:
#     def __init__(self):
#         self.job_events = {}
#         self.job_files = {}
#         self.detector = dlib.get_frontal_face_detector()
#         self.predictor = dlib.shape_predictor('/shape_predictor_68_face_landmarks.dat')

#     async def process_files(self, request, url_source_overlay, horizontal_scale, vertical_scale, xLocation, yLocation):
#         jobs = []
#         for field_name, file_storage in (await request.files).items():
#             content_type = file_storage.content_type

#             if content_type is None:
#                 raise ValueError("Invalid file type")

#             is_image = content_type.startswith("image")

#             if not is_image:
#                 raise ValueError("File is not an image")
            
#             new_job_id, new_file_path = await self.handle_image(file_storage, url_source_overlay, horizontal_scale, vertical_scale, xLocation, yLocation)
#             jobs.append(new_job_id)
#             self.job_files[new_job_id] = new_file_path

#         # Wait for all events to be set
#         await asyncio.gather(*(self.job_events[job].wait() for job in jobs))

#         # Clear events from the dictionary
#         for job in jobs:
#             del self.job_events[job]

#         return jobs

#     async def handle_image(self, file_storage, url_source_overlay, horizontal_scale, vertical_scale, xLocation, yLocation):
#         job_id = uuid.uuid4()
#         image_path = f"/pfs/{job_id}.{file_storage.filename.split('.')[-1]}"

#         # Save the uploaded image to image_path
#         with open(image_path, 'wb') as f:
#             f.write(file_storage.read())

#         # Download the overlay image
#         response = requests.get(url_source_overlay, stream=True)
#         overlay_image_path = f"/pfs/staging/overlay/{uuid.uuid4()}.png"
#         with open(overlay_image_path, 'wb') as f:
#             f.write(response.content)

#         output_image_path = f"/pfs/out/{job_id}.jpg"
#         os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

#         # Replace faces in the image
#         self.face_replace_pipeline(image_path, overlay_image_path, output_image_path, horizontal_scale, vertical_scale, xLocation, yLocation)

#         return job_id, output_image_path
    
    
#     def load_image(image_path):
#         image = cv2.imread(image_path)
#         image = imutils.resize(image, width=500)
#         return image

#     def load_overlay_image(overlay_image_path):
#         overlay_image = cv2.imread(overlay_image_path, cv2.IMREAD_UNCHANGED)
#         return overlay_image

#     def detect_faces(image, detector):
#         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#         rects = detector(gray, 1)
#         return rects

#     def get_rotation_angle(shape):
#         left_eye = np.mean(shape[36:42], axis=0)
#         right_eye = np.mean(shape[42:48], axis=0)
#         angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
#         return angle

    
#     def replace_faces(image, overlay_image, rects, horizontal_scale, vertical_scale, xLocation, yLocation, predictor):
#         for rect in rects:
#             x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()

#             # Get facial landmarks
#             shape = predictor(image, rect)
#             shape = np.array([(p.x, p.y) for p in shape.parts()])

#             # Calculate rotation angle
#             angle = get_rotation_angle(shape)

#             # Rotate overlay image
#             rows, cols, _ = overlay_image.shape
#             rotation_matrix = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
#             rotated_overlay = cv2.warpAffine(overlay_image, rotation_matrix, (cols, rows))

#             # Replace face with rotated overlay
#             w = int(w * horizontal_scale)
#             h = int(h * vertical_scale)
#             x += xLocation - w // 2
#             y += yLocation - h // 2
#             resized_overlay = cv2.resize(rotated_overlay, (w, h), interpolation=cv2.INTER_AREA)
#             for i in range(h):
#                 for j in range(w):
#                     if resized_overlay[i, j, 3] != 0:
#                         y_index = y + i
#                         x_index = x + j
#                         if 0 <= y_index < image.shape[0] and 0 <= x_index < image.shape[1]:
#                             image[y_index, x_index] = resized_overlay[i, j, 0:3]
#         return image

#     def face_replace_pipeline(self, input_image_path, overlay_image_path, output_image_path, horizontal_scale, vertical_scale, xLocation, yLocation):
#         # Load the images
#         image = load_image(input_image_path)
#         overlay_image = load_overlay_image(overlay_image_path)

#         # Initialize the face detector and facial landmarks predictor
#         print(os.listdir())
#         detector = dlib.get_frontal_face_detector()
#         predictor = dlib.shape_predictor('/shape_predictor_68_face_landmarks.dat')

#         # Detect faces in the input image
#         rects = detect_faces(image, detector)

#         # Replace faces in the input image with the overlay image
#         result_image = replace_faces(image, overlay_image, rects, horizontal_scale, vertical_scale, xLocation, yLocation, predictor)

#         # Save the result
#         cv2.imwrite(output_image_path, result_image)



# db_manager = DatabaseManager()
# image_processor = ImageProcessor(db_manager)
# file_processor = FileProcessor()


# @app.route("/uploadImageOrVideo", methods=["POST"])
# async def uploadImageOrVideo():
#     selectedMilady = (await request.form)["selectedMilady"]
#     xScale = (await request.form)["xScale"]
#     yScale = (await request.form)["yScale"]
#     xLocation = (await request.form)["xLocation"]
#     yLocation = (await request.form)["yLocation"]
#     rotation = (await request.form)["rotation"]

#     jobs = await file_processor.process_files(request, selectedMilady, xScale, yScale, xLocation, yLocation, rotation)

#     # Check for the processed image file and return the base64 encoded content
#     base64_encoded_images = {}
#     for job_id in jobs:
#         file_path = file_processor.job_files[job_id]
#         while not os.path.exists(file_path):
#             await asyncio.sleep(1)  # Check every 1 second

#         with open(file_path, "rb") as image_file:
#             encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
#             base64_encoded_images[job_id] = encoded_string

#     # Save the prediction when a prediction is made
#     save_prediction(new_job_id, prediction)

#     return json.dumps(base64_encoded_images)

# @app.route("/uploadSwappedImage", methods=["POST"])
# async def uploadSwappedImage():
#     await file_processor.save_processed_image(request)

#     return "Ack! milady 🫡"

# @app.route('/mmr', methods=['GET'])
# async def get_mmr():
#     try:
#         return json.dumps(image_processor.get_sheet_data())
#     except Exception as e:
#         return json.dumps({'error': str(e)}), 500

# @app.route('/prediction', methods=['POST'])
# async def prediction():
#     data = await request.get_json()
#     image_id = data.get('image_id', None)
#     prediction = data.get('prediction', None)
#     if image_id is not None and prediction is not None:
#         try:
#             image_processor.save_prediction(image_id, prediction)
#             return json.dumps({'success': True}), 200
#         except Exception as e:
#             return json.dumps({'error': str(e)}), 500
#     else:
#         return json.dumps({'error': 'Invalid input'}), 400

# @app.route('/feedback', methods=['POST'])
# async def feedback():
#     data = await request.get_json()
#     image_id = data.get('image_id', None)
#     feedback = data.get('feedback', None)
#     if image_id is not None and feedback is not None:
#         try:
#             image_processor.save_feedback(image_id, feedback)
#             return json.dumps({'success': True}), 200
#         except Exception as e:
#             return json.dumps({'error': str(e)}), 500
#     else:
#         return json.dumps({'error': 'Invalid input'}), 400

# @app.route('/retrain', methods=['POST'])
# async def retrain():
#     try:
#         image_processor.retrain_model()
#         return json.dumps({'success': True}), 200
#     except Exception as e:
#         return json.dumps({'error': str(e)}), 500

# @app.route('/model', methods=['GET'])
# async def model():
#     try:
#         vw = image_processor.load_model()
#         # Use vw to do something...
#         # You would probably want to use the model for a prediction
#         # and return that prediction.
#         # Return an appropriate response.
#     except Exception as e:
#         return json.dumps({'error': str(e)}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)

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

from db import DatabaseManager
from ml import MLProcessor
from fil import FileProcessor
from ap import AdminProcessor


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)
app = cors(app, allow_origin="*")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000

admin_processor = AdminProcessor(app, 'client')
admin_processor.setup_routes()
db_manager = DatabaseManager()
db_manager.initialize_db()
ml_processor = MLProcessor(db_manager)
file_processor = FileProcessor(db_manager)

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

@app.route('/stream')
async def stream():
    def event_stream():
        while True:
            feedback = db_manager.get_last_feedback()  # method that gets the last feedback entered
            yield f"data:{json.dumps(feedback)}\n\n"
            asyncio.sleep(1)  # sleep for a second before sending the next feedback
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)