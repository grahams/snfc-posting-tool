FROM python:3.14-slim
LABEL org.opencontainers.image.source="https://github.com/grahams/snfc-posting-tool"

# git + ssh are needed by the Hugo plugin (GitPython shells out to git)
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends git openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project
COPY requirements.txt .
# pip isn't needed at runtime and its vendored deps (urllib3, msgpack) trip scanners
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip
COPY . /project

# Set user and group
ARG user=appuser
ARG group=appuser
ARG uid=1000
ARG gid=1000
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -s /bin/sh -m ${user} # <--- the '-m' create a user home directory

# Switch to user
USER ${uid}:${gid}

CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
