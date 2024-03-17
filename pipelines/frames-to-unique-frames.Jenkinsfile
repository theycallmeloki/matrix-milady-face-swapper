pipeline {
    agent {
        docker {
            image 'nikolaik/python-nodejs'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    parameters {
        stashedFile(name: 'file1')
    }
    stages {
        stage('Clear Workspace') {
            steps {
                cleanWs()
            }
        }
        stage('Prepare') {
            steps {
                script {
                    // Unstash file1 and rename it to its original 
filename
                    unstash 'file1'
                    sh 'mv file1 $file1_FILENAME'
                    
                    sh 'ls -lh'
                    
                    // Extract frames from the zip file. 
                    // Make sure the Python environment and necessary 
libraries are properly set up
                    sh 'unzip $file1_FILENAME -d images'
                }
                // Write the JavaScript file to the workspace
                writeFile file: 'varied-images.js', text: '''
                    const resemble = require('resemblejs');
                    const fs = require('fs');
                    const path = require('path');
                    
                    const images = [];
                    const folder = 'images';
                    
                    const fileList = fs.readdirSync(folder);
                    
                    fileList.forEach((file) => {
                        const imageData = 
fs.readFileSync(path.join(folder, file));
                        images.push(imageData);
                    });
                    
                    async function compareImages() {
                        const distances = [];
                    
                        for (let i = 0; i < images.length; i++) {
                            for (let j = i + 1; j < images.length; j++) {
                                const result = await 
resemble(images[i]).compareTo(images[j]).onComplete(function(data){
                                    distances.push({
                                        image1: i,
                                        image2: j,
                                        distance: data.misMatchPercentage,
                                    });
                                });
                            }
                        }
                    
                        const sortedDistances = distances.sort((a, b) => 
a.distance - b.distance);
                        const variedImages = [];
                    
                        for (let i = 0; i < sortedDistances.length; i++) {
                            const distance = sortedDistances[i].distance;
                            if (distance > 100) {
                                
variedImages.push(sortedDistances[i].image1);
                                
variedImages.push(sortedDistances[i].image2);
                            }
                        }
                    
                        console.log(variedImages);
                    }
                    
                    compareImages();

                '''
            }
        }
        stage('Install Dependencies') {
            steps {
                // Install dependencies
                sh 'npm install resemblejs'
                sh 'npm install canvas'
            }
        }
        stage('Run Image Comparison') {
            steps {
                // Run the script
                sh 'node varied-images.js'
            }
        }
    }
}

