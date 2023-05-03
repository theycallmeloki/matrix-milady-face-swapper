import requests
from quart import Quart, request
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


app = Quart(__name__)
app = cors(app, allow_origin="*")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000

pachd_address = "localhost:30650"
client = python_pachyderm.Client.new_from_pachd_address(pachd_address)
# dblend_image = "laneone/distributedblender:v1.0.10"
# Replace this with the path to your service account key file
SERVICE_ACCOUNT_FILE = '../pipelines/face-swapper-image/scratch/creds.json'

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

            client.create_pipeline(
                processed,
                transform=python_pachyderm.Transform(
                    cmd=["python3", "/face_swapper.py", f"{imgswap}", f"{selectedMilady}", f"{xScale}", f"{yScale}", f"{xLocation}", f"{yLocation}"],
                    image="laneone/edith-images:7eeee5e19a024179ac2f65df0928f447",
                    image_pull_secrets=["laneonekey"],
                ),
                input=python_pachyderm.Input(
                    pfs=python_pachyderm.PFSInput(glob="/*", repo=imgswap)
                ),
            )


    return json.dumps(jobs)

        # if not (is_image or is_video):
        #     return json.dumps({"error": "File is neither image nor video"})

        # print("Filename: " + name)
        # selectedIndex = (await request.form)["selectedMilady"]
        # print("Selected Index: " + selectedIndex)
        # t = name.split(".")
        # t.pop()
        # prejobfilename = "".join(t) + ".blend"
        # new_job_id = str(uuid.uuid4())
        # jobs.append(new_job_id)
        # new_job_filename = new_job_id + ".blend"
        # print(new_job_id)
        # actual_file = f.read()
        # print("Size: " + str(len(actual_file)))

        # if not os.path.exists("/tmp/blends"):
        #     os.makedirs("/tmp/blends")

        # with open("/tmp/blends/" + new_job_filename, "wb") as reader:
        #     reader.write(actual_file)

        # swapped = new_job_id + "-toswap"

        # client.create_repo(swapped)

        # with client.commit(swapped, "master") as commit:
        #     client.put_file_bytes(
        #         commit,
        #         "/" + new_job_id,
        #         open("/tmp/blends/" + new_job_filename, "rb"),
        #     )
        #     os.remove("/tmp/blends/" + new_job_filename)

        # Handle images
    #     if is_image:
    #         # Your image processing logic here
    #         pass

    #     # Handle videos
    #     if is_video:
    #         # Your video processing logic here
    #         pass

    # return json.dumps(jobs)


# @app.route("/uploadZip", methods=["POST"])
# async def uploadZip():
#     for name, file in (await request.files).items():
#         print("Filename: " + name)
#         t = name.split(".")
#         t.pop()
#         prejobid = "".join(t)
#         prejobfilename = "".join(t) + ".zip"
#         actual_file = file.read()
#         print("Size: " + str(len(actual_file)))
#         with open("/var/www/html/zips/" + prejobfilename, "wb") as reader:
#             reader.write(actual_file)

#         blends = prejobid + "-blends"
#         splitter = prejobid + "-splitter"
#         renderer = prejobid + "-renderer"
#         merger = prejobid + "-merger"
#         watermarker = prejobid + "-watermarker"
#         unenczipper = prejobid + "-unenczipper"
#         enczipper = prejobid + "-enczipper"
#         megazipper = prejobid + "-megazipper"

#         client.delete_repo(megazipper)
#         client.delete_pipeline(megazipper)

#         client.delete_repo(unenczipper)
#         client.delete_pipeline(unenczipper)

#         client.delete_repo(watermarker)
#         client.delete_pipeline(watermarker)

#         client.delete_repo(enczipper)
#         client.delete_pipeline(enczipper)

#         client.delete_repo(merger)
#         client.delete_pipeline(merger)

#         client.delete_repo(renderer)
#         client.delete_pipeline(renderer)

#         client.delete_repo(splitter)
#         client.delete_pipeline(splitter)

#         client.delete_repo(blends)
#         print("Cleaned up job " + prejobid)

#     return "Ack!"


app.run(host="0.0.0.0", ssl_context=("adhoc"))