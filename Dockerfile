FROM gliderlabs/alpine:latest
MAINTAINER matt maier <mgmaier@gmail.com>

COPY src/apk-installer /
RUN chmod +x /apk-installer

RUN /apk-installer collectd collectd-python collectd-network py-pip py-yaml
RUN pip install docker-py

RUN mkdir -p /opt/collectd/csv
RUN mkdir /opt/collectd/python
RUN touch /opt/collectd/python/__init__.py

COPY src/cadvisor/cadvisor-cli /opt/collectd/
COPY src/cadvisor/python/cadvisor.py /opt/collectd/python/
COPY src/cadvisor/python/cadvisor-metrics.py /opt/collectd/python/
COPY src/cadvisor/cadvisor-types.db /opt/collectd/

COPY src/mesos/mesos-cli /opt/collectd/
COPY src/mesos/python/mesos.py /opt/collectd/python/
COPY src/mesos/python/mesos_collectd.py /opt/collectd/python/
COPY src/mesos/python/mesos-master.py /opt/collectd/python/
COPY src/mesos/python/mesos-slave.py /opt/collectd/python/
COPY src/mesos/mesos-types.db /opt/collectd/

COPY collectd-launch.sh /

RUN chown nobody /opt/collectd/cadvisor-cli
RUN chmod +x /opt/collectd/cadvisor-cli

RUN chown nobody /opt/collectd/mesos-cli
RUN chmod +x /opt/collectd/mesos-cli

RUN chmod +x /collectd-launch.sh

VOLUME /etc/collectd

CMD ["/collectd-launch.sh"]
