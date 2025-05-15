#!/bin/bash
set -e

apt-get update && \
  apt-get install -y \
  build-essential \
  zlib1g-dev \
  wget \
  unzip \
  python3-pip \
  bcftools \
  git \
  cmake \
  libcurl4-openssl-dev \
  libssl-dev \
  libbz2-dev

# Install APT Tools
cd /tmp && \
  git clone https://github.com/affymetrix/powertools.git && \
  cd powertools && \
  ./configure && \
  make -j2 && \
  make install

# Clone gtc2vcf
cd /opt && \
  git clone https://github.com/freeseek/gtc2vcf.git

# Add gtc2vcf as bcftools plugin
mkdir -p ~/.bcftools/plugins && \
  cp /opt/gtc2vcf/gtc2vcf.c ~/.bcftools/plugins/ && \
  bcftools plugin -lv
