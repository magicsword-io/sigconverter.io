FROM python:3.11.4-slim-buster

# set workdir
WORKDIR /code

# copy the flask app to the working directory
COPY ./ .

# install the dependencies
RUN apt update && apt install git -y

RUN pip install poetry && poetry install

# run the application
EXPOSE 8000
CMD [ "poetry", "run", "./run.py" ]
