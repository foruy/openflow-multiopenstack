"""
SQLAlchemy models for daoliproxy data.
"""

from oslo_config import cfg
from oslo_utils import uuidutils
from oslo_db.sqlalchemy import models
from sqlalchemy import (Column, Index, Integer, BigInteger, String, schema)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float

from daoliproxy.db.sqlalchemy import types

CONF = cfg.CONF
BASE = declarative_base()

def MediumText():
    return Text().with_variant(MEDIUMTEXT(), 'mysql')

class ProxyBase(models.ModelBase):
    metadata = None

    def __copy__(self):
        """Implement a safe copy.copy()."""
        session = orm.Session()

        copy = session.merge(self, load=False)
        session.expunge(copy)
        return copy

    def save(self, session=None):
        from daoliproxy.db.sqlalchemy import api

        if session is None:
            session = api.get_session()

        super(ProxyBase, self).save(session=session)


class User(BASE, ProxyBase, models.TimestampMixin):
    """Represents a user."""

    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, default=uuidutils.generate_uuid)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False)
    type = Column(Integer, default=0)
    phone = Column(String(11))
    company = Column(String(255))
    reason = Column(String(255))
    enabled = Column(Boolean, default=True)
    extra = Column(types.JsonBlob(), default=dict())

class UserLogin(BASE, ProxyBase, models.TimestampMixin):
    __tablename__ = 'user_login'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    user_addr = Column(String(64))
    user_type = Column(String(255))

class UserTask(BASE, ProxyBase):
    __tablename__ = 'user_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    utype = Column(String(255), nullable=False)
    # text column used for storing a json object of user register    
    uobj = Column(MediumText())

#class UserProject(BASE, ProxyBase):
#    """Represents a user with project map."""
#
#    __tablename__ = 'user_projects'
#
#    id = Column(Integer, primary_key=True, autoincrement=True)
#    user_id = Column(String(36), nullable=False)
#    zone_id = Column(String(36), nullable=False)
#    keystone_project_id = Column(String(36), nullable=False)
#    keystone_user_id = Column(String(36), nullable=False)
#    total_instances = Column(Integer, default=10)

class UserToken(BASE, ProxyBase, models.TimestampMixin):
    """Represents a user token."""

    __tablename__ = 'user_tokens'

    id = Column(String(64), primary_key=True)
    user_id = Column(String(36), nullable=False)

class KeystoneToken(BASE, ProxyBase, models.TimestampMixin):
    """Represents a keystone token."""

    __tablename__ = 'keystone_tokens'

    id = Column(String(64), primary_key=True)
    expires = Column(DateTime)
    user_id = Column(String(36), nullable=False)
    project_id = Column(String(36), nullable=False)
    user_token_id = Column(String(64), ForeignKey('user_tokens.id'),
                           nullable=False)
    catalog = Column(types.JsonBlob(), default=dict())
    zone_id = Column(String(36), nullable=False)

class Service(BASE, ProxyBase):

    __tablename__ = 'services'

    id = Column(String(36), primary_key=True, default=uuidutils.generate_uuid)
    name = Column(String(255))
    url = Column(String(64), nullable=False)
    topic = Column(String(255))
    idc_id = Column(Integer, default=0)

class Zone(BASE, ProxyBase):
    """Represents a Zone."""
    __tablename__ = 'zones'

    id = Column(String(36), primary_key=True, default=uuidutils.generate_uuid)
    name = Column(String(255), nullable=False)
    auth_url = Column(String(255), nullable=False)
    auth_token = Column(String(255), nullable=False)
    idc_id = Column(Integer, default=0)
    default_instances = Column(Integer, default=10)
    disabled = Column(Boolean, default=False)

class Instance(BASE, ProxyBase, models.TimestampMixin):
    """Represents an instance."""

    __tablename__ = 'instances'

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    host = Column(String(255))
    keystone_project_id = Column(String(36))
    user_id = Column(String(36), nullable=False)
    zone_id = Column(String(36), ForeignKey('zones.id'), nullable=False)
    image_id = Column(String(36), nullable=False)
    flavor_id = Column(String(36), nullable=False)
    status = Column(String(10), default=None)
    power_state = Column(Integer)
    fake_hostname = Column(String(255))

class InstanceNetwork(BASE, ProxyBase):
    """Represents an instance network info."""

    __tablename__ = 'instance_networks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(64))
    mac_address = Column(String(64))
    version = Column(Integer)
    instance_id = Column(String(36), nullable=False)
    network_id = Column(String(36), nullable=False)
    addresses = relationship(Instance, backref="addresses",
                            foreign_keys=instance_id,
                            primaryjoin="and_("
            "InstanceNetwork.instance_id==Instance.id)")

class Image(BASE, ProxyBase):

    __tablename__ = 'images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    imageid = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    checksum = Column(String(32))
    container_format = Column(String(32), nullable=False)
    disk_format = Column(String(32), default='raw')
    is_public = Column(Boolean, default=True)
    min_disk = Column(Integer, default=0)
    min_ram = Column(Integer, default=0)
    size = Column(Integer, nullable=False)
    owner = Column(String(32))
    status = Column(String(32))
    property = Column(types.JsonBlob())
    display_format = Column(String(32))
    zone_id = Column(String(36), nullable=False)

