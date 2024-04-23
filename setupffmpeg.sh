#!/bin/bash
git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git
cd nv-codec-headers &&  make install && cd –
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg/
apt-get install build-essential yasm cmake libtool libc6 libc6-dev unzip wget libnuma1 libnuma-dev -y
/app/nv-codec-headers/ffmpeg/configure --enable-nonfree --enable-cuda-nvcc --enable-libnpp --extra-cflags=-I/usr/local/cuda/include --extra-ldflags=-L/usr/local/cuda/lib64 --disable-static --enable-shared
make -j 8
make install
chmod +x ffmpeg

python3 /app/mount_slides.py
