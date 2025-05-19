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
rm -rf htslib && git clone --recurse-submodules https://github.com/samtools/htslib.git
cd htslib
make -j$(nproc)
export HTSLIB_PATH=/tmp/htslib

# Download and build bcftools from GitHub (for internal headers like bcftools.h)
cd /tmp
rm -rf bcftools
git clone --recurse-submodules https://github.com/samtools/bcftools.git
cd bcftools && make
mkdir -p /tmp/bin
cp bcftools /tmp/bin/bcftools
export BCFTOOLS_SRC=/tmp/bcftools

# Compile gtc2vcf plugin using bcftools headers
rm -rf /tmp/gtc2vcf
git clone --depth 1 https://github.com/freeseek/gtc2vcf.git /tmp/gtc2vcf
mkdir -p /tmp/bcftools-plugins

# Compile gtc2vcf plugin with correct headers
gcc -O2 -Wall -shared -fPIC \
  -I$HTSLIB_PATH \
  -I$BCFTOOLS_SRC \
  -L$HTSLIB_PATH \
  -lhts \
  -o /tmp/bcftools-plugins/gtc2vcf.so \
  /tmp/gtc2vcf/gtc2vcf.c

# Export plugin path (this is needed for bcftools plugin to work)
export BCFTOOLS_PLUGINS=/tmp/bcftools-plugins

# Optional debug: check if .so is readable
ls -lh /tmp/bcftools-plugins/

# Clone repo containing binary
git clone https://github.com/Space-Pikachu/cel-to-g25-backend.git /tmp/cel-to-g25-backend

# Copy apt-cel-convert from repo to tmp/bin
mkdir -p /tmp/bin
cp /tmp/cel-to-g25-backend/binaries/apt-cel-convert /tmp/bin/apt-cel-convert
chmod +x /tmp/bin/apt-cel-convert