class Flavor(BASE, ProxyBase):

    __tablename__ = 'flavors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    flavorid = Column(String(36), nullable=False)
    name = Column(String(255))
    vcpus = Column(Integer, nullable=False)
    ram = Column(Integer, nullable=False)
    disk = Column(Integer, nullable=False)
    swap = Column(String(10), default='')
    ephemeral = Column(Integer)
    rxtx_factor = Column(Float, default=1)
    is_public = Column(Boolean, default=True)
    zone_id = Column(String(36), nullable=False)

class Gateway(BASE, ProxyBase):
    __tablename__ = 'gateways'

    __table_args__ = (
        schema.UniqueConstraint('datapath_id', name='uniq_datapaht_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    datapath_id = Column(String(255), nullable=False)
    hostname = Column(String(255), nullable=False)
    idc_id = Column(Integer, default=0)
    idc_mac = Column(String(64))
    vint_dev = Column(String(255), nullable=False)
    vint_mac = Column(String(64), nullable=False)
    vext_dev = Column(String(255), nullable=False)
    vext_ip = Column(String(64))
    ext_dev = Column(String(255), nullable=False)
    ext_mac = Column(String(64), nullable=False)
    ext_ip = Column(String(64), nullable=False)
    int_dev = Column(String(255), nullable=False)
    int_mac = Column(String(64), nullable=False)
    int_ip = Column(String(64))
    zone_id = Column(String(36), nullable=False)
    count = Column(Integer, nullable=False, default=0)
    is_gateway = Column(Boolean, default=False)
    disabled = Column(Boolean, default=False)

class Network(BASE, ProxyBase):
    """Represents a network."""
    __tablename__ = 'networks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    networkid = Column(String(36), nullable=False)
    gateway = Column(String(64))
    netype = Column(Integer, nullable=False)
    zone_id = Column(String(36), nullable=False)

class NetworkType(BASE, ProxyBase):
    __tablename__ = 'network_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cidr = Column(String(64), nullable=False)

################################
class IPAvailabilityRange(BASE, models.ModelBase):
    __tablename__ = 'ipavailabilityranges'

    allocation_pool_id = Column(String(36), ForeignKey('ipallocationpools.id',
                                                       ondelete="CASCADE"),
                                primary_key=True)
    first_ip = Column(String(64), nullable=False)
    last_ip = Column(String(64), nullable=False)

    def __repr__(self):
        return "%s - %s" % (self.first_ip, self.last_ip)

class IPAllocationPool(BASE, models.ModelBase):
    __tablename__ = 'ipallocationpools'

    id = Column(String(36), primary_key=True, default=uuidutils.generate_uuid)
    subnet_id = Column(String(36), ForeignKey('subnets.id',
                                              ondelete="CASCADE"))
    first_ip = Column(String(64), nullable=False)
    last_ip = Column(String(64), nullable=False)
    available_ranges = relationship(IPAvailabilityRange,
                                    backref='ipallocationpool',
                                    lazy="joined",
                                    cascade='delete')

    def __repr__(self):
        return "%s - %s" % (self.first_ip, self.last_ip)

class Subnet(BASE, models.ModelBase):
    """Represents a tenant subnet.

    When a subnet is created the first and last entries will be created. These
    are used for the IP allocation.
    """
    __tablename__ = 'subnets'

    id = Column(String(36), primary_key=True, default=uuidutils.generate_uuid)
    name = Column(String(255))
    cidr = Column(String(64), nullable=False)
    gateway_ip = Column(String(64))
    netype = Column(Integer, nullable=False)
    user_id = Column(String(36), nullable=False)
    allocation_pools = relationship(IPAllocationPool,
                                    backref='subnet',
                                    lazy="joined",
                                    cascade='delete')

class SingleSecurityGroup(BASE, ProxyBase):
    """Represents an security group for instance."""
    __tablename__ = 'single_security_groups'
    __table_args__ = (
        schema.UniqueConstraint(
            "start", "end", "user_id",
            name="uniq_single_security_group0start0end0user_id"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(String(36), nullable=False)
    end = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)

class Firewall(BASE, ProxyBase):
    """Represents a port map."""
    __tablename__ = 'firewalls'
    __table_args__ = (
        schema.UniqueConstraint("hostname", "gateway_port",
            name="uniq_hostname0gateway_port"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(100), nullable=False)
    gateway_port = Column(Integer, nullable=False)
    service_port = Column(Integer, nullable=False)
    instance_id = Column(String(36), nullable=False)
    fake_zone = Column(Boolean, nullable=False)

class Resource(BASE, ProxyBase, models.TimestampMixin):
    __tablename__ = 'resources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(255), nullable=False)
    source_id = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    extra = Column(types.JsonBlob())
    user_id = Column(String(36), nullable=False)
