FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    nodejs npm \
    curl wget git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Keep the container alive; the manager runs commands into it with `docker exec`.
CMD ["sleep", "infinity"]
