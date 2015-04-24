# Examples

Contains the artifacts necessary to instrument simple demonstrations for *Quick Starts*. The goal being to provide a low friction test-drive environment to explore the various components involved.


## Contents

* Vagrantfile - will start a CentOS 7 VM, install Docker, and pull the containers used by the quick starts. It will do all the leg work necessary to make running the quick starts as simple as possible.
* quickstart - a simple script to orchestrate the various quick start demonstrations.
* influxdb/ - a rudimentary configuration for InfluxDB which primarily adds the collectd input plugin.


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
> Note, the first `vagrant up` may take some time, it will depend on bandwidth.


## Configuration files

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

* The metrics being collected show up in `csv/` (`/home/vagrant/examples/csv`) which was mounted by the `quickstarts` script when it started the Collectd container.


### InfluxDB

```
./quickstart influxdb
```

* InfluxDB UI: <http://localhost:8083/>
* InfluxDB user: root
* InfluxDB password: root
* InfluxDB hostname and port: 127.0.0.1 8086
* Once you're in, click *Databases* then *Explore Data* next to the **collectd** database.
* In the query field, type `list series` and click the *Execute Query* button to see all of the metrics currently coming in from Collectd.
* Another query for demo purposes: `select value from /.*\/cadvisor.cpu\/time_ns-total/ limit 30`
* More information on how to use the [InfluxDB Query Language](http://influxdb.com/docs/v0.8/api/query_language.html).


### Graphite

```
./quickstart graphite
```

* Graphite UI: <http://localhost:8081/>
* Navigate the tree, on the left side of the screen, to *Graphite.centos7*, unless `collectd.conf` was modified to use custome hostname.


### CAdvisor

Access the built-in CAdvisor UI for realtime metrics here: <http://localhost:8080/>