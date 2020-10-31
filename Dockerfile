FROM gengkapak/mirrorbot:latest

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

RUN git clone https://github.com/AnggaR96s/python-aria-mirror-bot /usr/src/app

COPY extract /usr/local/bin
RUN chmod +x /usr/local/bin/extract

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
COPY credentials.json token.pickle config.env /usr/src/app/
COPY netrc /root/.netrc
RUN chmod +x aria.sh

CMD ["bash","start.sh"]
