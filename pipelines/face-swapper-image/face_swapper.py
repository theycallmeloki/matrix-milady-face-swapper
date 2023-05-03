import os
import sys
import argparse
import cv2
import dlib
import imutils
import numpy as np
import shutil
import uuid
import requests

pfs_source_images = f"/pfs/{sys.argv[1]}"
job_id_with_ext = os.listdir(pfs_source_images)[0]
job_id = job_id_with_ext.split('.')[0]
url_source_overlay = f"{sys.argv[2]}"
response_destination_endpoint = f"{sys.argv[3]}"
horizontal_scale = float(sys.argv[4])
vertical_scale = float(sys.argv[5])
xLocation = int(sys.argv[6])
yLocation = int(sys.argv[7])

print("pfs_source_images: " + pfs_source_images)
print("job_id_with_ext: " + job_id_with_ext)
print("job_id: " + job_id)
print("url_source_overlay: " + url_source_overlay)
print("response_destination_endpoint: " + response_destination_endpoint)
print("horizontal_scale: " + str(horizontal_scale))
print("vertical_scale: " + str(vertical_scale))
print("xLocation: " + str(xLocation))
print("yLocation: " + str(yLocation))


def load_image(image_path):
    image = cv2.imread(image_path)
    image = imutils.resize(image, width=500)
    return image

def load_overlay_image(overlay_image_path):
    overlay_image = cv2.imread(overlay_image_path, cv2.IMREAD_UNCHANGED)
    return overlay_image

def detect_faces(image, detector):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 1)
    return rects

def get_rotation_angle(shape):
    left_eye = np.mean(shape[36:42], axis=0)
    right_eye = np.mean(shape[42:48], axis=0)
    angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
    return angle

def replace_faces(image, overlay_image, rects, horizontal_scale, vertical_scale, xLocation, yLocation, predictor):
    for rect in rects:
        x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()

        # Get facial landmarks
        shape = predictor(image, rect)
        shape = np.array([(p.x, p.y) for p in shape.parts()])

        # Calculate rotation angle
        angle = get_rotation_angle(shape)

        # Rotate overlay image
        rows, cols, _ = overlay_image.shape
        rotation_matrix = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
        rotated_overlay = cv2.warpAffine(overlay_image, rotation_matrix, (cols, rows))

        # Replace face with rotated overlay
        w = int(w * horizontal_scale)
        h = int(h * vertical_scale)
        x += xLocation - w // 2
        y += yLocation - h // 2
        resized_overlay = cv2.resize(rotated_overlay, (w, h), interpolation=cv2.INTER_AREA)
        for i in range(h):
            for j in range(w):
                if resized_overlay[i, j, 3] != 0:
                    y_index = y + i
                    x_index = x + j
                    if 0 <= y_index < image.shape[0] and 0 <= x_index < image.shape[1]:
                        image[y_index, x_index] = resized_overlay[i, j, 0:3]
    return image

def face_replace_pipeline(input_image_path, overlay_image_path, output_image_path, horizontal_scale, vertical_scale, xLocation, yLocation):
    # Load the images
    image = load_image(input_image_path)
    overlay_image = load_overlay_image(overlay_image_path)

    # Initialize the face detector and facial landmarks predictor
    print(os.listdir())
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor('/shape_predictor_68_face_landmarks.dat')

    # Detect faces in the input image
    rects = detect_faces(image, detector)

    # Replace faces in the input image with the overlay image
    result_image = replace_faces(image, overlay_image, rects, horizontal_scale, vertical_scale, xLocation, yLocation, predictor)

    # Save the result
    cv2.imwrite(output_image_path, result_image)


for dirpath, dirs, files in os.walk(pfs_source_images):
    for file in files:
        if file.endswith((".jpg", ".jpeg", ".png")):
            input_image_path = os.path.join(dirpath, file)
            # overlay_image_path = os.path.join(pfs_source_overlay, os.listdir(pfs_source_overlay)[0])
            # retrieve the overlay image from the url with requests, store it in a temp file, and then use that temp file as the overlay image
            request = requests.get(url_source_overlay, stream=True)
            # create /pfs/staging/overlay if it doesn't exist
            os.makedirs("/pfs/staging/overlay", exist_ok=True)
            overlay_image_path = f"/pfs/staging/overlay/{uuid.uuid4()}.png"
            with open(overlay_image_path, 'wb') as f:
                f.write(request.content)

            output_image_path = f"/pfs/out/{job_id}.jpg"
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            face_replace_pipeline(input_image_path, overlay_image_path, output_image_path, horizontal_scale, vertical_scale, xLocation, yLocation)
            # do something like this: files = {job_id + ".zip": open("/pfs/out/" + job_id + ".zip", "rb")}
            files = {job_id + ".jpg": open(output_image_path, "rb")}
            # do something like this: requests.post("http://localhost:3000/api/v1/jobs/" + job_id + "/results", files=files)
            r = requests.post(f"{response_destination_endpoint}", files=files)
            print(r.text)