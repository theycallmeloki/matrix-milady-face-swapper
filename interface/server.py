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


app = Quart(__name__)
app = cors(app, allow_origin="*")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000


# Add this line to create a dictionary to store events for each job
job_events = {}
job_files = {}


pachd_address = "localhost:30650"
client = python_pachyderm.Client.new_from_pachd_address(pachd_address)
# dblend_image = "laneone/distributedblender:v1.0.10"
# Replace this with the path to your service account key file
SERVICE_ACCOUNT_FILE = '/tmp/creds.json'

# The ID of your Google Sheet
SPREADSHEET_ID = '1pCCSCKxHyDsBqF_Vy7Fw39_V4Q7Wg6NuKQWYchmr8P8'

# The range of data you want to access (e.g., 'Sheet1!A1:Z100')
RANGE_NAME = 'Reference!A1:Z100'

# Load the service account credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])

sheets_api = build('sheets', 'v4', credentials=credentials)


def get_sheet_data(spreadsheet_id, range_name):
    try:
        result = sheets_api.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        rows = result.get('values', [])
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
    sheet_data = get_sheet_data(SPREADSHEET_ID, RANGE_NAME)
    json_data = sheet_data_to_json(sheet_data)
    return json.dumps(json_data)

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
            client.create_repo(imgswap)

            with client.commit(imgswap, "master") as commit:
                client.put_file_bytes(
                    commit,
                    "/" + new_job_id + '.' + ext,
                    open("/tmp/blends/" + new_job_id + '.' + ext, "rb"),
                )
                os.remove("/tmp/blends/" + new_job_id + '.' + ext)

            processed = new_job_id + "-img-prcsd"
            client.create_repo(processed)
            print("xScale: " + xScale)
            print("yScale: " + yScale)
            print("xLocation: " + xLocation)
            print("yLocation: " + yLocation)

            client.create_pipeline(
                processed,
                transform=python_pachyderm.Transform(
                    cmd=["python3", "/face_swapper.py", f"{imgswap}", f"{selectedMilady}", "http://192.168.0.221:5000/uploadSwappedImage", f"{xScale}", f"{yScale}", f"{xLocation}", f"{yLocation}"],
                    image="laneone/edith-images:221df1ab01c548a29be649f0e92ea06c",
                    image_pull_secrets=["laneonekey"],
                ),
                input=python_pachyderm.Input(
                    pfs=python_pachyderm.PFSInput(glob="/*", repo=imgswap)
                ),
            )
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
        client.delete_repo(processed)
        client.delete_pipeline(processed)

        client.delete_repo(imgswap)
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
