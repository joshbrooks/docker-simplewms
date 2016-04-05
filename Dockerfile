FROM ubuntu:latest
MAINTAINER Joshua Brooks "josh.vdbroek@gmail.com"
ENV DEBIAN_FRONTEND=noninteractive
RUN route -n | awk '/^0.0.0.0/ {print $2}' > /tmp/host_ip.txt; nc -zv `cat /tmp/host_ip.txt` 3142 &> /dev/null && if [ $? -eq 0 ]; then echo "Acquire::http::Proxy \"http://$(cat /tmp/host_ip.txt):3142\";" > /etc/apt/apt.conf.d/30proxy; echo "Proxy detected on docker host - using for this build"; fi
RUN  apt-get update && apt-get install -y python-pip build-essential python-dev libmemcached-dev && apt-get clean
RUN pip install mapnik uwsgi Pillow pylibmc
RUN if [ -f "/etc/apt/apt.conf.d/30proxy" ]; then rm /etc/apt/apt.conf.d/30proxy; fi
RUN useradd -ms /bin/bash simplewms
USER simplewms
WORKDIR /home/simplewms
RUN mkdir /home/simplewms/app
COPY app /home/simplewms/app/
EXPOSE 80
CMD ["uwsgi", "/home/simplewms/app/uwsgi.ini"]

