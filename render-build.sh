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

# Download reference genome and index into writable temp directory
mkdir -p /tmp/reference

curl -L "https://download1324.mediafire.com/a5k1ijo792kgANBj6mpPm_aeTwskLeQr6ybzgeT0uW2wIsq0yCr5zMccSWY4kQDpnaTPFRCKUCAoelO9Oi4p8GkCQRQgsaUe3-Pm7ksHA3xLH_QFi7zSRkeM7WNuk0MQWolLUrkrMxZ8Zzs_2PG_aUCp10MGiIy-RhIwqbYxQeUOBw/l2nuwhg89bbtnwj/reference.fa" -o /tmp/reference/reference.fa

curl -L "https://download1085.mediafire.com/j6772ngye28g3mdPET0qqqhjQE4auRXWyoprvp6X3kPh3z9plyCU2YlfrLEaR8WHiZnsO7LmkCKtKScZM8YFa5LKtGf1aaRmr7UNmO4_xX-LHRh_uTmWFu7SRsQLrnR-PNtdT9lBr5zLeZF-t-8TlbttO_EGZ80OR23Rv5Lyk9gwlg/62mny5kk5qx7oju/reference.fa.fai" -o /tmp/reference/reference.fa.fai

# Confirm files downloaded
ls -lh /tmp/reference

# Skip apt-cel-convert setup at build time — handled at runtime by app.py
echo "[INFO] Skipping apt-cel-convert copy during build"

# Create Procfile at the project root to override default timeout
echo "web: gunicorn app:app --timeout 300 --bind 0.0.0.0:\$PORT" > /opt/render/project/src/Procfile
