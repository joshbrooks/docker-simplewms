FROM digitaltl/tilestache:latest

RUN  apt-get update \
  && apt-get install -y python-pip \
  && apt-get install -y build-essential python-dev \
  && apt-get clean

RUN pip install uwsgi
RUN pip install Pillow
RUN mkdir /webapp
WORKDIR /webapp
COPY /webapp/* /webapp/

EXPOSE 80

CMD ["uwsgi", "--http", ":80", "--wsgi-file", "app.py"]
