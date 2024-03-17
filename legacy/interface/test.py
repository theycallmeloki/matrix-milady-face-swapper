import unittest
import requests
import os

class TestApplicationFlow(unittest.TestCase):
    BASE_URL = 'http://localhost:5000'  # Replace with your FastAPI server URL

    def test_application_flow(self):
        # Upload an image
        with open('test.jpg', 'rb') as f:
            response = requests.post(
                f'{self.BASE_URL}/uploadImageOrVideo',
                files={'file': ('test.jpg', open('test.jpg', 'rb'), 'image/jpeg')},
                data={
                    'urlSourceOverlay': 'https://i.imgur.com/wZH4GjE.png',
                    'horizontalScale': '3.0',
                    'verticalScale': '3.0',
                    'xLocation': '50',
                    'yLocation': '0',
                    'rotation': '0'
                }
            )
        
        self.assertEqual(response.status_code, 200)

        # Get the job ID
        job_id = response.json()['jobIDs'][0]

        # Check the prediction
        response = requests.get(f'{self.BASE_URL}/prediction/{job_id}')
        self.assertEqual(response.status_code, 200)

        # Submit feedback
        response = requests.post(
            f'{self.BASE_URL}/feedback/{job_id}',
            data={'feedback': '1'}
        )
        self.assertEqual(response.status_code, 200)

        # Retrain the model
        response = requests.post(f'{self.BASE_URL}/retrain')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
