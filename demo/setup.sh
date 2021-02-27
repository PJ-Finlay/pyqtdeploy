#!/bin/sh

# Not really sure what is needed just installing all packages from two tutorials
# pyqtdeploy needs to also be installed:
# cd ..
# pip3 install -e .

sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get install -y python3 python3-pip python-is-python3

# Add python scripts to path
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.profile
export PATH="$HOME/.local/bin:$PATH"

# From https://gist.github.com/suizokukan/8abb8437561048c63080575b54dce70a
sudo apt-get -y install python
sudo apt-get -y install libssl1.0-dev
sudo apt-get -y install libudev-dev
sudo apt-get -y install libx11-xcb-dev
sudo apt-get -y install libjpeg-dev
sudo apt-get -y install libts-dev
sudo apt-get -y install libvulkan-dev
sudo apt-get -y install libcups2-dev
sudo apt-get -y install libmysqlclient-dev libdrm-dev libharfbuzz-dev libsqlite-dev

sudo apt-get -y install cmake libx11-dev xorg-dev libglu1-mesa-dev freeglut3-dev libglew1.5 libglew1.5-dev libglu1-mesa libglu1-mesa-dev libgl1-mesa-glx libgl1-mesa-dev

sudo apt-get -y dist-upgrade
sudo apt-get -y install build-essential python-dev python-setuptools python-pip python-smbus
sudo apt-get -y install libncursesw5-dev libgdbm-dev libc6-dev
sudo apt-get -y install zlib1g-dev libsqlite3-dev tk-dev
sudo apt-get -y install libssl-dev openssl
sudo apt-get -y install libffi-dev

# From https://stackoverflow.com/questions/65059086/project-error-unknown-modules-in-qt-x11extras

sudo apt-get install -y libfreetype6-dev libfontconfig1-dev libglib2.0-dev \
            libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libice-dev \
            libaudio-dev libgl1-mesa-dev libc6-dev libsm-dev libxcursor-dev \
            libxext-dev libxfixes-dev libxi-dev libxinerama-dev \
                    libxrandr-dev libxrender-dev libxkbcommon-dev \
            libxkbcommon-x11-dev libx11-dev

sudo apt-get install -y libxcb1-dev libx11-xcb-dev libxcb-glx0-dev \
            libxcb-icccm4-dev libxcb-image0-dev libxcb-keysyms1-dev \
            libxcb-render0-dev libxcb-render-util0-dev \
            libxcb-randr0-dev libxcb-shape0-dev libxcb-shm0-dev \
            libxcb-sync-dev libxcb-xfixes0-dev \
            libxcb-xinerama0-dev libxcb-xkb-dev

sudo apt-get install -y g++ gperf ninja-build cmake
sudo apt-get install -y libpulse-dev libasound2-dev libssl-dev libcups2-dev \
            libxml++2.6-dev postgresql-server-dev-12

sudo apt-get install -y git

# Install Qt
sudo apt-get install -y qt5-default
sudo apt-get install -y python3-pyqt5.qtx11extras


# Install Python packages
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

