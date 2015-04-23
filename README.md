# cadvisor-collectd

Collecting host and container metrics using [CAdvisor](https://registry.hub.docker.com/u/google/cadvisor/) and [Collectd](https://github.com/collectd/collectd/).

Status: [docker registry](https://registry.hub.docker.com/u/maier/cadvisor-collectd/)


# Problem

* Collect metrics from host system, running containers, and processes exposing metrics running in containers.
* Send metrics to multiple external (from host) systems simultaneously.
* Run in a container, not on the host system.


# Solution

### Collectd and CAdvisor

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

# Features

* Leverage Collectd's wealth of plugins
* Leveage CAdvisor's ability to see the *Host* as well as the *Containers*
* Runs in a separate container (not as a 1st class process on the Host)
* Has built-in metrics collectors for:
   * Host
   * Containers
   * Mesos
* Easy to use...which is, of course, relative and subjective :)
* Basic metric name manipulation for metric continuity

# Getting started

See the repository wiki for [complete documentation](https://github.com/maier/cadvisor-collectd/wiki) on configuring and using the cadvisor-collectd container.

## On deck

- [x] add mesos metrics collection plugin for Collectd
- [x] refactor cadvisor and mesos -- provide both command line and plugin capabilities
- [ ] add service filter modes to cadvisor
    - [ ] group options
        - [ ] mounts
        - [ ] sockets
        - [ ] docker scopes
        - [ ] user slice
        - [ ] system slice
        - [ ] other slices
    - [ ] service options
        - [ ] all
        - [ ] include -- implicit exclusion, explicit inclusion
        - [ ] exclude -- implicit inclusion, explicit exclusion
- [ ] rewirte and reorganize documentation
    - [ ] introduction
    - [ ] configuring collectd
    - [ ] configuring cadvisor plugin
    - [ ] configuring mesos plugin
- [ ] ansible playbook
    - [ ] cadvisor service
    - [ ] cadvisor-collectd service
    - [ ] configure collectd
    - [ ] configure cadvisor plugin
    - [ ] configure mesos plugin
- [ ] options for metric source (for docker containers)
    - [ ] Docker
    - [ ] CAdvisor
- [ ] configuration sources
    - [ ] consul
    - [ ] etcd
        - [ ] confd
