#
# Collectd exec script to gather metrics from CAdvisor and output them for Collectd
#

from __future__ import print_function
import sys
from abc import ABCMeta, abstractmethod

import json
import yaml
import urllib2
import socket
import docker
import re


class CAdvisor(object):
    """ Abstract base class for gathering host and container metrics """
    __metaclass__ = ABCMeta

    def __init__(self, config):
        """
        host: string, 'ip' or 'docker/(name|id)' of docker container running cadvisor
        port: optional, string (quote Port: in collectd config otherwise it comes through as a float)
        config_file: pathspec for the full yaml config of this plugin
        """
        super(CAdvisor, self).__init__()
        self.name = self.__class__.__name__

        self.doc_url = 'https://github.com/maier/cadvisor-collectd/wiki/Configuring-CAdvisor'

        self.config_host = config.get('host', 'cadvisor/docker')
        self.config_port = config.get('port', 8080)
        self.config_file = config.get('config_file', '/etc/collectd/cadvisor.yaml')
        self.host = None
        self.port = None
        self.config = {}

        #
        # initialize static configuration items
        #

        try:
            # self.log_info('Parsing configuration {}'.format(self.config_file))
            f = open(self.config_file, 'r')
            self.config = yaml.load(f)
        except Exception, e:
            self.log_error('Unable to load configuration "{}": {}'.format(self.config_file, e))
            sys.exit(1)

        self.docker_socket = self.config.get('docker_socket', '/var/run/docker.sock')

        self.active_metrics = self.get_active_metrics()

        self.system_enabled = self.config.get('system_enabled', False)
        self.system_fs_metrics = self.config.get('system_fs_metrics', False)
        self.system_services = self.config.get('system_services', {
                                               'options': {
                                                   'include_mounts': False,
                                                   'include_sockets': False,
                                                   'include_docker_scopes': False,
                                                   'include_system_slice': False,
                                                   'include_user_slice': False,
                                                   'include_other_slice': False
                                               },
                                               'include': [],
                                               'exclude': '*'})
        self.service_filter = None

        if self.system_services['include'] is not list:
            self.system_services['include'] = []

        if self.system_services['exclude'] is not list:
            self.system_services['exclude'] = []

        if not self.system_services['include'] and not self.system_services['exclude']:                 # Include everything, not controlled by system_services.options
            self.service_filter = 'all'
        elif '*' in self.system_services['exclude'] and '*' not in self.system_services['include']:     # implicit exclusion, explicit inclusion
            self.service_filter = 'include'
        elif '*' in self.system_services['include'] and '*' not in self.system_services['exclude']:     # implicit inclusion, explicit exclusion
            self.service_filter = 'exclude'
        elif'*' in self.system_services['include'] and '*' in self.system_services['exclude']:
            self.log_error('Conflicting service filter configuration, cannot be include and exclude simultaneously. See documentation: {}'.format(self.doc_url))
            sys.exit(1)
        else:
            self.log_error('No service filter configuration identified. See documentation: {}'.format(self.doc_url))
            sys.exit(1)

        self.docker_enabled = self.config.get('docker_enabled', True)
        self.docker_container_config = self.config.get('docker_containers', [])
        if type(self.docker_container_config) is not list:
            self.docker_container_config = []

        # namespec macros:
        # {hn}  = hostname
        # {cn}  = container name
        # {cid} = 12 char hex container id
        self.host_namespec = self.config.get('ns_host', '{hn}')
        self.plugin_namespec = self.config.get('ns_plugin', '{cn}.')

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
    def dispatch_metric(self, container_name, container_id, plugin, plugin_instance, metric_type, type_instance, metric_value):
        """
        send metrics to the target output
        intended to be overridden - e.g. by an abstraction to collectd's Values.dispatch()
        """
        pass

    def gen_host_name(self, hostname, container_name, container_id):
        return(self.host_namespec.format(hn=hostname, cn=container_name, cid=container_id))

    def gen_plugin_name(self, hostname, container_name, container_id, plugin):
        return('{}{}'.format(self.plugin_namespec.format(hn=hostname, cn=container_name, cid=container_id), plugin))

    def is_container_id(self, id):
        """
        basically, is 'id' a hex string...
        """
        try:
            if int(id, 16):
                return True
        except ValueError:
            return False

    def fix_container_name(self, name):
        """
        strings all prefixed with '/' in the Names[] element returned from docker inspect_container
        """
        if name[0:1] != '/':
            return('/' + name)
        else:
            return(name)

    def container_match(self, target, container_id, container_names):
        if self.is_container_id(target):
            if container_id[0:len(target)] == target:
                return True
        else:
            if self.fix_container_name(target) in container_names:
                return True
        return False

    def set_container_slice_ids(self):
        """
        adds a 'SliceId' key to each of the containers
        initially sets it to None
        uses docker_container_config to determine which containers to set the SliceId
        """
        docker_container_config = self.docker_container_config
        all_containers = '*' in docker_container_config
        for container_idx, container in enumerate(self.docker_container_list):
            self.docker_container_list[container_idx]['SliceId'] = None
            slice_id = "/system.slice/docker-{cid}.scope".format(cid=container['Id'])
            if all_containers:
                self.docker_container_list[container_idx]['SliceId'] = slice_id
            else:
                for include_container in docker_container_config:
                    if self.container_match(include_container, container['Id'], container['Names']):
                        self.docker_container_list[container_idx]['SliceId'] = slice_id
                        break  # not supporting substrings, explicit container name/id only

    def set_cadvisor_connect_info(self):
        """
        set cadvisor host and port, explicitly or derived from container
        """
        #
        # return if host and port are already set
        # and were defined statically in the collectd config
        #
        host_spec = self.config_host
        port_spec = self.config_port
        docker_prefix = 'docker/'
        if self.host and self.port and not host_spec.lower().startswith(docker_prefix):
            return True

        ip = None
        port = port_spec

        if re.match('^\d{1,3}(\.\d{1,3}){3}$', host_spec):
            ip = host_spec
        elif host_spec.lower().startswith(docker_prefix):               # cadvisor_connect is a docker container specifier
            container_identifier = host_spec[len(docker_prefix):]
            cadvisor_container = None
            try:
                cli = docker.Client(base_url='unix:/{}'.format(self.docker_socket))
                cadvisor_container = cli.inspect_container(container_identifier)
                if not cadvisor_container['State']['Running']:
                    self.log_error('Error specified CAdvisor container "{}" is not running.'.format(host_spec))
                    sys.exit(1)
                ip = cadvisor_container['NetworkSettings']['IPAddress']
                for exposed_port in cadvisor_container['Config']['ExposedPorts']:
                    if '/tcp' in exposed_port:
                        port = exposed_port.split('/')[0]
                        break
            except docker.errors.APIError, e:
                self.log_error('Error retrieving container from docker: {}'.format(e))
                sys.exit(1)
            except IOError, e:
                self.log_error('Error connecting to docker socket "{}": {}'.format(self.docker_socket, e))
                sys.exit(1)
        else:
            self.log_error('Invalid cadvisor connection method specified "{}".'.format(host_spec))
            sys.exit(2)

        connection_specifier = '{}:{}'.format(ip, port)
        if not re.match('^\d{1,3}(\.\d{1,3}){3}:\d+$', connection_specifier):
            self.log_error('No valid connection specifier found for cadvisor "{}" = "{}".'.format(host_spec, connection_specifier))
            sys.exit(2)

        self.host = ip
        self.port = port
        return(True)

    def set_docker_container_list(self):
        """
        get list of containers from docker socket using docker api
        add a SliceId element (to hold the cadvisor slice id)
        """

        try:
            cli = docker.Client(base_url='unix:/{}'.format(self.docker_socket))
            #
            # fragile: docker-py defaults to only listing 'running' containers
            # call explicitly with all=False in case default behavior changes
            # TODO check the docker-py code for this API call to ensure all=False does force only running
            #
            self.docker_container_list = cli.containers(all=False)
        except docker.errors.APIError, e:
            self.log_error('Error retrieving from docker: {}'.format(e))
            sys.exit(1)
        except IOError, e:
            self.log_error('Error connecting to docker socket "{}": {}'.format(self.docker_socket, e))
            sys.exit(1)

        return(True)

    def get_active_metrics(self):
        """
        locate the various metric groups in the configuration (keys starting with 'metrics_')
        verify that 'none' is *not* in the list (which would disable the metric group)
        build list of metric sections (key w/o 'metrics_')
        can be done as a one-liner using list/dict completions, long line, complicated to parse visually
            self.active_metrics = {metric[8:]: self.config[metric] for metric in self.config if metric[0:8] == 'metrics_' and 'none' not in map(str.lower, self.config[metric])}
        """
        key_prefix = 'metrics_'
        active_metrics = {}
        for k, v in self.config.iteritems():
            if k.startswith(key_prefix):
                if 'none' not in map(str.lower, self.config[k]):
                    active_metrics[k[len(key_prefix):]] = v
        return(active_metrics)

    def fetch_metrics(self):
        """fetch stats from CAdvisor, parse returned JSON, return a python data structure"""
        #
        # dynamic items needed for each fetch run.
        #   cadvisor connection information
        #
        self.set_cadvisor_connect_info()

        url = "http://{}:{}/api/v2.0/stats?recursive=true&count=1".format(self.host, self.port)
        stats = {}
        try:
            response = urllib2.urlopen(url, None, 5)
            stats = json.loads(response.read())
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                self.log_error("Failed to reach server, reason {}".format(e.reason))
            elif hasattr(e, 'code'):
                self.log_error("Server unable to fulfill request {}".format(e.code))
            sys.exit(1)
        except socket.timeout:
            self.log_error("Timeout connecting to {}".format(url))
            sys.exit(1)
        return(stats)

    #
    # Collectd is particular about the way it wants metric names formatted.
    # The naming schema is documented here: https://collectd.org/wiki/index.php/Naming_schema
    #
    # basically: host "/" plugin ["-" plugin instance] "/" type ["-" type instance]
    #
    # notes:
    #   1 not all systems *receiving* metrics honor 'host', you may need to get creative with plugin_ns
    #   2 pay particular attention to how plugin instance and type instance are used
    #   3 the 'type's used are a combination of the types in the collectd default types.db and custom types in cadvisor-types.db
    #

    def emit_cpu_metrics(self, container_name, container_id, metrics):
        """ parse cpu metric structure; create a collectd'ish metric name; map metric value(s) to collectd types; output metric """

        plugin = 'cpu'

        plugin_instance = None
        metric_type = 'gauge'
        type_instance = 'avg'
        self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [metrics['load_average']])

        plugin_instance = None
        metric_type = 'time_ns'
        for key in ('system', 'total', 'user'):
            type_instance = key
            self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [metrics['usage'][key]])

        metric_type = 'time_ns'
        type_instance = None
        for i, v in enumerate(metrics['usage']['per_cpu_usage']):
            plugin_instance = i
            self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [v])

    def emit_memory_metrics(self, container_name, container_id, metrics):
        """ parse memory metric structure; create a collectd'ish metric name; map metric value(s) to collectd types; output metric """

        plugin = 'memory'

        plugin_instance = None
        metric_type = 'memory'
        type_instance = 'usage'
        self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [metrics['usage']])

        plugin_instance = None
        metric_type = 'memory'
        type_instance = 'working_set'
        self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [metrics['working_set']])

        plugin_instance = None
        metric_type = 'gauge'
        type_instance = None
        for item in ('hierarchical', 'container'):
            item_key = '{}_data'.format(item)
            plugin_instance = item_key
            for key in metrics[item_key]:
                type_instance = key
                self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [metrics[item_key][key]])

    def emit_network_metrics(self, container_name, container_id, metrics):
        """ parse network metric structure; create a collectd'ish metric name; map metric value(s) to collectd types; output metric """

        plugin = 'net'

        plugin_instance = None
        metric_type = None
        type_instance = None

        #
        # the if_(dropped|packets|octets|errors) collectd types
        # expect the values to be compound in the form: rx:tx
        #
        for i, v in enumerate(metrics):
            plugin_instance = 'if{}'.format(i)
            for item in ('dropped', 'packets', 'bytes', 'errors'):
                rx_key = 'rx_{}'.format(item)
                tx_key = 'tx_{}'.format(item)
                metric_type = 'if_{}'.format('octets' if item == 'bytes' else item)
                self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [v[rx_key], v[tx_key]])

    def emit_diskio_metrics(self, container_name, container_id, metrics):
        """ parse diskio metric structure; create a collectd'ish metric name; map metric value(s) to collectd types; output metric """

        plugin = 'blkio'

        #
        # see: https://www.kernel.org/doc/Documentation/cgroups/blkio-controller.txt
        #

        plugin_instance = None
        metric_type = None
        type_instance = None

        #
        # times
        #
        metric = 'io_time'
        if metric in metrics:
            metric_type = 'time_ms'
            type_instance = metric
            for device in metrics[metric]:
                plugin_instance = '{}_{}'.format(device['major'], device['minor'])
                self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device['stats']['Count']])

        metric_type = 'time_ns'
        for metric in ('io_wait_time', 'io_service_time'):
            if metric in metrics:
                for device in metrics[metric]:
                    plugin_instance = '{}_{}'.format(device['major'], device['minor'])
                    for stat in device['stats']:
                        type_instance = '{}_{}'.format(metric, stat)
                        self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device['stats'][stat]])

        # bytes
        metric = 'io_service_bytes'
        metric_type = 'bytes'
        if metric in metrics:
            for device in metrics[metric]:
                plugin_instance = '{}_{}'.format(device['major'], device['minor'])
                for stat in device['stats']:
                    type_instance = '{}_{}'.format(metric, stat)
                    self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device['stats'][stat]])

        # gauges/counters
        metric = 'sectors'
        metric_type = 'gauge'
        if metric in metrics:
            type_instance = '{}'.format(metric)
            for device in metrics[metric]:
                plugin_instance = '{}_{}'.format(device['major'], device['minor'])
                self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device['stats']['Count']])

        metric_type = 'gauge'
        for metric in ('io_serviced', 'io_merged'):
            if metric in metrics:
                for device in metrics[metric]:
                    plugin_instance = '{}_{}'.format(device['major'], device['minor'])
                    for stat in device['stats']:
                        type_instance = '{}_{}'.format(metric, stat)
                        self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device['stats'][stat]])

        metric = 'io_queued'
        metric_type = 'counter'
        if metric in metrics:
            for device in metrics[metric]:
                plugin_instance = '{}_{}'.format(device['major'], device['minor'])
                for stat in device['stats']:
                    type_instance = '{}_{}'.format(metric, stat)
                    self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device['stats'][stat]])

    def emit_load_metrics(self, container_name, container_id, metrics):
        """ parse load metric structure; create a collectd'ish metric name; map metric value(s) to collectd types; output metric """

        plugin = 'load_stats'
        plugin_instance = None
        metric_type = 'gauge'
        type_instance = None

        for metric in metrics:
            type_instance = '-{}'.format(metric)
            self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [metrics[metric]])

    def emit_filesystem_metrics(self, container_name, container_id, metrics):
        """ parse filesystem metric structure; create a collectd'ish metric name; map metric value(s) to collectd types; output metric """
        plugin = 'fs'
        plugin_instance = None
        metric_type = None
        type_instance = None

        for device in metrics:
            device_name = device['device']
            if device_name[0:19].lower() == '/dev/mapper/docker-':
                device_name = device_name.replace('/dev/mapper/', '')
                device_name_parts = device_name.split('-')
                device_name_parts[-1] = device_name_parts[-1][0:12]
                device_name = '_'.join(device_name_parts)

            plugin_instance = device_name

            metric_type = 'bytes'
            for stat in ('capacity', 'usage'):
                type_instance = stat
                self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device[stat]])

            metric_type = 'time_ms'
            for stat in ('read_time', 'io_time', 'weighted_io_time', 'write_time'):
                type_instance = stat
                self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device[stat]])

            metric_type = 'gauge'
            for stat in ('writes_completed', 'reads_completed', 'writes_merged', 'sectors_written', 'reads_merged', 'sectors_read'):
                type_instance = stat
                self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device[stat]])

            metric_type = 'counter'
            type_instance = 'io_in_progress'
            self.dispatch_metric(container_name, container_id, plugin, plugin_instance, metric_type, type_instance, [device['io_in_progress']])

    def output_metrics(self, container_name, container_id, metrics, fs_metrics=False):
        """ parcel out the various metric sections to dedicated (isolated) handlers for each of the distinct structures. """

        if metrics['has_cpu'] and 'cpu' in self.active_metrics:
            self.emit_cpu_metrics(container_name, container_id, metrics['cpu'])

        if metrics['has_memory'] and 'memory' in self.active_metrics:
            self.emit_memory_metrics(container_name, container_id, metrics['memory'])

        if metrics['has_network'] and 'network' in self.active_metrics:
            self.emit_network_metrics(container_name, container_id, metrics['network'])

        if metrics['has_diskio'] and 'diskio' in self.active_metrics:
            self.emit_diskio_metrics(container_name, container_id, metrics['diskio'])

        if metrics['has_load'] and 'load_stats' in self.active_metrics:
            self.emit_load_metrics(container_name, container_id, metrics['load_stats'])

        if metrics['has_filesystem'] and fs_metrics:
            self.emit_filesystem_metrics(container_name, container_id, metrics['filesystem'])

    def emit_metrics(self, metrics):
        """walk through retrieved CAdvisor metrics output each metric for collectd"""
        for service in metrics.keys():
            if service == '/':
                if self.system_enabled:
                    self.output_metrics('sys', 0, metrics[service][0], self.system_fs_metrics)
                else:
                    continue
            elif service == '/system.slice':
                if self.system_services['options']['include_system_slice']:
                    self.output_metrics('sys.slice', 0, metrics[service][0], False)
                else:
                    continue
            elif service == '/user.slice':
                if self.system_services['options']['include_user_slice']:
                    self.output_metrics('usr.slice', 0, metrics[service][0], False)
                else:
                    continue
            elif service[-6:] == '.slice':
                if self.system_services['options']['include_other_slice']:
                    self.output_metrics('oth.slice', 0, metrics[service][0], False)
                else:
                    continue
            elif service[-6:] == '.mount':
                if self.system_services['options']['include_mounts']:
                    self.output_metrics('mount', 0, metrics[service][0], False)
                else:
                    continue
            elif service[-8:] == '.sockets':
                if self.system_services['options']['include_sockets']:
                    self.output_metrics('socket', 0, metrics[service][0], False)
                else:
                    continue
            elif service[0:21] == '/system.slice/docker-' and service[-6:] == '.scope':
                if self.system_services['options']['include_docker_scopes']:
                    self.output_metrics('docker', 0, metrics[service][0], False)
                else:
                    continue
            else:

                try:
                    real_service_name = service.split('/')[-1].replace('.service', '.svc')
                except (ValueError, KeyError):
                    real_service_name = service

                if self.service_filter == 'all':
                    self.output_metrics(real_service_name, 0, metrics[service][0], False)

                elif self.service_filter == 'include':
                    for elem in self.system_services['include']:
                        if elem in service:
                            self.output_metrics(real_service_name, 0, metrics[service][0], False)

                elif self.service_filter == 'exclude':
                    cleared = 0

                    for elem in self.system_services['exclude']:
                        if elem not in service:
                            cleared += 1

                    if cleared == len(self.system_services['exclude']):
                        self.output_metrics(real_service_name, 0, metrics[service][0], False)

                else:
                        self.log_error("rut roh...There's an elephant in the room, never should have gotten here!")
                        sys.exit(10)

        if self.docker_enabled:
            #
            # dynamic items needed for each fetch run.
            #   list of running containers from docker
            #   slice ids for running containers
            #
            self.set_docker_container_list()
            self.set_container_slice_ids()
            for docker_container in self.docker_container_list:
                if docker_container['SliceId']:
                    self.output_metrics(''.join(docker_container['Names']).replace('/', ''), docker_container['Id'][0:12], metrics[docker_container['SliceId']][0])

# END
