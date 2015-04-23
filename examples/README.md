# Examples

Contains simple artifacts for running the quick start examples. The enclosed Vagrantfile will start a CentOS 7 VM, install Docker, and pull the containers used by the quick starts. It will do all the leg work necessary to make running the quick starts as simple as possible.

## Requirements

This Vagrantfile depends on the [VirtualBox](https://www.virtualbox.org/) provider. 

### Optional configuration

* Resources - The default settings for CPU and memory in the Vagrantfile are:
	* cpu 2
	* memory 2048
	* If there are not adequate resources available on the system running the examples, modify the Vagrantfile accordingly. (or, to increase performance of the examples, adjust upwards...)
* Ports - several ports are exposed for InfluxDB and Graphite.
	* InfluxDB
		* tcp/8083
		* tcp/8086
	* Graphite
		* tcp/8081
	* CAdvisor
		* tcp/8080
	* If any of these ports conflict with ports on the system, edit the Vagrantfile and change the ports.
* Hostname - the quick starts will use `$(hostname)` as the hostname for Collectd to make things less complex.  

## Start the VM

```
vagrant up
vagrant ssh
cd examples
# run appropriate quick start command
./quickstart (csv|influxdb|graphite)
```

### Configuration files

The list of configuration files which will be used (created if they don't exist). To customize any of the quick starts ahead of time, copy the corresponding `.example` removing the extension. Keep the rest of the file name the same, e.g. `cp etc-collectd/collectd.conf.example etc-collectd/collectd.conf`

```
etc-collectd/collectd.conf

etc-collectd/cadvisor.yaml

# for CSV quick start
etc-collectd/conf.d/write_csv.conf

# for InfluxDB quick start
etc-collectd/conf.d/write_network.conf

# for Graphite quick start
etc-collectd/conf.d/write_graphite.conf
```

### CSV

```
./quickstart csv
```

### InfluxDB

```
./quickstart influxdb
```

A very basic configuration and collectd types file.


Proceed with remaining steps in quick start and point your browser to <http://localhost:8083/>, use root:root to log in to the influxdb web interface.

### Graphite

```
./quickstart graphite
```

Proceed with remaining steps in quick start and point your browser to <http://localhost:8081/>.


### CAdvisor

Access the built-in CAdvisor UI for realtime metrics.

<http://localhost:8080/>