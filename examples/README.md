# Examples

Contains simple artifacts for running the quick start examples.

## Basic usage

The enclosed Vagrantfile will start a CentOS 7 VM, with Docker and git installed. It will pull down the latest containers required for the quick starts. Note, this Vagrantfile depends on the [VirtualBox](https://www.virtualbox.org/) provider. 

```
vagrant up
vagrant ssh
```

## CSV

Nothing more to do, run the commands from the csv quick start on the repository readme.

## InfluxDB

A very basic configuration and collectd types file.

```
sudo docker run --name=influxdb -v /vagrant/examples/influxdb:/config -p 8083:8083 -p 8086:8086 -e PRE_CREATE_DB="collectd" -d tutum/influxdb:latest
```

Proceed with remaining steps in quick start and point your browser to <http://localhost:48083/>, use root:root to log in to the influxdb web interface.

## Graphite

```
sudo docker run --name=graphite -p 80:80 -d nickstenning/graphite
```

Proceed with remaining steps in quick start and point your browser to <http://localhost:48080/>.
