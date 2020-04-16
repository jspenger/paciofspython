# Python3 image
FROM alpine:3.11 AS python-image
RUN apk update
RUN apk add python3 && apk add python3-dev
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# install python libraries
RUN  pip3 install --upgrade pip \
  && pip3 install --trusted-host pypi.python.org grpcio==1.26.0 \
  && pip3 install --trusted-host pypi.python.org etcd3==0.11.1 \
  && pip3 install --trusted-host pypi.python.org backoff==1.10.0 \
  && pip3 install --trusted-host pypi.python.org rpyc==4.1.2 \
  && pip3 install --trusted-host pypi.python.org fusepy==3.0.1 \
  && pip3 install --trusted-host pypi.python.org retrying==1.3.3 \
  && pip3 install --trusted-host pypi.python.org multichaincli==1.1.0 \
  && pip3 install --trusted-host pypi.python.org port-for==0.4

# MultiChain Image
FROM alpine:3.11 AS multichain-image
RUN apk update
# install MultiChain
RUN wget --quiet https://www.multichain.com/download/multichain-2.0.5.tar.gz \
  && tar -xvzf multichain-2.0.5.tar.gz \
  && /multichain-2.0.5/multichaind --version

# ETCD image
FROM alpine:3.11 AS etcd-image
RUN apk update && apk add curl
# install ETCD https://github.com/etcd-io/etcd/releases
RUN curl --silent -L https://storage.googleapis.com/etcd/v3.4.5/etcd-v3.4.5-linux-amd64.tar.gz -o /tmp/etcd-v3.4.5-linux-amd64.tar.gz \
  && mkdir tmp/etcd-download-test \
  && tar xzvf /tmp/etcd-v3.4.5-linux-amd64.tar.gz -C /tmp/etcd-download-test --strip-components=1 \
  && rm -f /tmp/etcd-v3.4.5-linux-amd64.tar.gz \
  && /tmp/etcd-download-test/etcd --version \
  && /tmp/etcd-download-test/etcdctl version

# final image
FROM alpine:3.11
# copy files from multistage builds
COPY --from=multichain-image /multichain-2.0.5/multichaind /usr/local/bin
COPY --from=multichain-image /multichain-2.0.5/multichain-cli /usr/local/bin
COPY --from=multichain-image /multichain-2.0.5/multichain-util /usr/local/bin
COPY --from=multichain-image /multichain-2.0.5/multichaind-cold /usr/local/bin
COPY --from=etcd-image /tmp/etcd-download-test/etcd /usr/local/bin
COPY --from=etcd-image /tmp/etcd-download-test/etcdctl /usr/local/bin
COPY --from=python-image /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# expose ports 3489 (clients) and 3490 (peers)
EXPOSE 3489
EXPOSE 3490
# update apk
RUN apk update && apk add libstdc++
# install git
RUN apk add git
# install python3
RUN apk add python3
# install FUSE
RUN apk add fuse
# install fio benchmark
RUN apk add fio
# pull latest version of app
RUN echo version 0.3.3
RUN git clone https://github.com/jonasspenger/paciofspython.git
RUN python3 paciofspython/paciofs/paciofslocal.py -h
RUN python3 paciofspython/paciofs/paciofsclient.py -h
RUN python3 paciofspython/paciofs/paciofsserver.py -h
