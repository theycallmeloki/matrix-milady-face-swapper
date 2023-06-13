import requests
from quart import Quart, request, send_file, Response
import json
import copy
from datetime import datetime
import moment
import asyncio
import os
from time import sleep
import uuid
from quart_cors import cors
import python_pachyderm
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import mimetypes
import threading
import base64
import csv
import sqlite3
from sqlite3 import Error
from vowpalwabbit import pyvw


app = Quart(__name__)
app = cors(app, allow_origin="*")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000

# Add this line to create a dictionary to store events for each job
job_events = {}
job_files = {}

def format_vw_example(row):
    image_id, prediction, feedback, _ = row
    return f"{feedback} {image_id}| {prediction}"

# Database setup
def create_connection():
    conn = None
    db_file = 'mmr.db' # Modify this path to your database file

    try:
        conn = sqlite3.connect(db_file)
        if conn:
            print(sqlite3.version)
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    try:
        sql_create_table = """ CREATE TABLE IF NOT EXISTS predictions (
                                            id integer PRIMARY KEY,
                                            image_id text NOT NULL,
                                            prediction text NOT NULL,
                                            feedback text
                                        ); """
        if conn is not None:
            c = conn.cursor()
            c.execute(sql_create_table)
    except Error as e:
        print(e)

def insert_prediction(conn, prediction):
    sql = ''' INSERT INTO predictions(image_id,prediction)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, prediction)
    return cur.lastrowid

def insert_feedback(conn, feedback):
    sql = ''' UPDATE predictions
              SET feedback = ?
              WHERE image_id = ? '''
    cur = conn.cursor()
    cur.execute(sql, feedback)
    conn.commit()

# When you make a prediction
def save_prediction(image_id, prediction):
    database = create_connection()
    create_table(database)
    
    prediction_tuple = (image_id, json.dumps(prediction))
    insert_prediction(database, prediction_tuple)

# When you receive feedback
def save_feedback(image_id, feedback):
    database = create_connection()

    feedback_tuple = (feedback, image_id)
    insert_feedback(database, feedback_tuple)

def fetch_feedback(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM predictions WHERE feedback IS NOT NULL")

    rows = cur.fetchall()

    return rows

def retrain_model():
    database = create_connection()
    feedback_rows = fetch_feedback(database)
    
    # Format the feedback and existing data in a way that VW can understand
    # You need to convert feedback, action (prediction), and context (features) into VW format
    formatted_data = [format_vw_example(row) for row in feedback_rows]
    
    # Add the new data to your existing data and retrain the model
    vw = pyvw.vw("--cb 4")
    for example in formatted_data:
        vw.learn(example)
    
    # Save the new model
    vw.save_model('new_model.vw')

def load_model():
    vw = pyvw.vw("--cb 4 -i new_model.vw")
    return vw

def get_sheet_data():
    try:
        rows = []
        # read from mmr.csv locally, along with headers
        with open('mmr.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                oneRow = {}
                oneRow["url"] = row[0]
                oneRow["x_scale"] = row[1]
                oneRow["y_scale"] = row[2]
                oneRow["x_location"] = row[3]
                oneRow["y_location"] = row[4]
                oneRow["rotation"] = row[5]
                rows.append(oneRow)

        return rows
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def sheet_data_to_json(sheet_data):
    if not sheet_data:
        return []

    headers = [header.lower() for header in sheet_data[0]]
    json_data = [dict(zip(headers, row)) for row in sheet_data[1:]]

    return json_data


@app.route('/sheet-data', methods=['GET'])
async def get_sheet_data_json():
    sheet_data = get_sheet_data()
    return json.dumps(sheet_data)

@app.route("/uploadImageOrVideo", methods=["POST"])
async def uploadImageOrVideo():
    jobs = []
    print("Number of files:", len(await request.files))
    for field_name, file_storage in (await request.files).items():
        selectedMilady = (await request.form)["selectedMilady"]
        xScale = (await request.form)["xScale"]
        yScale = (await request.form)["yScale"]
        xLocation = (await request.form)["xLocation"]
        yLocation = (await request.form)["yLocation"]
        print("Selected Milady:", selectedMilady)
        print("Field name: " + field_name)
        print("File name: " + file_storage.filename)
        print("X-Scale: " + xScale)
        print("Y-Scale: " + yScale)
        print("xLocation: " + xLocation)
        print("yLocation: " + yLocation)
        content_type = file_storage.content_type

        if content_type is None:
            return json.dumps({"error": "Invalid file type"})

        is_image = content_type.startswith("image")
        is_video = content_type.startswith("video")

        print("Is image:", is_image)
        print("Is video:", is_video)

        if not (is_image or is_video):
            return json.dumps({"error": "File is neither image nor video"})
        
        if(is_image):
            print("Image")
            # Your image processing logic here

            t = file_storage.filename.split(".")
            ext = t.pop()
            print("Extension: " + ext)
            new_job_id = str(uuid.uuid4())
            jobs.append(new_job_id)
            print(new_job_id)
            actual_file = file_storage.read()
            # create a directory to store the blend files
            if not os.path.exists("/tmp/blends"):
                os.makedirs("/tmp/blends")
            with open("/tmp/blends/" + new_job_id + '.' + ext, "wb") as reader:
                reader.write(actual_file)
            print("Size: " + str(len(actual_file)))

            imgswap = new_job_id + "-imgswap"

            clientCreateRepo = f"pachctl create repo {imgswap}"
            print("running: " + clientCreateRepo)
            os.system(clientCreateRepo)
            

            putFileRepo = f"pachctl put file {imgswap}@master:/{new_job_id}.{ext} -f /tmp/blends/{new_job_id}.{ext}"
            print("running: " + putFileRepo)
            os.system(putFileRepo)
            os.remove("/tmp/blends/" + new_job_id + '.' + ext)

            processed = new_job_id + "-img-prcsd"
            clientCreateRepo = f"pachctl create repo {processed}"
            print("running: " + clientCreateRepo)
            os.system(clientCreateRepo)

            print("xScale: " + xScale)
            print("yScale: " + yScale)
            print("xLocation: " + xLocation)
            print("yLocation: " + yLocation)

            jsonPipeline = {}
            jsonPipeline["pipeline"] = {}
            jsonPipeline["pipeline"]["name"] = processed
            jsonPipeline["input"] = {}
            jsonPipeline["input"]["pfs"] = {}
            jsonPipeline["input"]["pfs"]["glob"] = "/*"
            jsonPipeline["input"]["pfs"]["repo"] = imgswap
            jsonPipeline["transform"] = {}
            jsonPipeline["transform"]["cmd"] = ["python3", "/face_swapper.py", f"{imgswap}", f"{selectedMilady}", "https://api.matrixmilady.com/uploadSwappedImage", f"{xScale}", f"{yScale}", f"{xLocation}", f"{yLocation}", f"{rotation}"]
            jsonPipeline["transform"]["image"] = "laneone/edith-images:221df1ab01c548a29be649f0e92ea06c"
            jsonPipeline["transform"]["image_pull_secrets"] = ["laneonekey"]

            createPipeline = f"pachctl create pipeline -f - <<EOF\n{json.dumps(jsonPipeline)}\nEOF"
            print("running: " + createPipeline)
            os.system(createPipeline)

            job_events[new_job_id] = asyncio.Event()

            job_files[new_job_id] = f"/tmp/swappedimage/{new_job_id}.jpg"

    # Wait for all events to be set
    await asyncio.gather(*(job_events[job].wait() for job in jobs))
    # Clear events from the dictionary
    for job in jobs:
        del job_events[job]


    # Check for the processed image file and return the base64 encoded content
    base64_encoded_images = {}
    for job_id in jobs:
        file_path = job_files[job_id]
        while not os.path.exists(file_path):
            await asyncio.sleep(1)  # Check every 1 second

        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            base64_encoded_images[job_id] = encoded_string

    # Save the prediction when a prediction is made
    save_prediction(new_job_id, prediction)

    return json.dumps(base64_encoded_images)

@app.route("/uploadSwappedImage", methods=["POST"])
async def uploadSwappedImage():
    jobs = []
    print("Number of files:", len(await request.files))
    for field_name, file_storage in (await request.files).items():
        print("Field name: " + field_name)
        print("File name: " + file_storage.filename)
        prejobid = file_storage.filename.split(".")[0]
        actual_file = file_storage.read()
        print("Size: " + str(len(actual_file)))
        # create a directory to store the blend files
        if not os.path.exists("/tmp/swappedimage"):
            os.makedirs("/tmp/swappedimage")
        
        with open("/tmp/swappedimage/" + prejobid + ".jpg", "wb") as reader:
            reader.write(actual_file)
        
        imgswap = prejobid + "-imgswap"
        processed = prejobid + "-img-prcsd"
        # client.delete_repo(processed)
        clientDeleteProcessed = f"pachctl delete repo {processed}"
        print("running: " + clientDeleteProcessed)
        os.system(clientDeleteProcessed)
        # client.delete_pipeline(processed)
        clientDeletePipeline = f"pachctl delete pipeline {processed}"
        print("running: " + clientDeletePipeline)
        os.system(clientDeletePipeline)

        # client.delete_repo(imgswap)
        clientDeleteImgswap = f"pachctl delete repo {imgswap}"
        print("running: " + clientDeleteImgswap)
        os.system(clientDeleteImgswap)
        print("Cleaned up job " + prejobid)

    # Set the event for this job, signaling that it's complete
    job_events[prejobid].set()

    return "Ack! milady 🫡"
        
app.run(host="0.0.0.0", ssl_context=("adhoc"))
