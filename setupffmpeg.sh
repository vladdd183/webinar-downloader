#!/bin/bash
git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git  /usr/lib/nv-codec-headers
cd /usr/lib/nv-codec-headers &&  make install
git clone https://git.ffmpeg.org/ffmpeg.git /usr/lib/ffmpeg/
apt-get install build-essential yasm cmake libtool libc6 libc6-dev unzip wget libnuma1 libnuma-dev libffmpeg-nvenc-dev x264 x265 libx264-dev pkg-config -y
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig"
cd /usr/lib/ffmpeg
./configure --enable-gpl --enable-libx264  --extra-libs="-lpthread" --pkg-config-flags="--static" && make -j 8 && make install 
ffmpeg
python3 /app/mount_slides.py
