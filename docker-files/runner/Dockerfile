FROM arm32v7/ubuntu:16.04

LABEL maintainer "Srinivasan Sekar <srinivasan.sekar1990@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qqy update && \
    apt-get -qqy --no-install-recommends install \
    openjdk-8-jdk \
    ca-certificates \
    tzdata \
    unzip \
    curl \
    wget \
    libqt5webkit5 \
    libgconf-2-4 \
    xvfb


# install appium
ARG APPIUM_VERSION=1.7.2
ENV APPIUM_VERSION=$APPIUM_VERSION

RUN curl -sL https://deb.nodesource.com/setup_7.x | bash - && \
    apt-get -qqy install nodejs && \
    npm install -g appium@${APPIUM_VERSION}


# install android tools
RUN apt-get install -y --no-install-recommends android-tools-adb android-tools-fastboot


# install python
RUN apt-get install -y --no-install-recommends python3 python3-pip


EXPOSE 4723
COPY \
    Appium/entry_point.sh \
    Appium/generate_config.sh \
    /root/
RUN chmod +x /root/entry_point.sh
RUN chmod +x /root/generate_config.sh


RUN npm cache clean && \
    apt-get remove --purge -y npm && \
    apt-get autoremove --purge -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    apt-get clean

CMD ["/root/entry_point.sh"]
