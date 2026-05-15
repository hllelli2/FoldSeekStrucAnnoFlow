# =============================================================================
# PeSTo – Protein Structure Transformer
# NVIDIA GPU-enabled Docker image
# https://github.com/LBM-EPFL/PeSTo
#
# Stack: Python 3.10 (native on Ubuntu 22.04) + PyTorch CUDA 11.8 + JupyterLab
# =============================================================================

FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

LABEL maintainer="PeSTo Docker Image"
LABEL description="PeSTo: Parameter-free Geometric Deep Learning for Protein Binding Interfaces (GPU)"
LABEL org.opencontainers.image.source="https://github.com/LBM-EPFL/PeSTo"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# ── System dependencies + Python 3.10 (native on Ubuntu 22.04) ────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        wget \
        curl \
        git \
        ca-certificates \
        libhdf5-dev \
        libssl-dev \
        python3 \
        python3-dev \
        python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── PyTorch (CUDA 11.8 wheel) + all PeSTo dependencies ────────────────────────
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

RUN pip3 install --no-cache-dir \
        torch torchvision torchaudio \
        --index-url https://download.pytorch.org/whl/cu118

RUN pip3 install --no-cache-dir \
        gemmi \
        numpy \
        scipy \
        pandas \
        matplotlib \
        scikit-learn \
        h5py \
        tqdm \
        tensorboard \
        mdtraj \
        jupyterlab \
        ipywidgets

# ── Clone PeSTo repository ────────────────────────────────────────────────────
WORKDIR /opt
RUN git clone https://github.com/LBM-EPFL/PeSTo.git

WORKDIR /opt/PeSTo

# ── Runtime environment variables ─────────────────────────────────────────────
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ── Volumes for PDB input/output data ─────────────────────────────────────────
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8888

# ── Default: launch JupyterLab ─────────────────────────────────────────────────
# Override for script use: docker run --gpus all pesto:gpu python profiling.py
CMD ["jupyter-lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--NotebookApp.token=''", \
     "--NotebookApp.password=''"]