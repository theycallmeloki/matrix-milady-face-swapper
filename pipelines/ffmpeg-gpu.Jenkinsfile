pipeline {
    agent any
    parameters {
        stashedFile(name: 'VIDEO_FILE', description: 'Video file to be uploaded')
    }
    stages {
        stage('Transcode Video') {
            agent any
            
            steps {
                script {
                    // Unstash the video file
                    unstash 'VIDEO_FILE'
                    // Rename the file to its original filename
                    sh "mv VIDEO_FILE \${env.VIDEO_FILE_FILENAME}"
                    sh "ls -lh"
                    // Transcode the video file using NVENC
                    //sh """
                    //ffmpeg -hwaccel cuda -i \${env.VIDEO_FILE_FILENAME} \
                    //-c:v h264_nvenc -preset veryslow output_video.mkv
                    //"""
                    sh "ls -lh"
                    // Archive the transcoded video file
                    //archiveArtifacts artifacts: "output_video.mkv", onlyIfSuccessful: true, fingerprint: true
                }
            }
        }
    }
    
}
