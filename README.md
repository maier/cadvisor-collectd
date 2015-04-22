# cadvisor-collectd

Collecting host and container metrics using [CAdvisor](https://registry.hub.docker.com/u/google/cadvisor/) and [Collectd](https://github.com/collectd/collectd/).

Status: [docker registry](https://registry.hub.docker.com/u/maier/cadvisor-collectd/)

## Problem

* Collect metrics from host system, running containers, and processes exposing metrics running in containers.
* Send metrics to multiple external (from host) systems simultaneously.
* Run in a container, not on the host system.

## Solution: Collectd and CAdvisor

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


# Usage

Since Collectd configurations are dynamic and target specific, a mounted volume is used initially. This requirement will be eliminated as configuration support via [etcd](https://coreos.com/using-coreos/etcd/) and [consul](https://www.consul.io/) is added. For now the configurations are distributed through current orchestration methods (ansible, puppet, chef, salt, etc.).

1. Deploy `etc-collectd` to target host and configure.
1. Start containers. Manual and systemd instructions below configuration section.

## Configuration

### Collectd

The main Collectd configuration `etc-collectd/collectd.conf.example`.

**Hostname** or **FQDNLookup** must be set prior to starting Collectd.

1. `cd etc-colletd`
1. `cp collectd.conf.example collectd.conf`
1. Edit resulting `collectd.conf` accordingly:
   1. Static IP and valid forward and reverse DNS for the hostname to be used.
      1. Comment **Hostname** `#Hostname`
      1. Ensure **FQDNLookup** set to **true** `FQDNLookup true`
   1. Dynamic IP and ephemeral hostname to be used.
	   1. Update **Hostanme** `Hostname "test.local"`
	   1. Ensure **FQDNLookup** set to **false** `FQDNLookup false`

### Collectd writer

At least one Collectd *writer* plugin, in `etc-collectd/conf.d`, must be enabled for Collectd to run correctly.

1. Copy one, or more, of the example (network, write_graphite, write_http, csv) configurations to file(s) with a `.conf` extension.
1. Edit the resulting configuration file.
1. Note, configurations are not dynamically loaded by Collectd. If the Collectd container is already running, a restart will be required to pick up configuration changes and the addition of new configuration files.

#### Collectd Graphite writer

InfluxDB also has a Graphite plugin which can be used by this configuration.

1. Determine fqdn or ip of the destination (graphite or influxdb) host.
1. Determine destination protocol and port (e.g. tcp 2003).
1. `cd etc-collectd/conf.d && cp write_graphite.conf.example write_graphite.conf`
1. Edit `write_graphite.conf`
1. Update applicable settings for target. *Host*, *Port*, and *Protocol* at a minimum.

#### Collectd Network writer

InfluxDB also has a native Collectd plugin which can be used by this configuration.

1. Determine fqdn or ip of the destination (graphite or influxdb) host.
1. Determine destination port (e.g. collectd's default is 25826).
1. `cd etc-collectd/conf.d && cp network.conf.example network.conf`
1. Edit `network.conf`
1. Update *Server* setting (one-line or block form) and any others applicable to target. Note format for *Server* is `Server "IP||FQDN" "port"`.

#### Collectd HTTP writer

1. Determine destination URL.
1. `cd etc-collectd/conf.d && cp write_http.conf.example write_http.conf`
1. Edit `write_http.conf`
1. Update applicable setting(s), *URL* at a minimum.

#### Collectd CSV writer

1. `cd etc-collectd/conf.d && cp csv.conf.example csv.conf`
1. Edit `csv.conf`
1. Update *DataDir*, default is `/opt/collectd/csv`. Update to write to a mounted volume if the data is needed outside of the container. (export, easier access for testing, etc.)

### Collectd CAdvisor plugin

This configures the script which gathers metrics from CAdvisor and emits them to Collectd. The documentation and descriptions of the settings are contained within the YAML file. The CAdvisor script is intentionally an *Exec* plugin script. Electing this method versus a direct *Python* plugin module makes verifying configurations and debugging more straight-forward.

1. `cd etc-collectd && cp cadvisor.yaml.example cadvisor.yaml`
2. Edit `cadvisor.yaml`
3. Read descriptions and update settings accordingly.

### Mesos

Enabling and configuring the [Mesos](http://mesos.apache.org/) plugin(s) is pretty straight-forward and many settings are defaulted to acceptable values.

#### Mesos metrics configuration

Controls the mesos to collectd metric type translations. Provides facility to ignore specific mesos metrics (information, redundant, etc.).

1. `cd etc-collectd && cp mesos.yaml.example mesos.yaml`
2. Edit `mesos.yaml`
3. Read descriptions and update settings accordingly.

#### Mesos plugin configuration

1. `cd etc-collectd/conf.d && cp mesos.conf.example mesos.conf`
1. Edit `mesos.conf`
1. Uncomment the master, slave, or both section(s).
1. Update settings accordingly.
   * `Host` - IP of target mesos host
      * IP (e.g. 127.0.0.1)
      * `docker:gateway` to use the value of *NetworkSettings.Gateway* for the current container. (as in, from `docker inspect collectd`)
      * `docker/container_name` to use the value of *NetworkSettings.IPAddress* for the named container. (as in, from `docker inspect container_name`)
   * `Port` - port to use (master default: 5050, slave default: 5051)
   * `Separator` - optional, character to use to separate elements of a mesos metric name when it is used as collectd type-instance. (e.g. '.' instead of the mesos default of '/')
   *  `TrackingName` - applies **only** to active mesos master
      1. maintain metric continuity at the service level, regardless of which physical host is running the active master currently.
      2. send master metrics using common, virtual hostname/identifier.
   * `MetricConfigFile` - location of mesos metric configuration file. Should be fine at its default of `/etc/collectd/mesos.yaml`.

## Starting

### Manual start

From wherever `etc-collectd` was placed.

```
sudo docker run --name=cadvisor \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:rw \
  -v /sys:/sys:ro \
  -v /var/lib/docker/:/var/lib/docker:ro \
  -d google/cadvisor:latest

sudo docker run --name=collectd \
  -v $(pwd)/etc-collectd:/etc/collectd \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -d maier/cadvisor-collectd:latest
```

### Systemd units

The `collectd.service` and `cadvisor.service` unit files from this repository can be used as a starting point. Note, modify collectd unit file to ensure the path for `etc-collectd` points to where the configuration files are actually located. (default is `/conf/etc-collectd`)


## Troubleshooting

1. shell access
   * CAdvisor `docker exec -it cadvisor /bin/sh`, busybox based, use `opkg-install` to add additional packages.
   * Collectd `docker exec -it collectd /bin/sh`, alipine based, use `apk-install` to add additional packages.
1. verify docker socket in collectd container
   * `docker exec -it collectd /bin/sh`
   * `apk-install socat`
   * `echo -e "GET /containers/json HTTP/1.1\r\n" | socat unix-connect:/var/run/docker.sock -`
1. verify cadvisor (from host)
   * `curl -s "$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' cadvisor):8080/api/v2.0/machine" | python -m json.tool`
1. list cadvisor */system.slice/subcontainers* (from host), useful when editing `system_services:` list in `cadvisor.yaml`
   * `curl -s "$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' cadvisor):8080/api/v1.3/containers/system.slice" | python -c 'import json,sys,pprint;obj=json.load(sys.stdin);pprint.pprint(obj["subcontainers"]);'`


## On deck

In no particular priority order...

- [x] add mesos metrics collection plugin for Collectd
- [ ] ansible playbook
- [ ] option to pull container metrics from Docker or CAdvisor
- [ ] configure from consul
- [ ] configure from etcd
