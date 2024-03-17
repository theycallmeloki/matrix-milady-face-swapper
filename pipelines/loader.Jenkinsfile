pipeline {
    agent any

    environment {
        // Define the name of the image we're going to build
        DOCKER_IMAGE = 'ogmiladyloki/unzip'
        DOCKER_TAG = 'v0.0.1'
    }

    stages {
        stage('Prepare Dockerfile') {
            steps {
                // Write the functions
                writeFile file: 'loader.py', text: '''
import os
import sys

pfs_source_images = f"/pfs/{sys.argv[1]}"
for dirpath, dirs, files in os.walk(pfs_source_images):
    for file in files:
        if file.endswith((".zip")):
            print(file)
'''
                // Write the Dockerfile to the working directory
                writeFile file: 'Dockerfile', text: '''
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y unzip python3

COPY loader.py /loader.py
'''
            }
        }
        stage('Build Docker Image') {
            steps {
                // Build the Docker image from the Dockerfile in the workspace
                script {
                    def customImage = docker.build(env.DOCKER_IMAGE + ':' + env.DOCKER_TAG, '.')
                    
                    customImage.push()
                }
            }
        }
        stage('Run Face Swapper') {
            agent {
                docker {
                    image "ogmiladyloki/unzip:latest"
                    args '-u root:root'
                }
            }
            steps {
                script {
                    sh 'ls'
                    sh 'python3 /loader.py miladyzip'
                }
            }
        }
        stage('Create pachctl configuration for pipeline loader') {
            agent any
            steps {
                writeFile file: 'pipeline.json', text: '''
{
  "pipeline": {
    "name": "milady"
  },
  "input": {
    "pfs": {
      "glob": "/*",
      "repo": "miladyzip"
    }
  },
  "transform": {
    "image_pull_secrets": [
      "ogmiladykey"
    ],
    "cmd": [
      "python3",
      "/loader.py",
      "miladyzip"
    ],
    "image": "ogmiladyloki/unzip:v0.0.1"
  }
}
'''
                script {
                    sh 'pachctl update pipeline -f pipeline.json --reprocess --username ogmiladyloki || pachctl create pipeline -f pipeline.json --username ogmiladyloki'
                }
            }
        }
    }
    post {
        cleanup {
            cleanWs()
        }
    }
}
