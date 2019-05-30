# MRS-Design-Project

## What this is:

This is the Design Project of Saif Elkholy and Moetassem Abdelazmim. The work is supervised by Prof. Jamie Near.
The main python project can be found under `scripts/MRS-DP`


# General Installation:
- Install ANTS tar.gz from https://sourceforge.net/projects/advants/files/ANTS/ANTS_Latest/
- Install iTKSnap tar.gz from https://sourceforge.net/projects/itk-snap/files/itk-snap/3.8.0-beta/itksnap-3.8.0-beta-20181028-Linux-x86_64.tar.gz/download
 --> The two files above are quite big in size, they can't be included on Github. There might be a docker image of them that can be included in the Dockerfile instead (to explore).
- Save the tar.gz files in the root of the project (same level as Dockerfile)
- Install Docker either by apt-get on Linux (docker.io) or app on Windows  
- If you dont want to use Docker, just open the Dockerfile and follow the instructions (Ignore RUN, CMD, ENTRYPOINT and so on in this case)

## On Windows
- docker build -f Dockerfile . -t motassem
- Install  VcXsrv Windows X Server
- Open XLaunch
- https://dev.to/darksmile92/run-gui-app-in-linux-docker-container-on-windows-host-4kde
- Open powershell at the root folder where the Dockerfile is
- set-variable -name DISPLAY -value <YOUR-IP>:0.0
- docker run --privileged -d --rm --name=con1 -e DISPLAY=$DISPLAY motassem
- docker exec -it con1 /bin/bash

## ON LINUX
- sudo docker run --privileged -d --rm --name=con1 --net=host --env="DISPLAY" --volume="$HOME/.Xauthority:/root/.Xauthority:rw" motassem
--> https://medium.com/@SaravSun/running-gui-applications-inside-docker-containers-83d65c0db110?fbclid=IwAR065QdKw2-sD113SKqZi6jb9JBHTNdOruXWSAwaKGrYL1oMAQ4mnJGT9-4
- docker exec -it con1 /bin/bash

# Installation Finalization
## After running the Docker container
### Run these commands in the container (Linux Shell)
1- export PATH=$PATH:/usr/local/fsl/bin
2- export USER=/usr
3- export FSLDIR=/usr/local/fsl
4- source ${FSLDIR}/etc/fslconf/fsl.sh
5- If any other commands need to be included in the PATH, follow the same pattern of steps above
6- These commands can probably be included in the Dockerfile however we couldn't figure it out yet
7- Go to scripts/MRS-DP and run MRS-DP.py with python3

## TO COPY FILES FROM HOST TO DOCKER CONTAINER (AFTER RUNNING)
### this copies one of more files from host to cont or vice versa
### docker cp mycontainer:/src/. targetFolder

# Useful Docker commands 
### https://medium.com/the-code-review/top-10-docker-commands-you-cant-live-without-54fb6377f481

### System Overview:

![System Overview](https://bitbucket.org/selkholy/mrs-design-project/raw/6c892c5c5a9e8e546891f546bf54200a70894084/Diagrams/mrs-design-python-project.jpg)