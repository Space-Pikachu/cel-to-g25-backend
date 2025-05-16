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
  curl \
  libhts-dev \
  autoconf \
  automake \
  libtool \
  bzip2

# Download and build HTSlib
cd /tmp
rm -rf htslib && git clone https://github.com/samtools/htslib.git
cd htslib && git submodule update --init --recursive
make -j$(nproc)
export HTSLIB_PATH=/tmp/htslib

# Download and install bcftools
cd /tmp
curl -L https://github.com/samtools/bcftools/releases/download/1.16/bcftools-1.16.tar.bz2 -o bcftools.tar.bz2
mkdir -p /tmp/bcftools-src
cd /tmp/bcftools-src
bunzip2 -c ../bcftools.tar.bz2 | tar -xvf -
cd bcftools-1.16 && make
mkdir -p /tmp/bin
cp bcftools /tmp/bin/bcftools

# Compile gtc2vcf plugin with HTSlib headers
rm -rf /tmp/gtc2vcf
git clone --depth 1 https://github.com/freeseek/gtc2vcf.git /tmp/gtc2vcf
mkdir -p /tmp/bcftools-plugins

gcc -O2 -Wall -shared -fPIC \
  -I$HTSLIB_PATH \
  -L$HTSLIB_PATH \
  -lhts \
  -o /tmp/bcftools-plugins/gtc2vcf.so \
  /tmp/gtc2vcf/gtc2vcf.c

export BCFTOOLS_PLUGINS=/tmp/bcftools-plugins
/tmp/bin/bcftools plugin -lv

# Install apt-cel-convert binary from your GitHub
curl -L https://github.com/Space-Pikachu/cel-to-g25-backend/raw/main/binaries/apt-cel-convert -o /tmp/bin/apt-cel-convert
chmod +x /tmp/bin/apt-cel-convert
