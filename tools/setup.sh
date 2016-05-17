#!/bin/bash

SQL_CONF=$(crudini --get /etc/nova/nova.conf DEFAULT sql_connection)

if [ -z "$SQL_CONF" ]; then
   echo "Check /etc/nova/nova.conf"
   exit 2
fi

SQL_CLI=$(echo $SQL_CONF | sed 's/@[^\/]*//' | awk -F[:/] '{printf "%s -u%s -p%s %s -e ",$1,$4,$5,$6}')

rpm -q docker || yum install -y docker
rpm -q docker-python || yum install -y docker-python
openstack-config --set /etc/nova/nova.conf DEFAULT compute_driver novadocker.virt.docker.DockerDriver
openstack-config --set /etc/nova/nova.conf DEFAULT firewall_driver nova.virt.firewall.NoopFirewallDriver
openstack-config --set /etc/nova/nova.conf DEFAULT compute_manager nova.daolicloud.compute_manager.ComputeManager
openstack-config --set /etc/nova/nova.conf DEFAULT network_manager nova.daolicloud.network_manager.SimpleManager
openstack-config --set /etc/glance/glance-api.conf DEFAULT container_formats ami,ari,aki,bare,ovf,ova,docker
openstack-config --set /usr/lib/systemd/system/openstack-nova-compute.service Service User root

setenforce 0
sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
cp -rf usr/* /usr/

$SQL_CLI "alter table fixed_ips drop index uniq_fixed_ips0address0deleted"
$SQL_CLI "delete from fixed_ips; delete from networks;insert into networks(created_at,injected,cidr,netmask,bridge,gateway,broadcast,dns1,label,multi_host,uuid,deleted,enable_dhcp,share_address) values(NOW(),0,'10.0.0.0/8','255.0.0.0','br-int','10.255.255.254','10.255.255.255','8.8.8.8','novanetwork',0,'$(uuidgen)',0,0,0),(NOW(),0,'172.16.0.0/12','255.240.0.0','br-int','172.16.255.254','172.31.255.255','8.8.8.8','novanetwork',0,'$(uuidgen)',0,0,0),(NOW(),0,'192.168.0.0/16','255.255.0.0','br-int','192.168.255.254','192.168.255.255','8.8.8.8','novanetwork',0,'$(uuidgen)',0,0,0)"

systemctl daemon-reload
systemctl enable docker.service
systemctl enable openstack-nova-sync.service
systemctl start docker.service
systemctl restart openstack-nova-api
systemctl restart openstack-nova-sync
systemctl restart openstack-nova-network
systemctl restart openstack-nova-conductor
systemctl restart openstack-nova-compute
systemctl restart openstack-glance-api

echo "Installation Successfully"
