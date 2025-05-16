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
  autoconf \
  libncurses5-dev

# Set up working directories
mkdir -p /tmp/bin
cd /tmp

#######################
# Install HTSlib from source
#######################
git clone --depth 1 https://github.com/samtools/htslib.git
cd htslib
make
make install PREFIX=/tmp/hts
cd ..

#######################
# Install bcftools from source using HTSlib above
#######################
git clone --depth 1 https://github.com/samtools/bcftools.git
cd bcftools
make HTSDIR=/tmp/hts
make install prefix=/tmp/bcftools
cd ..

# Add bcftools to path
export PATH="/tmp/bcftools/bin:$PATH"

#######################
# Clone and build gtc2vcf plugin
#######################
git clone --depth 1 https://github.com/freeseek/gtc2vcf.git /tmp/gtc2vcf
mkdir -p /tmp/bcftools-plugins
cp /tmp/gtc2vcf/gtc2vcf.c /tmp/bcftools-plugins/
export BCFTOOLS_PLUGINS=/tmp/bcftools-plugins

# Compile plugin against HTSlib
gcc -g -Wall -O2 -I/tmp/hts -fPIC -shared /tmp/bcftools-plugins/gtc2vcf.c -o /tmp/bcftools-plugins/gtc2vcf.so

# Test if bcftools recognizes plugin
/tmp/bcftools/bin/bcftools plugin -lv

#######################
# Install apt-cel-convert binary
#######################
curl -L https://github.com/Space-Pikachu/cel-to-g25-backend/raw/main/binaries/apt-cel-convert -o /tmp/bin/apt-cel-convert
chmod +x /tmp/bin/apt-cel-convert
