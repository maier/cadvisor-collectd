FROM gliderlabs/alpine:latest
MAINTAINER matt maier <mamaier@cisco.com>

RUN apk-install collectd collectd-network py-pip py-yaml
RUN pip install docker-py

RUN mkdir -p /etc/collectd
RUN mkdir -p /opt/collectd && chmod 0755 /opt/collectd
RUN mkdir -p /opt/colletc/csv

COPY cadvisor-client /opt/collectd
RUN chown nobody /opt/collectd/cadvsior-client && chmod 0700 /opt/collectd/cadvisor-client

COPY cadvisor-types.db /opt/collectd

COPY collectd-launch.sh /
RUN chmod +x /collectd-launch.sh

VOLUME "/etc/collectd"

CMD ["/collectd-launch.sh"]
