FROM python:3.11.4-slim-buster

# set workdir
WORKDIR /code

# copy the flask app to the working directory
COPY ./ .

# install the dependencies
RUN apt update && apt install git -y

RUN pip install -r requirements.txt

# run the application
CMD [ "python", "./run.py" ]
