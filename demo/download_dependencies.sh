#!/bin/sh

# Based partially on this tutorial:
# https://medium.com/@Lola_Dam/packaging-pyqt-application-using-pyqtdeploy-for-both-linux-and-android-32ac7824708b

# Download PyQt, QScintilla, and PyQt-sip from riverbankcomputing.com

wget https://www.zlib.net/fossils/zlib-1.2.11.tar.gz
wget https://download.qt.io/official_releases/qt/5.15/5.15.0/single/qt-everywhere-src-5.15.0.tar.xz
wget https://www.python.org/ftp/python/3.7.8/Python-3.7.8.tar.xz
wget https://ftp.openssl.org/source/old/1.1.1/openssl-1.1.1g.tar.gz

for f in *.tar.gz; do tar xf "$f"; done
for f in *.tar.xz; do tar xf "$f"; done
rm *.tar.*

