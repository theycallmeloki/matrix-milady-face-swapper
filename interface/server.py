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


app = Quart(__name__)
app = cors(app, allow_origin="*")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000


# Add this line to create a dictionary to store events for each job
job_events = {}
job_files = {}


# pachd_address = "0.0.0.0:30650"
# client = python_pachyderm.Client.new_from_pachd_address(pachd_address)
# dblend_image = "laneone/distributedblender:v1.0.10"
# Replace this with the path to your service account key file
# SERVICE_ACCOUNT_FILE = '../creds.json'

# The ID of your Google Sheet
# SPREADSHEET_ID = '1pCCSCKxHyDsBqF_Vy7Fw39_V4Q7Wg6NuKQWYchmr8P8'

# The range of data you want to access (e.g., 'Sheet1!A1:Z100')
# RANGE_NAME = 'Reference!A1:Z200'

# Load the service account credentials
# credentials = service_account.Credentials.from_service_account_file(
    # SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])

# sheets_api = build('sheets', 'v4', credentials=credentials)


def get_sheet_data():
    try:
        rows = []
        # read from mmr.csv locally, along with headers
        with open('mmr.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                oneRow = {}
                oneRow["url"] = row[0]
                oneRow["xScale"] = row[1]
                oneRow["yScale"] = row[2]
                oneRow["xLocation"] = row[3]
                oneRow["yLocation"] = row[4]
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

# @app.route('/download/<job_id>', methods=['GET'])
# async def download_processed_file(job_id):
#     file_path = job_files.get(job_id)
#     if file_path is None:
#         return "File not found", 404
#     if not os.path.exists(file_path):
#         return "File not found", 404

#     # Get the file name and extension
#     file_name = os.path.basename(file_path)

#     # Send the file as a response with the Content-Disposition header
#     return await send_file(file_path, attachment_filename=file_name, as_attachment=True)

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

            # client.create_repo(imgswap)
            clientCreateRepo = f"pachctl create repo {imgswap}"
            print("running: " + clientCreateRepo)
            os.system(clientCreateRepo)
            

            # with client.commit(imgswap, "master") as commit:
            #     client.put_file_bytes(
            #         commit,
            #         "/" + new_job_id + '.' + ext,
            #         open("/tmp/blends/" + new_job_id + '.' + ext, "rb"),
            #     )
            #     os.remove("/tmp/blends/" + new_job_id + '.' + ext)

            putFileRepo = f"pachctl put file {imgswap}@master:/{new_job_id}.{ext} -f /tmp/blends/{new_job_id}.{ext}"
            print("running: " + putFileRepo)
            os.system(putFileRepo)
            os.remove("/tmp/blends/" + new_job_id + '.' + ext)


            processed = new_job_id + "-img-prcsd"
            # client.create_repo(processed)
            clientCreateRepo = f"pachctl create repo {processed}"
            print("running: " + clientCreateRepo)
            os.system(clientCreateRepo)

            print("xScale: " + xScale)
            print("yScale: " + yScale)
            print("xLocation: " + xLocation)
            print("yLocation: " + yLocation)

            # client.create_pipeline(
            #     processed,
            #     transform=python_pachyderm.Transform(
            #         cmd=["python3", "/face_swapper.py", f"{imgswap}", f"{selectedMilady}", "https://api.matrixmilady.com/uploadSwappedImage", f"{xScale}", f"{yScale}", f"{xLocation}", f"{yLocation}"],
            #         image="laneone/edith-images:221df1ab01c548a29be649f0e92ea06c",
            #         image_pull_secrets=["laneonekey"],
            #     ),
            #     input=python_pachyderm.Input(
            #         pfs=python_pachyderm.PFSInput(glob="/*", repo=imgswap)
            #     ),
            # )

            jsonPipeline = {}
            jsonPipeline["pipeline"] = {}
            jsonPipeline["pipeline"]["name"] = processed
            jsonPipeline["input"] = {}
            jsonPipeline["input"]["pfs"] = {}
            jsonPipeline["input"]["pfs"]["glob"] = "/*"
            jsonPipeline["input"]["pfs"]["repo"] = imgswap
            jsonPipeline["transform"] = {}
            jsonPipeline["transform"]["cmd"] = ["python3", "/face_swapper.py", f"{imgswap}", f"{selectedMilady}", "https://api.matrixmilady.com/uploadSwappedImage", f"{xScale}", f"{yScale}", f"{xLocation}", f"{yLocation}"]
            jsonPipeline["transform"]["image"] = "laneone/edith-images:221df1ab01c548a29be649f0e92ea06c"
            jsonPipeline["transform"]["image_pull_secrets"] = ["laneonekey"]

            # with open("/tmp/pipeline.json", "w") as outfile:
            #     json.dump(jsonPipeline, outfile)

            # createPipeline = f"pachctl create pipeline -f /tmp/pipeline.json"

            # cmd = f"pachctl create pipeline -f - <<EOF\n{config_str}\nEOF"

            createPipeline = f"pachctl create pipeline -f - <<EOF\n{json.dumps(jsonPipeline)}\nEOF"
            print("running: " + createPipeline)
            os.system(createPipeline)


            # Create and store an event for this job
            job_events[new_job_id] = asyncio.Event()

            # Store the file path for the processed image	
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
        
async def display_job_files():
    while True:
        for job_id, file_path in job_files.items():
            if os.path.exists(file_path):
                print(f"File path for job {job_id}: {file_path}")
        await asyncio.sleep(10)

app.run(host="0.0.0.0", ssl_context=("adhoc"), background_tasks=[display_job_files()])
