


class OPFException(Exception):
    message = "An unknown exception occurred."

    def __init__(self, msg=None, **kwargs):
        self.kwargs = kwargs

        if not msg:
            msg = self.message

            try:
                msg = msg % kwargs
            except Exception:
                # at least get the core message out if something happened
                msg = self.message

        super(OPFException, self).__init__(msg)

class DevicePortNotFound(OPFException):
    message = 'no such network device %(device)s'

class IPAddressNotMatch(OPFException):
    message = 'IP address %(address)s do not match'
