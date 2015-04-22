FROM gliderlabs/alpine:latest
MAINTAINER matt maier <mgmaier@gmail.com>

RUN apk-install collectd collectd-python collectd-network py-pip py-yaml
RUN pip install docker-py

RUN mkdir /opt
RUN mkdir /opt/collectd
RUN mkdir /opt/collectd/csv
RUN mkdir /opt/collectd/python
RUN touch /opt/collectd/python/__init__.py

COPY cadvisor/cadvisor-cli /opt/collectd/
RUN chown nobody /opt/collectd/cadvisor-cli
RUN chmod +x /opt/collectd/cadvisor-cli
COPY cadvisor/python/cadvisor.py /opt/collectd/python/
COPY cadvisor/python/cadvisor-metrics.py /opt/collectd/python/
COPY cadvisor-types.db /opt/collectd/

COPY mesos/mesos-cli /opt/collectd/
RUN chown nobody /opt/collectd/mesos-cli
RUN chmod +x /opt/collectd/mesos-cli
COPY mesos/mesos.py /opt/collectd/python/
COPY mesos/mesos_collectd.py /opt/collectd/python/
COPY mesos/mesos-master.py /opt/collectd/python/
COPY mesos/mesos-slave.py /opt/collectd/python/
COPY mesos-types.db /opt/collectd/

COPY collectd-launch.sh /
RUN chmod +x /collectd-launch.sh

VOLUME /etc/collectd

CMD ["/collectd-launch.sh"]
