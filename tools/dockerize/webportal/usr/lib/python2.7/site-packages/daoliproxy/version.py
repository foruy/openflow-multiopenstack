DAOLIPROXY_VENDOR = "OpenStack Foundation"
DAOLIPROXY_PRODUCT = "DaoliProxy"
DAOLIPROXY_PACKAGE = None # OS distro package version suffix

loaded = False

class VersionInfo(object):
    release = "1.el7.centos"
    version = "2015.1.21"

    def version_string(self):
        return self.version

    def release_string(self):
        return self.release

version_info = VersionInfo()
version_string = version_info.version_string

def vendor_string():
    return DAOLIPROXY_VENDOR

def product_string():
    return DAOLIPROXY_PRODUCT

def package_string():
    return DAOLIPROXY_PACKAGE

def version_string_with_package():
    if package_string() is None:
        return version_info.version_string()
    else:
        return "%s-%s" % (version_info.version_string(), package_string())
