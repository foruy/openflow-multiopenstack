#!/bin/bash

rpm -q docker || yum install -y docker
rpm -q docker-python || yum install -y docker-python
openstack-config --set /etc/nova/nova.conf DEFAULT compute_driver novadocker.virt.docker.DockerDriver
openstack-config --set /etc/nova/nova.conf DEFAULT firewall_driver nova.virt.firewall.NoopFirewallDriver
openstack-config --set /etc/nova/nova.conf DEFAULT compute_manager nova.daolicloud.compute_manager.ComputeManager
openstack-config --set /usr/lib/systemd/system/openstack-nova-compute.service Service User root

setenforce 0
sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
cp -rf usr/* /usr/

systemctl daemon-reload
systemctl enable docker.service
systemctl start docker.service
systemctl restart openstack-nova-compute

echo "Installation Successfully
