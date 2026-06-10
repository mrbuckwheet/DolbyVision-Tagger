FROM python:3.11-slim AS builder

WORKDIR /tmp

RUN apt-get update && apt-get install -y \
    curl \
    xz-utils \
    tar \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz \
    && mkdir ffmpeg_extracted \
    && tar -xf ffmpeg.tar.xz -C ffmpeg_extracted --strip-components=1 \
    && mv ffmpeg_extracted/ffmpeg /usr/local/bin/ffmpeg6 \
    && chmod +x /usr/local/bin/ffmpeg6

RUN curl -L https://github.com/quietvoid/dovi_tool/releases/download/2.3.2/dovi_tool-2.3.2-x86_64-unknown-linux-musl.tar.gz -o dovi_tool.tar.gz \
    && tar -xf dovi_tool.tar.gz \
    && mv dovi_tool /usr/local/bin/dovi_tool \
    && chmod +x /usr/local/bin/dovi_tool

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/bin/ffmpeg6 /usr/local/bin/ffmpeg6
COPY --from=builder /usr/local/bin/dovi_tool /usr/local/bin/dovi_tool

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir plexapi flask

COPY mrbuckwheets_dv_tagger.py /app/
COPY entrypoint.sh /app/
COPY app.py /app/

RUN chmod +x /app/entrypoint.sh

EXPOSE 3636

ENTRYPOINT ["/app/entrypoint.sh"]
