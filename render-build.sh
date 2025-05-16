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

# Download and install bcftools
mkdir -p /tmp/bin
cd /tmp/bin
curl -L https://github.com/samtools/bcftools/releases/download/1.16/bcftools-1.16.tar.bz2 -o /tmp/bcftools.tar.bz2
cd /tmp
tar -xvjf bcftools.tar.bz2
cd bcftools-1.16 && make
cp bcftools /tmp/bin/bcftools

# Clone gtc2vcf and install plugin
rm -rf /tmp/gtc2vcf
git clone --depth 1 https://github.com/freeseek/gtc2vcf.git /tmp/gtc2vcf
mkdir -p ~/.bcftools/plugins
mkdir -p /tmp/bcftools-plugins
cp /tmp/gtc2vcf/gtc2vcf.c /tmp/bcftools-plugins/
export BCFTOOLS_PLUGINS=/tmp/bcftools-plugins
/tmp/bin/bcftools plugin -lv

# Install apt-cel-convert binary from your GitHub
curl -L https://github.com/Space-Pikachu/cel-to-g25-backend/raw/main/binaries/apt-cel-convert -o /tmp/bin/apt-cel-convert
chmod +x /tmp/bin/apt-cel-convert
