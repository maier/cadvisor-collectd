#!/bin/sh
# note - alpine default shell is sh

set -eux

: ${DEST:=""}

mkdir -p ${DEST}/opt/collectd/csv
mkdir -p ${DEST}/opt/collectd/python
touch ${DEST}/opt/collectd/python/__init__.py

cp cadvisor/cadvisor-cli ${DEST}/opt/collectd/
chown nobody ${DEST}/opt/collectd/cadvisor-cli
chmod +x ${DEST}/opt/collectd/cadvisor-cli
cp cadvisor/python/cadvisor.py ${DEST}/opt/collectd/python/
cp cadvisor/python/cadvisor-metrics.py ${DEST}/opt/collectd/python/
cp cadvisor/cadvisor-types.db ${DEST}/opt/collectd/

cp mesos/mesos-cli ${DEST}/opt/collectd/
chown nobody ${DEST}/opt/collectd/mesos-cli
chmod +x ${DEST}/opt/collectd/mesos-cli
cp mesos/python/mesos.py ${DEST}/opt/collectd/python/
cp mesos/python/mesos_collectd.py ${DEST}/opt/collectd/python/
cp mesos/python/mesos-master.py ${DEST}/opt/collectd/python/
cp mesos/python/mesos-slave.py ${DEST}/opt/collectd/python/
cp mesos/mesos-types.db ${DEST}/opt/collectd/

# END
