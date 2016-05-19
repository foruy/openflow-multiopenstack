from oslo.db.sqlalchemy import models

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Column, schema, Text
from sqlalchemy import Float, Integer, String, Boolean
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base

from daoliagent.db.sqlalchemy import types
from daoliagent.openstack.common import uuidutils

BASE = declarative_base()

def MediumText():
    return Text().with_variant(MEDIUMTEXT(), 'mysql')

class User(BASE, models.ModelBase, models.TimestampMixin):
    """Represents a User."""
    __tablename__ = 'user'
    uuid = Column(String(36), primary_key=True, default=uuidutils.generate_uuid)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False)
    type = Column(Integer, default=0)
    phone = Column(String(11), nullable=False)
    company = Column(String(100), nullable=False)
    reason = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    extra = Column(types.JsonBlob(), default=dict())

class UserTask(BASE, models.ModelBase):
    __tablename__ = 'user_tasks'

    id = Column(Integer, primary_key=True)
    utype = Column(String(10), nullable=False)
    # text column used for storing a json object of user register    
    uobj = Column(MediumText())

class UserLogin(BASE, models.ModelBase, models.TimestampMixin):
    __tablename__ = 'user_login'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), nullable=False)
    user_addr = Column(String(17))
    user_type = Column(String(255))

class Instance(BASE, models.ModelBase, models.TimestampMixin):
    """Represents a instance."""
    __tablename__ = 'instances'
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(String(15))
    mac_address = Column(String(17))
    phy_ipv4 = Column(String(15))
    host = Column(String(100))
    project_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    availability_zone = Column(String(36), ForeignKey('zones.id'), nullable=False)
    image = Column(String(36), nullable=False)
    flavor = Column(String(36), nullable=False)
    status = Column(String(10), default=None)
    power_state = Column(Integer)
    fake_hostname = Column(String(255))

class UserProject(BASE, models.ModelBase):
    """Represents a user with project map."""
    __tablename__ = 'user_project'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    project_id = Column(String(36), nullable=False)
    keystone_user_id = Column(String(36), nullable=False)
    zone_id = Column(String(36), nullable=False)
    total_instances = Column(Integer, default=10)

class Firewall(BASE, models.ModelBase):
    """Represents an port map."""
    __tablename__ = 'firewalls'
    __table_args__ = (
        schema.UniqueConstraint("hostname", "gateway_port", name="uniq_hostname0gateway_port"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(100), nullable=False)
    gateway_port = Column(Integer, nullable=False)
    service_port = Column(Integer, nullable=False)
    instance_id = Column(String(36), nullable=False)
    fake_zone = Column(Boolean, nullable=False)
    
class SingleSecurityGroup(BASE, models.ModelBase):
    """Represents an security group for instance."""
    __tablename__ = 'single_security_groups'
    __table_args__ = (
        schema.UniqueConstraint(
            "top", "bottom", "user_id",
            name="uniq_single_security_group0top0bottom0user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    top = Column(String(36), nullable=False)
    bottom = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)

class ProjectNetwork(BASE, models.ModelBase):
    __tablename__ = 'project_networks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    third = Column(Integer, nullable=False, default=0)
    fourth = Column(Integer, nullable=False, default=2)
    project_id = Column(String(36), nullable=False)

class Gateway(BASE, models.ModelBase):
    __tablename__ = 'gateways'
    __table_args__ = (
        schema.UniqueConstraint('datapath_id', name='uniq_datapaht_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    datapath_id = Column(String(100), nullable=False)
    hostname = Column(String(100), nullable=False)
    idc_id = Column(Integer, default=0)
    idc_mac = Column(String(64))
    vint_dev = Column(String(100), nullable=False)
    vint_mac = Column(String(64), nullable=False)
    vext_dev = Column(String(100), nullable=False)
    vext_ip = Column(String(64))
    ext_dev = Column(String(100), nullable=False)
    ext_mac = Column(String(64), nullable=False)
    ext_ip = Column(String(64), nullable=False)
    int_dev = Column(String(100), nullable=False)
    int_mac = Column(String(64), nullable=False)
    int_ip = Column(String(64))
    zone = Column(String(36), nullable=False)
    count = Column(Integer, nullable=False, default=0)
    is_gateway = Column(Boolean, default=False)
    disabled = Column(Boolean, default=False)

class Image(BASE, models.ModelBase):
    __tablename__ = 'images'

    id = Column(String(36), nullable=False, primary_key=True)
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
    zone = Column(String(36), nullable=False)

class Zone(BASE, models.ModelBase):
    """Represents a Zone."""
    __tablename__ = 'zones'

    id = Column(String(36), primary_key=True, default=uuidutils.generate_uuid)
    name = Column(String(255), nullable=False)
    auth_url = Column(String(255), nullable=False)
    token = Column(String(255), nullable=False)
    default_instances = Column(Integer, default=10)
    disabled = Column(Boolean, default=False)
    idc_id = Column(Integer, default=0)

class Flavor(BASE, models.ModelBase):
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
    zone = Column(String(36), nullable=False)

class Resource(BASE, models.ModelBase, models.TimestampMixin):
    __tablename__ = 'resources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(255), nullable=False)
    source_id = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    extra = Column(types.JsonBlob())
    project_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)

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
    net_type = Column(Integer, nullable=False)
    user_id = Column(String(36), nullable=False)
    allocation_pools = relationship(IPAllocationPool,
                                    backref='subnet',
                                    lazy="joined",
                                    cascade='delete')

class Service(BASE, models.ModelBase):
    """Represents a api serivce."""
    __tablename__ = 'services'

    id = Column(String(36), primary_key=True, default=uuidutils.generate_uuid)
    name = Column(String(255))
    url = Column(String(255), nullable=False)
    topic = Column(String(20))
    idc_id = Column(Integer, default=0)
