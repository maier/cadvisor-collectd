from __future__ import print_function
from cadvisor import CAdvisor
import collectd


class CAdvisorMetrics(CAdvisor):

    def __init__(self, config):
        super(CAdvisorMetrics, self).__init__(config)
        self.name = self.__class__.__name__
        self.log_info('Configured {} plugin.'.format(self.name))

    def log_error(self, msg):
        collectd.error(msg)

    def log_warning(self, msg):
        collectd.warning(msg)

    def log_notice(self, msg):
        collectd.notice(msg)

    def log_info(self, msg):
        collectd.info(msg)

    def log_debug(self, msg):
        collectd.debug(msg)

    def dispatch_metric(self, container_name, container_id, plugin, plugin_instance, metric_type, type_instance, metric_value):
        metric = collectd.Values()

        #
        # BUG  there isn't an easy way for a plugin to determine what hostname collectd is actually using.
        # the value is NOT passed to plugins, only commands run by the exec plugin. so, there is no way
        # to modify the hostname unless the exec version of the plugin is run, even though the python
        # version is *supposed* to be more efficient.
        #
        # hostname = metric.host
        # metric.host = self.gen_host_name(hostname, container_name, container_id)

        metric.plugin = self.gen_plugin_name(None, container_name, container_id, plugin)
        if plugin_instance:
            metric.plugin_instance = plugin_instance

        metric.type = metric_type
        if type_instance:
            metric.type_instance = type_instance

        metric.values = metric_value
        metric.dispatch()

#
# CAdvisor metrics plugin for collectd python
#

client = None


def configurator(collectd_conf):
    """
    configure the cadvisor metrics collector
    options:
        host: ip of target mesos host
        port: port of target mesos host
        config_file: path to cadvisor.yaml
    """
    global client

    collectd.info('Loading CAdvisorMetrics plugin')

    config = {}
    for item in collectd_conf.children:
        key = item.key.lower()
        val = item.values[0]
        if key == 'host':
            config['host'] = val
        elif key == 'port':
            config['port'] = int(val)
        elif key == 'configfile':
            config['config_file'] = val
        else:
            collectd.warning('cadvisor plugin: unknown config key {} = {}'.format(item.key, val))

    client = CAdvisorMetrics(config)


def reader():
    global client
    client.emit_metrics(client.fetch_metrics())


collectd.register_config(configurator)
collectd.register_read(reader)
