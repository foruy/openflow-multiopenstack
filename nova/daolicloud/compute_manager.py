from nova.compute import manager
from nova.daolicloud.linux.network import Network

class ComputeManager(manager.ComputeManager):

    def __init__(self, compute_driver=None, *args, **kwargs):
        super(ComputeManager, self).__init__(
            compute_driver=compute_driver, *args, **kwargs)
        self.network = Network()

    def gateway_get(self, context):
        return self.network.gateway_get()
