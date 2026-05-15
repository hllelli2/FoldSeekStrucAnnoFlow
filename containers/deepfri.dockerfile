# =============================================================================
# DeepFRI – Deep Functional Residue Identification
# NVIDIA GPU-enabled Docker image
# https://github.com/flatironinstitute/DeepFRI
#
# Uses Ubuntu 18.04 where Python 3.7 is a native apt package (no PPA needed).
# TensorFlow 2.4.1 + CUDA 11.0 + cuDNN 8.
# =============================================================================

FROM nvidia/cuda:11.0.3-cudnn8-runtime-ubuntu18.04

LABEL maintainer="DeepFRI Docker Image"
LABEL description="DeepFRI: Structure-Based Protein Function Prediction (GPU-enabled)"
LABEL org.opencontainers.image.source="https://github.com/flatironinstitute/DeepFRI"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# ── System dependencies + Python 3.7 (native on Ubuntu 18.04) ─────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        wget \
        curl \
        git \
        ca-certificates \
        libhdf5-dev \
        libatlas-base-dev \
        libssl-dev \
        python3.7 \
        python3.7-dev \
        python3.7-distutils \
    && update-alternatives --install /usr/bin/python  python  /usr/bin/python3.7 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1 \
    && curl -sS https://bootstrap.pypa.io/pip/3.7/get-pip.py | python3.7 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Python / TensorFlow GPU stack ─────────────────────────────────────────────
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

RUN pip install --no-cache-dir \
        "tensorflow-gpu==2.4.1" \
        "numpy>=1.19,<1.20" \
        "scipy>=1.5" \
        "scikit-learn>=0.24" \
        "biopython>=1.78" \
        "h5py>=2.10,<3.0" \
        "matplotlib>=3.3" \
        "networkx>=2.5" \
        "tqdm"

# ── Clone DeepFRI repository ──────────────────────────────────────────────────
WORKDIR /opt
RUN git clone https://github.com/flatironinstitute/DeepFRI.git

WORKDIR /opt/DeepFRI
RUN pip install --no-cache-dir -e .

# ── Pretrained GPU models (optional – uncomment to bake into the image) ───────
# WARNING: archive is several GB; mount as a volume instead during development.
#
# RUN mkdir -p /opt/DeepFRI/trained_models \
#     && wget -q -O /tmp/trained_models.tar.gz \
#        https://users.flatironinstitute.org/~renfrew/DeepFRI_data/trained_models.tar.gz \
#     && tar xvzf /tmp/trained_models.tar.gz -C /opt/DeepFRI \
#     && rm /tmp/trained_models.tar.gz

# ── Runtime environment variables ─────────────────────────────────────────────
ENV TF_FORCE_GPU_ALLOW_GROWTH=true
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ── Volumes for models and data ───────────────────────────────────────────────
RUN mkdir -p /data
VOLUME ["/data", "/opt/DeepFRI/trained_models"]

WORKDIR /opt/DeepFRI

# ── Entrypoint ────────────────────────────────────────────────────────────────
# Example:
#   docker run --gpus all \
#     -v $(pwd)/trained_models:/opt/DeepFRI/trained_models \
#     -v $(pwd)/data:/data deepfri \
#     --cmap /data/1S3P-A.npz -ont mf --verbose
ENTRYPOINT ["python", "predict.py"]
CMD ["--help"]