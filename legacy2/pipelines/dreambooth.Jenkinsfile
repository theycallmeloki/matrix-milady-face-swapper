
// #@title Check GPU and VRAM available. (Optional)
// !nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
// print("\n\033[92mIf the available VRAM is equal or more than 24GB, then you are good to go.\033[0m") 
     

// #@title 1. Clone & Download The Repo
// !git clone https://github.com/JoePenna/Dreambooth-Stable-Diffusion
// %cd Dreambooth-Stable-Diffusion
     

// #@title 2. Build The Environment
// #@markdown You might get warnings about restarting the runtime. Do this from the Runtime menu and after restarting, resume from Cell.
// !pip install numpy==1.23.1
// !pip install pytorch-lightning==1.7.6
// !pip install csv-logger
// !pip install torchmetrics==0.11.1
// !pip install torch-fidelity==0.3.0
// !pip install albumentations==1.1.0
// !pip install opencv-python==4.7.0.72
// !pip install pudb==2019.2
// !pip install omegaconf==2.1.1
// !pip install pillow==9.4.0
// !pip install einops==0.4.1
// !pip install transformers==4.25.1
// !pip install kornia==0.6.7
// !pip install diffusers[training]==0.3.0
// !pip install captionizer==1.0.1
// !pip install -e git+https://github.com/CompVis/taming-transformers.git@master#egg=taming-transformers
// !pip install -e git+https://github.com/openai/CLIP.git@main#egg=clip
// !pip install -e .
// !pip install huggingface_hub
// !pip install gitpython

// import os
// os._exit(00)
     

// #@title 3. Just to ensure you are in the right directory.
// %cd Dreambooth-Stable-Diffusion
     

// #@title 4. Download the 1.5 SD model with the improved VAE
// from IPython.display import clear_output

// from huggingface_hub import hf_hub_download
// downloaded_model_path = hf_hub_download(
//  repo_id="panopstor/EveryDream",
//  filename="sd_v1-5_vae.ckpt"
// )

// # Move the sd_v1-5_vae.ckpt to the root of this directory as "model.ckpt"
// actual_locations_of_model_blob = !readlink -f {downloaded_model_path}
// !mv {actual_locations_of_model_blob[-1]} model.ckpt
// clear_output()
// print("✅ model.ckpt successfully downloaded")

     

// #@title 5. Download Regularization Images
// #@markdown We’ve created the following image sets
// #@markdown - `man_euler` - provided by Niko Pueringer (Corridor Digital) - euler @ 40 steps, CFG 7.5
// #@markdown - `man_unsplash` - pictures from various photographers
// #@markdown - `person_ddim`
// #@markdown - `woman_ddim` - provided by David Bielejeski - ddim @ 50 steps, CFG 10.0 
// #@markdown - `artstyle` - provided by Hackmans - ddim @ 50 steps, CFG 10.0 

// dataset="person_ddim" #@param ["man_euler", "man_unsplash", "person_ddim", "woman_ddim", "artstyle"]
// !git clone https://github.com/djbielejeski/Stable-Diffusion-Regularization-Images-{dataset}.git

// !mkdir -p regularization_images/{dataset}
// !mv -v Stable-Diffusion-Regularization-Images-{dataset}/{dataset}/*.* regularization_images/{dataset}

// # remove temp folder now it is empty. 
// !rm -rf Stable-Diffusion-Regularization-Images-{dataset}

// clear_output()
// print("✅ \033[92mRegularization Images downloaded.\033[0m")
     

// #@title 6. Training Images
// #@markdown ## Upload your training images
// #@markdown WARNING: Be sure to upload an even amount of images, otherwise the training inexplicably stops at 1500 steps. 
// #@markdown - 2-3 full body
// #@markdown - 3-5 upper body
// #@markdown - 5-12 close-up on face   
// #@markdown The images should be as close as possible to the kind of images you’re trying to make (most of the time, that means no selfies).
// #@markdown If you get an error during uploading, just manually drag your training images into the training_images folder.
// from google.colab import files
// from IPython.display import clear_output

// # Create the directory
// !rm -rf training_images
// !mkdir -p training_images

// # Upload the files
// uploaded = files.upload()
// for filename in uploaded.keys():
//  updated_file_name = filename.replace(" ", "_")
//  !mv "{filename}" "training_images/{updated_file_name}"
//  clear_output()

// # Tell the user what is going on
// training_images_file_paths = !find training_images/*
// if len(training_images_file_paths) == 0:
//  print("❌ \033[91mno training images found. Please upload images to training_images.\033[0m")
// else:
//  print("✅ \033[92m" + str(len(training_images_file_paths)) + " training images found.\033[0m")


     

// #@title 7. Final Setup & Training

// #@markdown This isn't used for training, just used to name the folders etc
// project_name = "project_name" #@param {type:"string"}

// #@markdown This is the unique token i.e. you can use a nonsensical word like zwx or your name.
// token = "firstNamelastName" #@param {type:"string"}

// #@markdown Match class_word to the category of the regularization images you chose above.
// class_word = "person" #@param ["man", "person", "woman"] {allow-input: true}

// # MAX STEPS
// #@markdown How many steps do you want to train for?
// max_training_steps = 2000 #@param {type:"integer"}

// #@markdown If you are training a person's face, set this to True
// i_am_training_a_persons_face = True #@param {type:"boolean"}
// flip_p_arg = 0.0 if i_am_training_a_persons_face else 0.5

// #@markdown Would you like to save a model every X steps? (Example: 250 would output a trained model at 250, 500, 750 steps, etc)
// save_every_x_steps = 0 #@param {type:"integer"}


