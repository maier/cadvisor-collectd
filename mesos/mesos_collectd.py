from mesos import Mesos
import collectd


class MesosCollectd(Mesos):

    def __init__(self, config):
        super(MesosCollectd, self).__init__(config)
        self.name = self.__class__.__name__

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

    def dispatch_metric(self, metric_type, metric_type_instance, metric_value):
        metric = collectd.Values()
        metric.plugin = self.plugin
        metric.plugin_instance = self.plugin_instance
        metric.type = metric_type
        metric.type_instance = metric_type_instance
        metric.values = [metric_value]
        metric.dispatch()
        if self.tracking_enabled:
            metric.host = self.tracking_name
            metric.dispatch()
