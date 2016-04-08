FROM digitaltl/mapnik
MAINTAINER Joshua Brooks "josh.vdbroek@gmail.com"

RUN 	useradd -ms /bin/bash simplewms
USER	simplewms
WORKDIR /home/simplewms
RUN 	mkdir /home/simplewms/app
COPY 	app /home/simplewms/app/


EXPOSE 8080
CMD ["uwsgi", "/home/simplewms/app/uwsgi.ini"]

