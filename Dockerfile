FROM python:3.11.4-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# define work directory
WORKDIR /app/
COPY . /app

# install pinned backend environments committed to the repository
RUN cd backend && ./setup-sigma-plugins.sh

# launch front- and backend
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
