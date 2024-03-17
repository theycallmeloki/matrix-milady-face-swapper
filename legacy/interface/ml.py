import json
import logging
from vowpalwabbit import pyvw

class MLProcessor:
    def __init__(self, database_manager):
        self.db_manager = database_manager

    def save_prediction(self, image_id, prediction, human_face_landmarks, anime_face_landmarks):
        prediction_tuple = (image_id, json.dumps(prediction), json.dumps(human_face_landmarks), json.dumps(anime_face_landmarks))
        self.db_manager.insert_prediction(prediction_tuple)

    def save_feedback(self, image_id, feedback, human_face_landmarks, anime_face_landmarks):
        feedback_tuple = (feedback, image_id, json.dumps(human_face_landmarks), json.dumps(anime_face_landmarks))
        self.db_manager.insert_feedback(feedback_tuple)

    def retrain_model(self):
        feedback_rows = self.db_manager.fetch_feedback()  # make sure this fetches the face landmarks too
        formatted_data = [self.format_vw_example(row) for row in feedback_rows]
        vw = pyvw.vw("--cb 4")
        for example in formatted_data:
            vw.learn(example)
        vw.save_model('new_model.vw')

    async def handle_prediction(request):
        # Request data should have 'image_id', 'human_face_landmarks', 'anime_face_landmarks' fields
        data = await request.get_json()
        image_id = data['image_id']
        human_face_landmarks = data['human_face_landmarks']
        anime_face_landmarks = data['anime_face_landmarks']

        # Use MLProcessor to generate prediction
        prediction = MLProcessor.predict_variables(human_face_landmarks, anime_face_landmarks)
        
        # Save prediction to DB along with face landmarks
        MLProcessor.save_prediction(image_id, prediction, human_face_landmarks, anime_face_landmarks)

        return {'prediction': prediction}
    
    def predict_variables(self, human_face_landmarks, anime_face_landmarks):
        # Load the trained model
        vw = self.load_model()

        # Format the face landmarks as an input for the model
        human_face_landmarks_string = ' '.join(map(str, human_face_landmarks))
        anime_face_landmarks_string = ' '.join(map(str, anime_face_landmarks))

        # Make a prediction
        prediction = vw.predict(human_face_landmarks_string + " " + anime_face_landmarks_string)

        # Here I'm assuming that prediction is a dictionary with keys 'xScale', 'yScale', 'xLocation', 'yLocation', 'rotation'
        return prediction

    def load_model(self):
        vw = pyvw.vw("--cb 4 -i new_model.vw")
        return vw

    @staticmethod
    def format_vw_example(row):
        image_id, prediction, human_face_landmarks, anime_face_landmarks, feedback = row
        face_landmarks_string = ' '.join(map(str, human_face_landmarks))
        anime_landmarks_string = ' '.join(map(str, anime_face_landmarks))
        return f"{feedback} {image_id}| {prediction} |f {face_landmarks_string} {anime_landmarks_string}"

