FROM centos
MAINTAINER CentOS7, Daolicloud
RUN yum -y install epel-release
ADD tmp/ /tmp/
RUN yum -y localinstall /tmp/packages/*.rpm
RUN ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key
RUN ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key
RUN echo "root:daoli123" | chpasswd
RUN sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
RUN crudini --set /etc/my.cnf.d/server.cnf mysqld port 3307
COPY etc/ /etc/
COPY usr/ /usr/
RUN mkdir /var/log/daoliproxy /var/log/mariadb
RUN rm -rf /tmp/packages; chown -R mysql:mysql /var/log/mariadb
RUN /usr/share/openstack-dashboard/manage.py compress
VOLUME [ "/var/lib/mysql" ]

CMD ["/usr/bin/supervisord"]
