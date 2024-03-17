# [milady.ing](https://milady.ing)

### Get milady [dataset](https://huggingface.co/datasets/hayden-donnelly/milady)

``` 
git clone git@hf.co:datasets/hayden-donnelly/milady
```

### Keep a runner ready ([MiladyOS](https://github.com/theycallmeloki/MiladyOS))

```
docker run -d --name miladyos --privileged --user root --restart=unless-stopped --net=host --env JENKINS_ADMIN_ID=admin --env JENKINS_ADMIN_PASSWORD=password -v /var/run/docker.sock:/var/run/docker.sock ogmiladyloki/miladyos
```

### TODO 

###### [ ] Generate a seperate dreambooth model for the subject postfixed with a specific milady face