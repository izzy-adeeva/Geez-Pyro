FROM hitokizzy/ibel:slim-buster

RUN git clone -b main https://github.com/vckyou/Geez-Pyro /home/geez/
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    npm i -g npm
WORKDIR /home/geez

CMD ["python3","-m","geez"]
