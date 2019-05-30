FROM ubuntu:latest

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y 	gcc \
			wget \
			vim \
			vis \
			sudo \
			iputils-ping \
			net-tools \
			netcat \
			htop \
			git \
			&& apt-get clean

#cmake \
#cmake-curses-gui \
#zlib1g-dev \


RUN apt-get install -y build-essential checkinstall

COPY . /usr/src/mrs-design-project

RUN apt-get install -y python python3
RUN apt-get install -y python3-pip python3-tk python-wxtools ants

RUN pip3 install fslpy nipype pandas scikit-image plotly webcolors wc
RUN pip3 install https://www.github.com/ANTsX/ANTsPy/releases/download/v0.1.4/antspy-0.1.4-cp36-cp36m-linux_x86_64.whl

WORKDIR /usr/src/mrs-design-project
RUN python fslinstaller.py -d /usr/local/fsl

RUN tar xzf itksnap-3.8.0-beta-20181028-Linux-x86_64.tar.gz
RUN tar xzf ANTs-2.1.0-rc3-Linux.tar.gz

#RUN export PATH=$PATH:/usr/local/fsl/bin
#RUN export USER=/usr
#RUN export FSLDIR=/usr/local/fsl
#RUN source ${FSLDIR}/etc/fslconf/fsl.sh

WORKDIR /home
ENTRYPOINT ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

WORKDIR /usr/src/mrs-design-project

# ON WINDOWS
## docker build -f Dockerfile . -t motassem 
## Install  VcXsrv Windows X Server
## Open XLaunch
## https://dev.to/darksmile92/run-gui-app-in-linux-docker-container-on-windows-host-4kde
## On powershell
## set-variable -name DISPLAY -value <YOUR-IP>:0.0
## docker run --privileged -d --rm --name=con1 -e DISPLAY=$DISPLAY motassem
## docker exec -it con1 /bin/bash


# ON LINUX
## sudo docker run --privileged -d --rm --name=con1 --net=host --env="DISPLAY" --volume="$HOME/.Xauthority:/root/.Xauthority:rw" motassem
## https://medium.com/@SaravSun/running-gui-applications-inside-docker-containers-83d65c0db110?fbclid=IwAR065QdKw2-sD113SKqZi6jb9JBHTNdOruXWSAwaKGrYL1oMAQ4mnJGT9-4

# TO COPY FILES FROM HOST TO DOCKER CONTAINER (AFTER RUNNING)
## this copies one of more files from host to cont or vice versa
## docker cp mycontainer:/src/. targetFolder



# EXTRAS (DELETED FOR NOW - Might be used later):
##
###RUN apt-get install -y libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev
###WORKDIR /usr/src
###RUN wget https://www.python.org/ftp/python/2.7.15/Python-2.7.15.tgz
###RUN tar xzf Python-2.7.15.tgz
##
###WORKDIR /usr/src/Python-2.7.15
###RUN ./configure --enable-optimizations
###RUN make altinstall
##
###CMD ["mkdir ANTs-code"]
###WORKDIR /usr/src/mrs-design-project/ANTs-code
###RUN git clone https://github.com/stnava/ANTs.git
###WORKDIR /usr/src/mrs-design-project
###RUN mkdir -p ~/bin/ants
###WORKDIR /usr/src/mrs-design-project/bin/ants
###RUN ccmake ~/ANTs-code/ANTs
### set SuperBuild_ANTS_USE_GIT_PROTOCOL=OFF
### git config --global url."https://".insteadOf git://