FROM python:3.11.4-slim-buster

# install dependencies
RUN apt-get update 
RUN apt-get install -y git curl jq
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# define work directory
WORKDIR /app/
COPY . /app

# install backend
RUN cd backend && ./setup-sigma-versions.sh

# launch front- and backend
# Expose frontend port
EXPOSE 8000
# Expose backend ports (for Sigma versions)
EXPOSE 8100-8199
ENTRYPOINT ["./entrypoint.sh"]
