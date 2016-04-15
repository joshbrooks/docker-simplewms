FROM digitaltl/mapnik
MAINTAINER Joshua Brooks "josh.vdbroek@gmail.com"

RUN 	useradd -ms /bin/bash simplewms
USER	simplewms
WORKDIR /home/simplewms
RUN 	mkdir /home/simplewms/app && mkdir /home/simplewms/data
COPY 	app /home/simplewms/app/
COPY 	data /home/simplewms/data/


EXPOSE 8080
CMD ["uwsgi", "/home/simplewms/app/uwsgi.ini"]