// reg_data_root = "/content/Dreambooth-Stable-Diffusion/regularization_images/" + dataset

// !rm -rf training_images/.ipynb_checkpoints
// !python "main.py" \
//  --project_name "{project_name}" \
//  --debug False \
//  --max_training_steps {max_training_steps} \
//  --token "{token}" \
//  --training_model "model.ckpt" \
//  --training_images "/content/Dreambooth-Stable-Diffusion/training_images" \
//  --regularization_images "{reg_data_root}" \
//  --class_word "{class_word}" \
//  --flip_p {flip_p_arg} \
//  --save_every_x_steps {save_every_x_steps}
     

// #@title 8. Save model into google drive
// #@markdown This is often much faster than a manual download.  it will also save you compute units. 
// from google.colab import drive
// drive.mount('/content/drive')

// # copy all ckpt files to google drive root dir
// !cp trained_models/*.ckpt /content/drive/MyDrive

pipeline {
    agent any

    parameters {
        file(name: 'TRAINING_IMAGES', description: 'Training files to be uploaded in a zip')
        file(name: 'REGULARIZATION_IMAGES', description: 'Regularization files to be uploaded in a zip')
        string(name: 'PROJECT_NAME', defaultValue: 'project_name', description: 'Project Name')
        string(name: 'TOKEN', defaultValue: 'firstNamelastName', description: 'Unique token')
        string(name: 'CLASS_WORD', defaultValue: 'person', description: 'Match class_word to the category of the regularization images')
        booleanParam(name: 'TRAINING_A_PERSONS_FACE', defaultValue: true, description: 'If you are training a person\'s face, set this to True')
        integer(name: 'MAX_TRAINING_STEPS', defaultValue: 2000, description: 'How many steps do you want to train for?')
        integer(name: 'SAVE_EVERY_X_STEPS', defaultValue: 0, description: 'Would you like to save a model every X steps? (Example: 250 would output a trained model at 250, 500, 750 steps, etc)')
        
    }

    stages {
        stage('Build Docker Image') {
            steps {
                script {
                    def dockerfilePath = 'Dockerfile'
                    def dockerfileContent = '''
                    FROM python:3.8
                    WORKDIR /app

                    RUN apt-get update && apt-get install -y \\
                        git \\
                        wget \\
                        nvidia-smi \\
                        && rm -rf /var/lib/apt/lists/*

                    # Installing python dependencies
                    RUN pip install numpy==1.23.1 \\
                        pytorch-lightning==1.7.6 \\
                        csv-logger \\
                        torchmetrics==0.11.1 \\
                        torch-fidelity==0.3.0 \\
                        albumentations==1.1.0 \\
                        opencv-python==4.7.0.72 \\
                        pudb==2019.2 \\
                        omegaconf==2.1.1 \\
                        pillow==9.4.0 \\
                        einops==0.4.1 \\
                        transformers==4.25.1 \\
                        kornia==0.6.7 \\
                        diffusers[training]==0.3.0 \\
                        captionizer==1.0.1 \\
                        git+https://github.com/CompVis/taming-transformers.git@master#egg=taming-transformers \\
                        git+https://github.com/openai/CLIP.git@main#egg=clip \\
                        huggingface_hub \\
                        gitpython
                    '''

                    // Write Dockerfile
                    writeFile file: dockerfilePath, text: dockerfileContent
                    
                    // Build Docker image
                    def image = docker.build('laneone/edith-images:dreambooth_v0.0.1')

                    // Login to Docker registry and push the image
                    sh "echo Mostwanted1 | docker login -u laneone --password-stdin"
                    // Push Docker image
                    image.push()
                }
            }
        }

        stage('Clone & Build') {
            steps {
                script {
                    sh 'git clone https://github.com/JoePenna/Dreambooth-Stable-Diffusion && cd Dreambooth-Stable-Diffusion && pip install -e .'
                }
            }
        }

        stage('Upload Training Images') {
            steps {
                script {
                    // Unstash TRAINING_IMAGES and rename it to its original filename
                    unstash 'TRAINING_IMAGES'
                    sh 'mv TRAINING_IMAGES $TRAINING_IMAGES_FILENAME'
                }
            }
        }

        stage('Upload Regularization Images') {
            steps {
                script {
                    // Unstash REGULARIZATION_IMAGES and rename it to its original filename
                    unstash 'REGULARIZATION_IMAGES'
                    sh 'mv REGULARIZATION_IMAGES $REGULARIZATION_IMAGES_FILENAME'
                }
            }
        }

        stage('Train') {
            steps {
                script {
                    // Run the training script
                    sh '''
                    python /Dreambooth-Stable-Diffusion/main.py \\
                        --project_name "${PROJECT_NAME}" \\
                        --debug False \\
                        --max_training_steps ${MAX_TRAINING_STEPS} \\
                        --token "${TOKEN}" \\
                        --training_model "/Dreambooth-Stable-Diffusion/model.ckpt" \\
                        --training_images "/${WORKSPACE}/${TRAINING_IMAGES_FILENAME}" \\
                        --regularization_images "/${WORKSPACE}/${REGULARIZATION_IMAGES_FILENAME}" \\
                        --class_word "${CLASS_WORD}" \\
                        --flip_p 0.0 \\
                        --save_every_x_steps ${SAVE_EVERY_X_STEPS}
                    '''
                }
            }
        }

        stage('Save Model') {
            steps {
                script {
                    // Create the directory
                    sh 'mkdir -p /output'

                    // Copy the trained model to the output directory
                    sh 'cp /Dreambooth-Stable-Diffusion/trained_models/*.ckpt /output'
                }
            }
        }

        
    }
}
