# cadvisor-collectd

Collecting host and container metrics using [CAdvisor](https://registry.hub.docker.com/u/google/cadvisor/) and [Collectd](https://github.com/collectd/collectd/).

Status: [docker registry](https://registry.hub.docker.com/u/maier/cadvisor-collectd/)


# Problem

* Collect metrics from host system, running containers, and processes exposing metrics running in containers.
* Send metrics to multiple external (from host) systems simultaneously.
* Run in a container, not on the host system.


# Solution

### Collectd and CAdvisor

1. Low adoption friction -- Collectd is already in-place as the solution for metrics collection and transport [where I work].
1. Flexibility, Collectd
   * Offers large number of plugins to support collection of metrics.
   * Various options for creating custom metrics collectors.
   * Offers a large number of plugins to send metrics to various external systems.
   * Collectd's native transport is supported by many such systems.
1. CAdvisor
   * Collectd has no inherent capability to inspect the host system [from a container] nor other containers.
   * Exposes host system and container metrics via an API which can be easily leveraged.
   * Offers near real-time visibility into a running system, if exposed, providing a powerful interactive troubleshooting tool.


### Drawbacks

1. It is a more complex solution, with complexity comes fragility.
1. CAdvisor adds additional load to a system.

As alternatives surface they will be investigated from the perspective of simplifying the overall solution and reducing load on the host system.

# Features

* Leverage Collectd's wealth of plugins
* Leveage CAdvisor's ability to see the *Host* as well as the *Containers*
* Runs in a separate container (not as a 1st class process on the Host)
* Has built-in metrics collectors for:
   * Host
   * Containers
   * Mesos
* Easy to use...which is, of course, relative and subjective :)
* Basic metric name manipulation for metric continuity

# Getting started

Refer to the repository wiki for [complete documentation](https://github.com/maier/cadvisor-collectd/wiki) on all of the configuration options, as well as, more details on using the cadvisor-collectd container.

## Quick starts

First, clone the repository, copy the etc-collectd directory to the target host, and ssh to the host.

```
git clone https://github.com/maier/cadvisor-collectd.git
scp -r etc-collectd <target_host>:.
ssh <target_host>
```

If the target host has internet access, clone the repository directly on the host.

```
ssh <target_host>
git clone https://github.com/maier/cadvisor-collectd.git
cd cadvisor-collectd
```

### Write to csv files

```
# Configure:
sed "s/example.local/$(hostname)/" etc-collectd/collectd.conf.example > etc-collectd/collectd.conf
cp etc-collectd/cadvisor.yaml.example etc-collectd/cadvisor.yaml
cp etc-collectd/conf.d/cadvisor-plugin.conf.example etc-collectd/conf.d/cadvisor.conf
cp etc-collectd/conf.d/write_csv.conf.example etc-collectd/conf.d/write_csv.conf

# Start cadvisor and cadvisor-collectd containers:
sudo docker run --name=cadvisor -v /:/rootfs:ro -v /var/run:/var/run:rw \
  -v /sys:/sys:ro -v /var/lib/docker/:/var/lib/docker:ro -d google/cadvisor:latest
sudo docker run --name=collectd -v $(pwd)/etc-collectd:/etc/collectd \
  -v /var/run/docker.sock:/var/run/docker.sock -d maier/cadvisor-collectd:latest

# Explore the metrics
docker exec -ti collectd /bin/sh
cd /opt/collectd/csv
```

### Write to a local InfluxDB container

Or, replace the docker inspect with the IP of a non-local InfluxDB instance. Ensure the collectd input plugin is active in config.toml.

```
# Configure:
sed "s/example.local/$(hostname)/" etc-collectd/collectd.conf.example > etc-collectd/collectd.conf
cp etc-collectd/cadvisor.yaml.example etc-collectd/cadvisor.yaml
cp etc-collectd/conf.d/cadvisor-plugin.conf.example etc-collectd/conf.d/cadvisor.conf
sed "s/FQDN\|IP/$(docker inspect -f '{{.NetworkSettings.IPAddress}}' influxdb)/" \
  etc-collectd/conf.d/write_network.conf.example > etc-collectd/conf.d/write_network.conf

# Start cadvisor and cadvisor-collectd containers:
sudo docker run --name=cadvisor -v /:/rootfs:ro -v /var/run:/var/run:rw \
  -v /sys:/sys:ro -v /var/lib/docker/:/var/lib/docker:ro -d google/cadvisor:latest
sudo docker run --name=collectd -v $(pwd)/etc-collectd:/etc/collectd \
  -v /var/run/docker.sock:/var/run/docker.sock -d maier/cadvisor-collectd:latest
```

### Write to a local Graphite container

Or, replace the docker inspect with the IP of a non-local Graphite instance. Update the port setting in the write_graphite.conf file if Carbon is not listening on the default 2003.

```
Configure:
sed "s/example.local/$(hostname)/" etc-collectd/collectd.conf.example > etc-collectd/collectd.conf
cp etc-collectd/cadvisor.yaml.example etc-collectd/cadvisor.yaml
cp etc-collectd/conf.d/cadvisor-plugin.conf.example etc-collectd/conf.d/cadvisor.conf
sed "s/FQDN\|IP/$(docker inspect -f '{{.NetworkSettings.IPAddress}}' graphite)/" \
  etc-collectd/conf.d/write_graphite.conf.example > etc-collectd/conf.d/write_graphite.conf

# Start cadvisor and cadvisor-collectd containers:
sudo docker run --name=cadvisor -v /:/rootfs:ro -v /var/run:/var/run:rw \
  -v /sys:/sys:ro -v /var/lib/docker/:/var/lib/docker:ro -d google/cadvisor:latest
sudo docker run --name=collectd -v $(pwd)/etc-collectd:/etc/collectd \
  -v /var/run/docker.sock:/var/run/docker.sock -d maier/cadvisor-collectd:latest

```

## On deck

- [x] add mesos metrics collection plugin for Collectd
- [x] refactor cadvisor and mesos -- provide both command line and plugin capabilities
- [x] add service filter modes to cadvisor
    - [x] group options
        - [x] mounts
        - [x] sockets
        - [x] docker scopes
        - [x] user slice
        - [x] system slice
        - [x] other slices
    - [x] service options
        - [x] all
        - [x] include -- implicit exclusion, explicit inclusion
        - [x] exclude -- implicit inclusion, explicit exclusion
- [x] rewirte and reorganize documentation
    - [x] introduction
    - [x] configuring collectd
    - [x] configuring cadvisor plugin
    - [x] configuring mesos plugin
    - [x] add quick start to README
        - [x] csv
        - [x] graphite
        - [x] influxdb
- [ ] ansible playbook
    - [ ] cadvisor service
    - [ ] cadvisor-collectd service
    - [ ] configure collectd
    - [ ] configure cadvisor plugin
    - [ ] configure mesos plugin
- [ ] options for metric source (for docker containers)
    - [ ] Docker
    - [ ] CAdvisor
- [ ] configuration sources
    - [ ] consul
    - [ ] etcd
        - [ ] confd
