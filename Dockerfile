FROM ubuntu:latest
MAINTAINER Joshua Brooks "josh.vdbroek@gmail.com"
ENV DEBIAN_FRONTEND=noninteractive

# Use docker host's apt-cache-ng server
RUN route -n | awk '/^0.0.0.0/ {print $2}' > /tmp/host_ip.txt; nc -zv `cat /tmp/host_ip.txt` 3142 &> /dev/null && if [ $? -eq 0 ]; then echo "Acquire::http::Proxy \"http://$(cat /tmp/host_ip.txt):3142\";" > /etc/apt/apt.conf.d/30proxy; echo "Proxy detected on docker host - using for this build"; fi

RUN 	apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y \
	python-pip python-dev libjpeg8 zlib1g libtiff5 libfreetype6 liblcms2-2 libwebp5 libtk8.6 \
	libjpeg8-dev zlib1g-dev libtiff5-dev libfreetype6-dev \
	libgeos-c1 libgeos-3.4.2 libgeos-dev && \
	apt-get clean

RUN	pip install -U pip \
 	mapnik gunicorn tilestache shapely \
    	Pillow modestmaps simplejson werkzeug

RUN apt-get install memcached
RUN pip install pylibmc
RUN pip install uwsgi

RUN sed -i 's/Image.fromstring/Image.frombytes/' /usr/local/lib/python2.7/dist-packages/TileStache/Mapnik.py
RUN sed -i 's/Image.fromstring/Image.frombytes/' /usr/local/lib/python2.7/dist-packages/TileStache/Pixels.py
RUN if [ -f "/etc/apt/apt.conf.d/30proxy" ]; then rm /etc/apt/apt.conf.d/30proxy; fi


RUN 	useradd -ms /bin/bash tilestache
USER	tilestache
WORKDIR /home/tilestache
RUN 	mkdir /home/tilestache/app
COPY 	app /home/tilestache/app/


EXPOSE 8080
CMD ["uwsgi", "/home/tilestache/app/uwsgi.ini"]

