import cv2
import numpy as np
import math
import argparse
import os
import mediapipe as mp
import random

from scipy.spatial.transform import Rotation as R

def get_face_orientation(face_landmarks):
    left_eye = face_landmarks[362]  # Right eye in mirrored image
    right_eye = face_landmarks[33]  # Left eye in mirrored image
    nose_tip = face_landmarks[1]

    if nose_tip.x < left_eye.x:
        return "Right"
    elif nose_tip.x > right_eye.x:
        return "Left"
    else:
        return "Center"

class YOLOv8_face:
    def __init__(self, path, conf_thres=0.2, iou_thres=0.5):
        self.conf_threshold = conf_thres
        self.iou_threshold = iou_thres
        self.class_names = ['face']
        self.num_classes = len(self.class_names)
        # Initialize model
        self.net = cv2.dnn.readNet(path)
        self.input_height = 640
        self.input_width = 640
        self.reg_max = 16

        self.project = np.arange(self.reg_max)
        self.strides = (8, 16, 32)
        self.feats_hw = [(math.ceil(self.input_height / self.strides[i]), math.ceil(self.input_width / self.strides[i])) for i in range(len(self.strides))]
        self.anchors = self.make_anchors(self.feats_hw)

    def make_anchors(self, feats_hw, grid_cell_offset=0.5):
        """Generate anchors from features."""
        anchor_points = {}
        for i, stride in enumerate(self.strides):
            h, w = feats_hw[i]
            x = np.arange(0, w) + grid_cell_offset  # shift x
            y = np.arange(0, h) + grid_cell_offset  # shift y
            sx, sy = np.meshgrid(x, y)
            # sy, sx = np.meshgrid(y, x)
            anchor_points[stride] = np.stack((sx, sy), axis=-1).reshape(-1, 2)
        return anchor_points

    def softmax(self, x, axis=1):
        x_exp = np.exp(x)
        # 如果是列向量，则axis=0
        x_sum = np.sum(x_exp, axis=axis, keepdims=True)
        s = x_exp / x_sum
        return s
    
    def resize_image(self, srcimg, keep_ratio=True):
        top, left, newh, neww = 0, 0, self.input_width, self.input_height
        if keep_ratio and srcimg.shape[0] != srcimg.shape[1]:
            hw_scale = srcimg.shape[0] / srcimg.shape[1]
            if hw_scale > 1:
                newh, neww = self.input_height, int(self.input_width / hw_scale)
                img = cv2.resize(srcimg, (neww, newh), interpolation=cv2.INTER_AREA)
                left = int((self.input_width - neww) * 0.5)
                img = cv2.copyMakeBorder(img, 0, 0, left, self.input_width - neww - left, cv2.BORDER_CONSTANT, value=(0, 0, 0))
            else:
                newh, neww = int(self.input_height * hw_scale), self.input_width
                img = cv2.resize(srcimg, (neww, newh), interpolation=cv2.INTER_AREA)
                top = int((self.input_height - newh) * 0.5)
                img = cv2.copyMakeBorder(img, top, self.input_height - newh - top, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        else:
            img = cv2.resize(srcimg, (self.input_width, self.input_height), interpolation=cv2.INTER_AREA)
        return img, newh, neww, top, left



    def detect(self, srcimg):

        input_img, newh, neww, padh, padw = self.resize_image(cv2.cvtColor(srcimg, cv2.COLOR_BGR2RGB))

        scale_h, scale_w = srcimg.shape[0] / newh, srcimg.shape[1] / neww

        input_img = input_img.astype(np.float32) / 255.0



        blob = cv2.dnn.blobFromImage(input_img)

        self.net.setInput(blob)

        outputs = self.net.forward(self.net.getUnconnectedOutLayersNames())

    def detect(self, srcimg):
        input_img, newh, neww, padh, padw = self.resize_image(cv2.cvtColor(srcimg, cv2.COLOR_BGR2RGB))
        scale_h, scale_w = srcimg.shape[0]/newh, srcimg.shape[1]/neww
        input_img = input_img.astype(np.float32) / 255.0

        blob = cv2.dnn.blobFromImage(input_img)
        self.net.setInput(blob)
        outputs = self.net.forward(self.net.getUnconnectedOutLayersNames())
        # if isinstance(outputs, tuple):
        #     outputs = list(outputs)
        # if float(cv2.__version__[:3])>=4.7:
        #     outputs = [outputs[2], outputs[0], outputs[1]] ###opencv4.7需要这一步，opencv4.5不需要
        # Perform inference on the image
        det_bboxes, det_conf, det_classid, landmarks = self.post_process(outputs, scale_h, scale_w, padh, padw)
        return det_bboxes, det_conf, det_classid, landmarks

    def post_process(self, preds, scale_h, scale_w, padh, padw):
        bboxes, scores, landmarks = [], [], []
        for i, pred in enumerate(preds):
            stride = int(self.input_height / pred.shape[2])
            pred = pred.transpose((0, 2, 3, 1))
            
            box = pred[..., :self.reg_max * 4]
            cls = 1 / (1 + np.exp(-pred[..., self.reg_max * 4:-15])).reshape((-1, 1))
            kpts = pred[..., -15:].reshape((-1, 15))

            tmp = box.reshape(-1, 4, self.reg_max)
            bbox_pred = self.softmax(tmp, axis=-1)
            bbox_pred = np.dot(bbox_pred, self.project).reshape((-1, 4))

            bbox = self.distance2bbox(self.anchors[stride], bbox_pred, max_shape=(self.input_height, self.input_width)) * stride
            kpts[:, 0::3] = (kpts[:, 0::3] * 2.0 + (self.anchors[stride][:, 0].reshape((-1, 1)) - 0.5)) * stride
            kpts[:, 1::3] = (kpts[:, 1::3] * 2.0 + (self.anchors[stride][:, 1].reshape((-1, 1)) - 0.5)) * stride
            kpts[:, 2::3] = 1 / (1 + np.exp(-kpts[:, 2::3]))

            bbox -= np.array([[padw, padh, padw, padh]])
            bbox *= np.array([[scale_w, scale_h, scale_w, scale_h]])
            kpts -= np.tile(np.array([padw, padh, 0]), 5).reshape((1, 15))
            kpts *= np.tile(np.array([scale_w, scale_h, 1]), 5).reshape((1, 15))

            bboxes.append(bbox)
            scores.append(cls)
            landmarks.append(kpts)

        bboxes = np.concatenate(bboxes, axis=0)
        scores = np.concatenate(scores, axis=0)
        landmarks = np.concatenate(landmarks, axis=0)
    
        bboxes_wh = bboxes.copy()
        bboxes_wh[:, 2:4] = bboxes[:, 2:4] - bboxes[:, 0:2]
        classIds = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)
        
        mask = confidences > self.conf_threshold
        bboxes_wh = bboxes_wh[mask]
        confidences = confidences[mask]
        classIds = classIds[mask]
        landmarks = landmarks[mask]
        
        indices = cv2.dnn.NMSBoxes(bboxes_wh.tolist(), confidences.tolist(), self.conf_threshold, self.iou_threshold).flatten()
        if len(indices) > 0:
            mlvl_bboxes = bboxes_wh[indices]
            confidences = confidences[indices]
            classIds = classIds[indices]
            landmarks = landmarks[indices]
            return mlvl_bboxes, confidences, classIds, landmarks
        else:
            print('nothing detect')
            return np.array([]), np.array([]), np.array([]), np.array([])

    def distance2bbox(self, points, distance, max_shape=None):
        x1 = points[:, 0] - distance[:, 0]
        y1 = points[:, 1] - distance[:, 1]
        x2 = points[:, 0] + distance[:, 2]
        y2 = points[:, 1] + distance[:, 3]
        if max_shape is not None:
            x1 = np.clip(x1, 0, max_shape[1])
            y1 = np.clip(y1, 0, max_shape[0])
            x2 = np.clip(x2, 0, max_shape[1])
            y2 = np.clip(y2, 0, max_shape[0])
        return np.stack([x1, y1, x2, y2], axis=-1)
    
    def draw_detections(self, image, boxes, scores, kpts, overlay_image, x_offset, y_offset, eye_to_eye_ratio, face_orientation):
        print("Boxes:", boxes)
        print("Scores:", scores)
        print("Keypoints:", kpts)

        for box, score, kp in zip(boxes, scores, kpts):
            x, y, w, h = box.astype(int)
            print("Keypoints for current face:", kp)
            kp = kp.reshape((5, 3))  # Reshape keypoints to (5, 3)
            left_eye = kp[0][:2]
            right_eye = kp[1][:2]

            angle = self.get_rotation_angle(left_eye, right_eye)

            # Determine if the face is looking left or right based on MediaPipe
            if face_orientation == "Left":
                overlay_img = overlay_image.copy()
                # angle = -angle
            else:
                overlay_img = cv2.flip(overlay_image, 1)
                # overlay_img = overlay_image.copy()
                # angle = -angle
                

            angle = self.get_rotation_angle(left_eye, right_eye)

            eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
            eye_distance = np.linalg.norm(left_eye - right_eye)

            overlay_width = int(eye_distance * eye_to_eye_ratio)
            overlay_height = int(overlay_width * overlay_img.shape[0] / overlay_img.shape[1])

            resized_overlay = cv2.resize(overlay_img, (overlay_width, overlay_height), interpolation=cv2.INTER_AREA)

            rotation_matrix = cv2.getRotationMatrix2D((overlay_width // 2, overlay_height // 2), angle, 1)
            rotated_overlay = cv2.warpAffine(resized_overlay, rotation_matrix, (overlay_width, overlay_height))

            x_start = int(eye_center[0]) - overlay_width // 2 + x_offset
            y_start = int(eye_center[1]) - overlay_height // 2 + y_offset

            for i in range(overlay_height):
                for j in range(overlay_width):
                    if rotated_overlay[i, j, 3] != 0:
                        y_index = int(y_start + i)
                        x_index = int(x_start + j)
                        if 0 <= y_index < image.shape[0] and 0 <= x_index < image.shape[1]:
                            image[y_index, x_index] = rotated_overlay[i, j, 0:3]
        return image

    def get_rotation_angle(self, left_eye, right_eye):
        angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
        return angle


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--imgpath', type=str, default='images', help="image path")
    parser.add_argument('--modelpath', type=str, default='weights/yolov8n-face.onnx', help="onnx filepath")
    parser.add_argument('--outputpath', type=str, default='output', help="output path")
    parser.add_argument('--overlaypath', type=str, default='overlays', help="overlay image path")
    parser.add_argument('--confThreshold', default=0.45, type=float, help='class confidence')
    parser.add_argument('--nmsThreshold', default=0.5, type=float, help='nms iou thresh')
    parser.add_argument('--x_offset', default=0, type=int, help='x offset for overlay placement')
    parser.add_argument('--y_offset', default=0, type=int, help='y offset for overlay placement')
    parser.add_argument('--eye_to_eye_ratio', default=7, type=float, help='Ratio of the distance between eyes to overlay width')

    args = parser.parse_args()

    # Initialize YOLOv8_face object detector
    YOLOv8_face_detector = YOLOv8_face(args.modelpath, conf_thres=args.confThreshold, iou_thres=args.nmsThreshold)
    
    # Load all overlay images from the specified directory
    overlay_images = []
    for file_name in os.listdir(args.overlaypath):
        if file_name.endswith(('.png', '.jpg', '.jpeg')):
            overlay_img = cv2.imread(os.path.join(args.overlaypath, file_name), cv2.IMREAD_UNCHANGED)
            if overlay_img is not None:
                overlay_images.append(overlay_img)

    # Create output directory if it does not exist
    if not os.path.exists(args.outputpath):
        os.makedirs(args.outputpath)

    # Process each image in the specified directory
    for img_name in sorted(os.listdir(args.imgpath)):
        img_path = os.path.join(args.imgpath, img_name)
        srcimg = cv2.imread(img_path)
        if srcimg is None:
            continue  # Skip if the image can't be read
        
        rgb_image = cv2.cvtColor(srcimg, cv2.COLOR_BGR2RGB)

        # Use MediaPipe to get face orientation
        face_orientation = "Left"  # Default value
        with mp.solutions.face_mesh.FaceMesh(static_image_mode=True) as face_mesh:
            results = face_mesh.process(rgb_image)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    face_orientation = get_face_orientation(face_landmarks.landmark)
                    print("Face is facing:", face_orientation)
                    break  # Assume one face for simplicity

        # Draw detections
        try:
            # Detect Objects
            boxes, scores, classids, kpts = YOLOv8_face_detector.detect(srcimg)
            print("Detected boxes:", boxes)
            print("Detected scores:", scores)
            print("Detected class IDs:", classids)
            print("Detected keypoints:", kpts)

            # Select a random overlay image for each face
            for i in range(len(boxes)):
                overlay_image = overlay_images[0]
                dstimg = YOLOv8_face_detector.draw_detections(
                    srcimg, boxes[i:i+1], scores[i:i+1], kpts[i:i+1], overlay_image, args.x_offset, args.y_offset, args.eye_to_eye_ratio, face_orientation
                )

            # Save the result image to the output folder
            output_img_path = os.path.join(args.outputpath, img_name)
            cv2.imwrite(output_img_path, dstimg)
        except Exception as e:
            print(f"Error processing image {img_name}: {e}")
        

    print("Processing complete. Output images saved to", args.outputpath)

    ### Legacy 


    # # Initialize YOLOv8_face object detector
    # YOLOv8_face_detector = YOLOv8_face(args.modelpath, conf_thres=args.confThreshold, iou_thres=args.nmsThreshold)
    # overlay_image = cv2.imread(args.overlaypath, cv2.IMREAD_UNCHANGED)
    
    
    # srcimg = cv2.imread(args.imgpath)
    # rgb_image = cv2.cvtColor(srcimg, cv2.COLOR_BGR2RGB)

    # # Use MediaPipe to get face orientation
    # face_orientation = "Left"  # Default value
    # with mp.solutions.face_mesh.FaceMesh(static_image_mode=True) as face_mesh:
    #     results = face_mesh.process(rgb_image)

    #     if results.multi_face_landmarks:
    #         for face_landmarks in results.multi_face_landmarks:
    #             face_orientation = get_face_orientation(face_landmarks.landmark)
    #             print("Face is facing:", face_orientation)
    #             break  # Assume one face for simplicity

    # # Detect Objects
    # boxes, scores, classids, kpts = YOLOv8_face_detector.detect(srcimg)
    # print("Detected boxes:", boxes)
    # print("Detected scores:", scores)
    # print("Detected class IDs:", classids)
    # print("Detected keypoints:", kpts)

    # # Display metadata before face replacement
    # pre_metadata_img = srcimg.copy()


    # # Draw detections
    # dstimg = YOLOv8_face_detector.draw_detections(
    #     srcimg, boxes, scores, kpts, overlay_image, 
    #     args.horizontal_scale, args.vertical_scale, args.x_offset, args.y_offset, args.eye_to_eye_ratio, face_orientation
    # )


    # # Display the images side by side
    # combined_img = np.hstack((pre_metadata_img, dstimg))
    # cv2.imshow('Metadata and Result', combined_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()