FROM gliderlabs/alpine:latest
MAINTAINER matt maier <mgmaier@gmail.com>

RUN apk-install collectd collectd-network py-pip py-yaml
RUN pip install docker-py

RUN mkdir /opt
RUN mkdir /opt/collectd
RUN mkdir /opt/collectd/csv

COPY cadvisor-client /opt/collectd/
RUN chown nobody /opt/collectd/cadvisor-client
RUN chmod +x /opt/collectd/cadvisor-client

COPY cadvisor-types.db /opt/collectd/

COPY collectd-launch.sh /
RUN chmod +x /collectd-launch.sh

VOLUME "/etc/collectd"

CMD ["/collectd-launch.sh"]
