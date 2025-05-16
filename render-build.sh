#!/bin/bash
set -e

# Install necessary packages
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
  git clone https://<Space-Pikachu>:<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>@github.com/affymetrix/powertools.git && \
  cd powertools && \
  ./configure && \
  make -j2 && \
  make install

# Download and install APT binaries from GitHub
mkdir -p /tmp/bin
curl -L https://github.com/Space-Pikachu/cel-to-g25-backend/raw/main/binaries/apt-cel-convert -o /tmp/bin/apt-cel-convert
chmod +x /tmp/bin/apt-cel-convert

# Clone gtc2vcf
cd /tmp && \
  git clone --depth 1 https://github.com/freeseek/gtc2vcf.git /tmp/gtc2vcf

# Install gtc2vcf plugin for bcftools (without conda)
cd /tmp && \
  git clone --depth 1 https://github.com/freeseek/gtc2vcf.git && \
  mkdir -p ~/.bcftools/plugins && \
  cp /tmp/gtc2vcf/gtc2vcf.c ~/.bcftools/plugins/ && \
  bcftools plugin -lv
