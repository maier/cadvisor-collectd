#!/usr/bin/env sh


# a little preamble to ensure access to the docker socket
# from the collectd cadvisor exec plugin script.
#
# note, exec plugin commands *cannot* run as uid=0


# if the `-v /var/run/docker.sock:/var/run/docker.sock`
# binding is changed, reflect the change below.
#
docker_sock="/var/run/docker.sock"


# user and group in etc-collectd/conf.d/cadvisor.conf
# used to run the script. if the user and/or group
# are changed in the configuration file, reflect the
# change(s) below.
#
exec_plugin_user="nobody"
exec_plugin_group="docker"


# determine the group id of the docker.sock owner
#
sock_group_id=$(/bin/stat -c %g $docker_sock 2>/dev/null)
[ $? -eq 0 ] || { echo "$docker_sock not found!"; exit 1; }

if [ $sock_group_id -eq 0 ]; then
	echo "$docker_sock group is 'root', host OS not running docker.service with Group=docker. Exec plugins will not have access to docker.sock."
else
	# add a group with the id and add the exec_plugin_user to
	# the group.
	#
	# ignore any errors (that the group already exists or that
	# the user is already a member).
	#
	/usr/sbin/addgroup -g $sock_group_id $exec_plugin_group &>/dev/null
	/usr/sbin/addgroup $exec_plugin_user $exec_plugin_group &>/dev/null
fi


# fire in the hole
#
exec /usr/sbin/collectd -f -C /etc/collectd/collectd.conf

#END
