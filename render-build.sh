#!/bin/bash
set -e

# Install dependencies
apt-get update && apt-get install -y \
  build-essential \
  zlib1g-dev \
  wget \
  unzip \
  python3-pip \
  git \
  cmake \
  libcurl4-openssl-dev \
  libssl-dev \
  libbz2-dev \
  curl

# Install Miniconda to /tmp
cd /tmp
curl -L -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash miniconda.sh -b -p /tmp/conda
export PATH="/tmp/conda/bin:$PATH"

# Install bcftools via conda
conda install -y -c bioconda bcftools

# Clone gtc2vcf and install plugin
rm -rf /tmp/gtc2vcf
git clone --depth 1 https://github.com/freeseek/gtc2vcf.git /tmp/gtc2vcf
mkdir -p ~/.bcftools/plugins
cp /tmp/gtc2vcf/gtc2vcf.c ~/.bcftools/plugins/
bcftools plugin -lv

# Install apt-cel-convert binary from your GitHub
mkdir -p /tmp/bin
curl -L https://github.com/Space-Pikachu/cel-to-g25-backend/raw/main/binaries/apt-cel-convert -o /tmp/bin/apt-cel-convert
chmod +x /tmp/bin/apt-cel-convert
