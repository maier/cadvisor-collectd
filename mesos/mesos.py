from __future__ import print_function
import sys
from abc import ABCMeta, abstractmethod

import json
import yaml
import urllib2
import socket
import docker
import re

#
# collectd python docs
#
# https://collectd.org/documentation/manpages/collectd-python.5.shtml
# http://dartarrow.net/collectd-python-plugin/311


class Mesos(object):
    """ Abstract Base Class for gathering metrics from mesos slave and master servers """
    __metaclass__ = ABCMeta

    def __init__(self, config):
        super(Mesos, self).__init__()

        self.name = self.__class__.__name__
        self.config = config

        self.plugin = 'mesos'
        self.plugin_instance = self.config['profile']
        self.active_master_key = 'master/elected'
        self.tracking_enabled = False
        try:
            self.tracking_name = self.config['trackingname']
        except KeyError:
            self.tracking_name = None

        self.port = self.config['port']
        # get mesos host (ip) from docker if configured to do so
        if self.config['host'][0:6].lower() == 'docker':
            self.get_host_from_docker()
        else:
            self.host = self.config['host']

        self.url = 'http://{}:{}/metrics/snapshot'.format(self.host, self.port)
        self.mesos_separator = '/'
        self.separator = self.config['separator'] if 'separator' in self.config else None

        # load mesos metrics configuration
        f = open(self.config['metricconfigfile'], 'r')
        config['metrics_config'] = yaml.safe_load(f)

    def log(self, message, level='INFO'):
        """
        log a message to stdout 'INFO' or stderr 'ERR'
        just gobbles up the abstract log_<level> methods which are intended to be overridden
        """
        msg = '{level} -- {msg}'.format(level=level, msg=message)
        if level == 'ERR':
            print(msg, file=sys.stderr)
        else:
            print(msg)

    @abstractmethod
    def log_error(self, message):
        self.log('{name}: {msg}'.format(name=self.name, msg=message), 'ERR')

    @abstractmethod
    def log_warning(self, message):
        self.log('{name}: {msg}'.format(name=self.name, msg=message), 'ERR')

    @abstractmethod
    def log_notice(self, message):
        self.log('{name}: {msg}'.format(name=self.name, msg=message))

    @abstractmethod
    def log_info(self, message):
        self.log('{name}: {msg}'.format(name=self.name, msg=message))

    @abstractmethod
    def log_debug(self, message):
        self.log('{name}: {msg}'.format(name=self.name, msg=message))

    @abstractmethod
    def dispatch_metric(self, metric_type, metric_type_instance, metric_value):
        """
        send metrics to the target output
        intended to be overridden - e.g. by an abstraction to collectd's Values.dispatch()
        """
        pass

    def fetch_metrics(self):
        """
        Retrieve metrics from mesos endpoint
        Convert returned JSON to python data structure
        Return metrics
        """
        metrics = {}
        try:
            response = urllib2.urlopen(self.url, None, 5)
            metrics = json.loads(response.read())
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                self.log_error('Failed to reach server "{}", reason {}'.format(self.url, e.reason))
            elif hasattr(e, 'code'):
                self.log_error('Server "{}" unable to fulfill request {}'.format(self.url, e.code))
            sys.exit(1)
        except socket.timeout:
            self.log_error('Timeout connecting to "{}"'.format(self.url))
            sys.exit(1)

        return(metrics)

    def emit_metrics(self, metrics={}):
        """
        iterate list of metrics:
            set metric type based on metrics configuration
            set metric type instance to metric name from mesos
            skip metrics configured with a type of 'ignore'
            optionally, change type instance separator from '/' to a user supplied separator
            call abstract dispatch_metric method to output metric
        """
        mesos_sep = self.mesos_separator
        user_sep = self.separator
        metrics_cfg = self.config['metrics_config']
        default_metric_type = metrics_cfg['default_metric_type']

        # disable tracking by default (master may have changed since last run)
        # enable it if this is a) a master, b) the active master, and c) a tracking name has been set
        self.tracking_enabled = False
        if self.config['profile'] == 'master' and self.tracking_name:
            self.tracking_enabled = self.active_master_key in metrics and metrics[self.active_master_key] == 1

        for metric in metrics:
            try:
                metric_type = metrics_cfg[metric]
                if metric_type.lower() == 'ignore':
                    continue
            except KeyError:
                metric_type = default_metric_type
            metric_type_instance = metric.replace(mesos_sep, user_sep) if user_sep else metric
            self.dispatch_metric(metric_type=metric_type, metric_type_instance=metric_type_instance, metric_value=metrics[metric])

    def get_host_from_docker(self):
        """
        obtain 'host' to use via two docker specific triggers.

        docker:gateway - use this container's gateway (NetworkSettings.Gateway) as the mesos ip.
        useful if mesos is running on the system host, not in a container, and listening to 0.0.0.0

        docker/<name> - use <name> to find the mesos container and use its NetworkSettings.IPAddress.
        e.g. docker/mesos-master assuming a docker container was run with --name=mesos-master

        """
        docker_socket = 'unix://var/run/docker.sock'
        ip = ""
        host = self.config['host']
        try:
            cli = docker.Client(base_url=docker_socket)
            if host.lower() == 'docker:gateway':
                docker_container = cli.inspect_container(socket.gethostname())
                ip = docker_container['NetworkSettings']['Gateway']
            elif host[0:7].lower() == 'docker/':
                container_name = host.split('/', 2)[1]
                if len(container_name) == 0:
                    self.log_error('Invalid Mesos Host container name "{}" specified.'.format(host))
                    sys.exit(1)
                docker_container = cli.inspect_container(container_name)
                ip = docker_container['NetworkSettings']['IPAddress']
        except docker.errors.APIError, e:
            self.log_error('Docker error for container "{}": {}'.format(host, e))
            sys.exit(1)
        except IOError, e:
            self.log_error('Error connecting to docker socket "{}": {}'.format(docker_socket, e))
            sys.exit(1)
        except KeyError, e:
            self.log_error('Mesos Host container "{}", unable to find required key -- {}.'.format(host, e))
            sys.exit(1)

        if re.match('^\d{1,3}(\.\d{1,3}){3}$', ip):
            self.host = ip
        else:
            self.log_error('Mesos Host container "{}", "{}" not a valid IP address.'.format(host, ip))
            sys.exit(1)
