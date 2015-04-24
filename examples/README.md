# Examples

Contains the artifacts necessary to instrument simple demonstrations for *Quick Starts*. The goal being to provide a low friction test-drive environment to explore the various components involved.


## Contents

Name | Description
---- | -----------
Vagrantfile | will start a CentOS 7 VM, install Docker, and pull the containers used by the quick starts. It will do all the leg work necessary to make running the quick starts as simple as possible.
quickstart | a simple script to orchestrate the various quick start demonstrations.
influxdb/ | a rudimentary configuration for InfluxDB which primarily adds the collectd input plugin.


## Requirements

This Vagrantfile depends on the [VirtualBox](https://www.virtualbox.org/) provider. 


### Optional configuration

**Resources**

Resource | Default
-------- | -------
CPU | 2
Memory | 2048

If there are not adequate resources available on the system running the examples, modify the Vagrantfile accordingly. (or, to increase performance of the examples, adjust upwards...)

**Ports**

Product | Port(s)
------- | ----
InfluxDB | tcp/8083, tcp/8086
Graphite | tcp/8081
CAdvisor | tcp/8080

If any of these ports conflict with ports on the system, edit the Vagrantfile and change the ports.

**Hostname**

The quick starts will use `$(hostname)` as the hostname for Collectd to make things less complex.  


## Start the VM

```
vagrant up
vagrant ssh
cd examples
# run appropriate quick start command
./quickstart (csv|influxdb|graphite)
```
> Note, the first `vagrant up` will take time, it will depend on bandwidth as files are retrieved.


## Configuration files

The list of configuration files which will be used (created if they don't exist). To customize any of the quick starts ahead of time, copy the corresponding example configuration file to a new file, without the '.example' extension. Keep the rest of the file name the same.

File | Description
---------------------------- | -----------
<code style="white-space: pre">etc-collectd/collectd.conf</code> | main collectd configuration, quickstart script will set `Hostname` to output from system's `hostname` command. ('centos7' is the hostname preset on the VM box).
<code style="white-space: pre">etc-collectd/cadvisor.yaml</code> | configuration for collecting metrics from cadvisor, quickstart script does not make changes, it uses the defaults.
<code style="white-space: pre">etc-collectd/conf.d/write_csv.conf</code> | **only** applies to CSV option, quickstart does not make any changes, defaults are used. 
<code style="white-space: pre">etc-collectd/conf.d/write_network.conf</code> | **only** applies to the InfluxDB option, quickstart script will set `Server`, replacing `FQDN|IP` with the IP address of the container running InfluxDB:<br />`docker inspect -f '{{.NetworkSettings.IPAddress}}' influxdb`.
<code style="white-space: pre">etc-collectd/conf.d/write_graphite.conf</code> | **only** applies to the Graphite option, quickstart script will set `Host`, replacing `FQDN|IP` with the IP address of the container running Graphite:<br />`docker inspect -f '{{.NetworkSettings.IPAddress}}' graphite`.


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
* Once logged in:
	*  Click *Databases* in the top navigation bar.
	*  Then, click *Explore Data* next to the **collectd** database.
* Viewing metrics using queries:
	* Type `list series` in the *Query* field and click the *[Execute Query]* button to see all metrics being received from Collectd.
	* An example query to see a graph: `select value from /.*\/cadvisor.cpu\/time_ns-total/ limit 30`
	* More information on how to use the [InfluxDB Query Language](http://influxdb.com/docs/v0.8/api/query_language.html).


### Graphite

```
./quickstart graphite
```

* Graphite UI: <http://localhost:8081/>
* Navigate the tree, on the left side of the screen, to *Graphite.centos7*, or whatever host name was used if `collectd.conf` was modified.


### CAdvisor

Access the built-in CAdvisor UI for realtime metrics here: <http://localhost:8080/>