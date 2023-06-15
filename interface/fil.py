import os
import uuid
import cv2
import dlib
import numpy as np
import requests
import shutil
import logging
import traceback
from typing import Tuple
import imutils
from aiofile import async_open
from concurrent.futures import ThreadPoolExecutor
import asyncio
# from anime_face_detector import create_detector
import logging

logger = logging.getLogger(__name__)

class SingletonPredictor:
    _predictor_instance = None
    
    @classmethod
    def get_predictor(cls):
        if cls._predictor_instance is None:
            cls._predictor_instance = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        return cls._predictor_instance

class FileProcessor:
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.job_events = {}
        self.job_files = {}
        self.human_detector = dlib.get_frontal_face_detector()
        self.human_predictor = SingletonPredictor.get_predictor()
        self.executor = ThreadPoolExecutor(max_workers=4)  
        # self.anime_detector = create_detector('yolov3')

    
    async def process_files(self, request, url_source_overlay, horizontal_scale, vertical_scale, xLocation, yLocation, rotation):
        jobs = []
        for field_name, file_storage in (await request.files).items():
            content_type = file_storage.content_type
            logger.info(f"Processing file with field name: {field_name} and content type: {content_type}")

            if content_type is None:
                logger.error("Encountered a file with no content type.")
                raise ValueError("Invalid file type")

            is_image = content_type.startswith("image")

            if not is_image:
                logger.error(f"File with field name: {field_name} is not an image. Its content type is {content_type}")
                raise ValueError("File is not an image")

            logger.info(f"Processing an image with field name: {field_name} and content type: {content_type}")
            new_job_id, new_file_path = await self.handle_image(file_storage, url_source_overlay, horizontal_scale, vertical_scale, xLocation, yLocation, rotation)
            jobs.append(new_job_id)
            self.job_files[new_job_id] = new_file_path

            logger.info(f"Successfully processed image with field name: {field_name}. Job ID: {new_job_id}")

        return jobs

    async def handle_image(self, file_storage, url_source_overlay, horizontal_scale, vertical_scale, xLocation, yLocation, rotation):
        job_id = uuid.uuid4()
        extension = file_storage.filename.split('.')[-1]
        image_path = f"/tmp/{job_id}.{extension}"
        overlay_image_path = None # Initialize here

        # Save the uploaded image to image_path
        try:
            async with async_open(image_path, 'wb') as f:
                data = await asyncio.get_event_loop().run_in_executor(
                    self.executor, file_storage.read)
                await f.write(data)

            # Make sure the overlay directory exists
            os.makedirs('/tmp/overlay', exist_ok=True)

            # Download the overlay image
            response = requests.get(url_source_overlay, stream=True)
            overlay_image_path = f"/tmp/overlay/{uuid.uuid4()}.png"
            async with async_open(overlay_image_path, 'wb') as f:
                await f.write(response.content)

            output_image_path = f"/tmp/out/{job_id}.jpg"
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

            # Replace faces in the image
            await self.face_replace_pipeline(image_path, overlay_image_path, output_image_path, horizontal_scale, vertical_scale, xLocation, yLocation, rotation)

            return job_id, output_image_path

        finally:
            # Clean up
            for path in [image_path, overlay_image_path]:
                if path is not None:  # Skip if path is None
                    try:
                        os.remove(path)
                    except Exception as e:
                        logging.error(f"Error while deleting file {path}: {str(e)}\n{traceback.format_exc()}")

    
    @staticmethod
    def load_image(image_path):
        image = cv2.imread(image_path)
        image = imutils.resize(image, width=500)
        return image

    @staticmethod
    def load_overlay_image(overlay_image_path):
        overlay_image = cv2.imread(overlay_image_path, cv2.IMREAD_UNCHANGED)
        return overlay_image

    @staticmethod
    def detect_faces(image, detector):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 1)
        return rects

    @staticmethod
    def get_rotation_angle(shape):
        left_eye = np.mean(shape[36:42], axis=0)
        right_eye = np.mean(shape[42:48], axis=0)
        angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
        return angle
    
    @staticmethod
    def rotate_image(image, angle):
        # Grab the dimensions of the image and then determine the
        # center
        (h, w) = image.shape[:2]
        center = (w / 2, h / 2)

        # Perform the rotation
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h))

        # Return the rotated image
        return rotated

    def replace_faces(self, image, overlay_image, rects, horizontal_scale, vertical_scale, xLocation, yLocation, rotation):
        for rect in rects:
            x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()

            # Get facial landmarks
            shape = self.human_predictor(image, rect)
            shape = np.array([(p.x, p.y) for p in shape.parts()])

            # Get rotation angle
            angle = FileProcessor.get_rotation_angle(shape)

            # Rotate overlay image
            overlay_image = FileProcessor.rotate_image(overlay_image, rotation)

            # Calculate scaling factors
            scaling_factor_x = w / overlay_image.shape[1] * horizontal_scale
            scaling_factor_y = h / overlay_image.shape[0] * vertical_scale

            # Resize overlay image
            overlay_image = cv2.resize(overlay_image, None, fx=scaling_factor_x, fy=scaling_factor_y)

            # Ensure that xLocation and yLocation are within the bounds of the image
            # Calculate offsets
            yLocation = int(y + yLocation - overlay_image.shape[0]/2)
            xLocation = int(x + xLocation - overlay_image.shape[1]/2)


            if yLocation < 0:
                overlay_image = overlay_image[abs(yLocation):, :]
                yLocation = 0
            if xLocation < 0:
                overlay_image = overlay_image[:, abs(xLocation):]
                xLocation = 0

            if yLocation + overlay_image.shape[0] > image.shape[0]:
                overlay_image = overlay_image[:image.shape[0] - yLocation, :]
            if xLocation + overlay_image.shape[1] > image.shape[1]:
                overlay_image = overlay_image[:, :image.shape[1] - xLocation]

            # If the overlay image has 4 channels (RGBA), use the alpha channel for merging
            if overlay_image.shape[2] == 4:
                # Split the overlay image into RGB and Alpha channels
                overlay_img_rgb = cv2.cvtColor(overlay_image, cv2.COLOR_RGBA2RGB)
                overlay_mask = overlay_image[:, :, 3]

                # We want to put logo on top-left corner, So we create a ROI
                roi = image[yLocation:yLocation + overlay_image.shape[0], xLocation:xLocation + overlay_image.shape[1]]

                # Now black-out the area of logo in ROI
                img_bg = cv2.bitwise_and(roi.copy(), roi.copy(), mask=cv2.bitwise_not(overlay_mask))

                # Take only region of logo from logo image.
                overlay_fg = cv2.bitwise_and(overlay_img_rgb, overlay_img_rgb, mask=overlay_mask)

                # Put logo in ROI and modify the main image
                image[yLocation:yLocation + overlay_image.shape[0], xLocation:xLocation + overlay_image.shape[1]] = cv2.add(img_bg, overlay_fg)
            else:
                # For RGB images, simply replace the region
                image[yLocation:yLocation + overlay_image.shape[0], xLocation:xLocation + overlay_image.shape[1]] = overlay_image

        return image



    async def face_replace_pipeline(self, image_path, overlay_image_path, output_image_path, horizontal_scale, vertical_scale, xLocation, yLocation, rotation):
        # Load images
        image = self.load_image(image_path)
        overlay_image = self.load_overlay_image(overlay_image_path)

        # Detect faces
        rects = self.detect_faces(image, self.human_detector)

        # Replace faces
        image = self.replace_faces(image, overlay_image, rects, horizontal_scale, vertical_scale, xLocation, yLocation, rotation)

        # Write output image
        cv2.imwrite(output_image_path, image)

    async def handle_upload_image_or_video_or_gif(self, request):
        form = await request.form
        print('form', form)
        files = await request.files
        print('files', files)
        url_source_overlay = form.get('urlSourceOverlay')
        horizontal_scale = float(form.get('horizontalScale'))
        vertical_scale = float(form.get('verticalScale'))
        xLocation = int(form.get('xLocation'))
        yLocation = int(form.get('yLocation'))
        rotation = int(form.get('rotation'))

        jobs = await self.process_files(request, url_source_overlay, horizontal_scale, vertical_scale, xLocation, yLocation, rotation)
        return {'jobIDs': jobs}


    async def handle_upload_swapped_image(self, request):
        jobID = await request.form.get('jobID')
        file_storage = await request.files.get('file')

        if file_storage is None:
            raise ValueError("File is not provided")

        content_type = file_storage.content_type

        if content_type is None:
            raise ValueError("Invalid file type")

        is_image = content_type.startswith("image")

        if not is_image:
            raise ValueError("File is not an image")

        swapped_image_path = self.job_files.get(jobID)
        
        if swapped_image_path is None:
            raise ValueError("Job not found")

        # Save the swapped image
        async with async_open(swapped_image_path, 'wb') as f:
            await f.write(await file_storage.read())

        return {'status': 'success'}