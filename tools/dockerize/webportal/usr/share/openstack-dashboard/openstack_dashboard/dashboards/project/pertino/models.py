from django.db import models

# Create your models here.
class people(object):
    def __init__(self,name,email,statusi,device,network):
        self.name = name
        self.email = email
        self.status = status
        self.device = device
        self.network = network

class device(object):
    def __init__(self,hostname,ip_address,user,os,client,status,auth_mode):
        self.hostname = hostname
        self.ip_address = ip_address
        self.user = user
        self.os = os
        self.os = os
        self.status = status
        self.auth_mode = auth_mode


class network(object):
    def __init__(self,network_name,network_id,owner,people,device):
        self.network_name = network_name
        self.network_id = network_id
        self.owner = owner
        self.people = people
        self.device = device
