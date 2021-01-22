FROM python:3
ENV TZ=America/Los_Angeles
RUN apt-get -y update && apt-get -y install telnet build-essential neovim avahi-utils avahi-daemon avahi-discover libnss-mdns libavahi-compat-libdnssd-dev  npm
ADD avahi-daemon.conf /etc/avahi/avahi-daemon.conf
ADD nsswitch.conf /etc/nsswitch.conf
RUN pip3 install pyatv pymongo pillow paho-mqtt
RUN npm install -g pm2 forever nodemon
RUN useradd --user-group --create-home --shell /bin/false app
ENV HOME=/home/app
WORKDIR /home/app
COPY . /home/app
CMD ["./loop.sh"]


