FROM python:3.11-slim AS builder

WORKDIR /tmp

ARG TARGETARCH

COPY binaries/ /tmp/binaries/

RUN cp /tmp/binaries/ffmpeg6-${TARGETARCH} /usr/local/bin/ffmpeg6 && \
    cp /tmp/binaries/dovi_tool-${TARGETARCH} /usr/local/bin/dovi_tool && \
    chmod +x /usr/local/bin/ffmpeg6 /usr/local/bin/dovi_tool

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