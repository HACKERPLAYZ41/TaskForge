FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    locales \
    && rm -rf /var/lib/apt/lists/*
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
WORKDIR /workspace/repo
RUN git clone https://github.com/pallets/click.git . && \
    git checkout 934813e4d421071a1b3db3973c02fe2721359a6e
RUN pip install --no-cache-dir -e . pytest==8.3.4
