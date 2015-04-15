from mesos_collectd import MesosCollectd
import collectd


class MesosMaster(MesosCollectd):

    def __init__(self, config):
        super(MesosMaster, self).__init__(config)
        self.name = self.__class__.__name__
        self.log_info('{} configuring.'.format(self.name))

#
# mesos master metrics collector python plugin for collectd
#
client = None


def configurator(collectd_conf):
    """
    configure the mesos metrics collector
    options:
        host: ip of target mesos host
        port: port of target mesos host
        trackingname: vanity host name to use for master tracking
    """
    global client

    mesos_config = {}
    for item in collectd_conf.children:
        mesos_config[item.key.lower()] = item.values[0]

    mesos_config['profile'] = 'master'
    client = MesosMaster(mesos_config)


def reader():
    global client
    client.emit_metrics(client.fetch_metrics())


collectd.register_config(configurator)
collectd.register_reader(reader)
