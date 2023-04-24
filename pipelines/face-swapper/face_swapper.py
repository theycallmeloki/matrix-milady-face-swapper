import os
import sys
import argparse
import cv2
import dlib
import imutils
import numpy as np
import shutil
import uuid

pfs_source_images = f"/pfs/{sys.argv[1]}"
pfs_source_overlay = f"/pfs/{sys.argv[2]}"
horizontal_scale = float(sys.argv[3])
vertical_scale = float(sys.argv[4])

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

def replace_faces(image, overlay_image, rects, horizontal_scale, vertical_scale):
    for rect in rects:
        x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()
        w = int(w * horizontal_scale)
        h = int(h * vertical_scale)
        resized_overlay = cv2.resize(overlay_image, (w, h), interpolation=cv2.INTER_AREA)
        for i in range(h):
            for j in range(w):
                if resized_overlay[i, j, 3] != 0:
                    image[y+i, x+j] = resized_overlay[i, j, 0:3]
    return image

def face_replace_pipeline(input_image_path, overlay_image_path, output_image_path, horizontal_scale, vertical_scale):
    # Load the images
    image = load_image(input_image_path)
    overlay_image = load_overlay_image(overlay_image_path)

    # Initialize the face detector
    detector = dlib.get_frontal_face_detector()

    # Detect faces in the input image
    rects = detect_faces(image, detector)

    # Replace faces in the input image with the overlay image
    result_image = replace_faces(image, overlay_image, rects, horizontal_scale, vertical_scale)

    # Save the result
    cv2.imwrite(output_image_path, result_image)


for dirpath, dirs, files in os.walk(pfs_source_images):
    for file in files:
        if file.endswith((".jpg", ".jpeg", ".png")):
            input_image_path = os.path.join(dirpath, file)
            overlay_image_path = os.path.join(pfs_source_overlay, os.listdir(pfs_source_overlay)[0])
            output_image_path = f"/pfs/out/swapped/{uuid.uuid4()}.jpg"
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            face_replace_pipeline(input_image_path, overlay_image_path, output_image_path, horizontal_scale, vertical_scale)