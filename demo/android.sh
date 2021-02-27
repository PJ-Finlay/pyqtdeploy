# Android
# https://doc.qt.io/qt-5/android-getting-started.html
sudo apt-get install -y openjdk-8-jdk

# Gradle: https://gradle.org/install/
wget https://services.gradle.org/distributions/gradle-6.8.3-all.zip
sudo rm -rf /opt/gradle
sudo mkdir /opt/gradle
sudo chown $( whoami ) /opt/gradle
unzip -d /opt/gradle gradle-6.8.3-all.zip
ls /opt/gradle/gradle-6.8.3


