from django.core.exceptions import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

def limit_port_range(port):
    if port not in range(10000, 50000):
        raise ValidationError(_("Enter an integer value "
                                "between 10000 and 50000"))
