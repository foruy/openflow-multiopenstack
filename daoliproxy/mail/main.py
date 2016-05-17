import smtplib
from oslo.config import cfg

from email.utils import formatdate
from email.mime.text import MIMEText

from jinja2 import Environment, PackageLoader

mail_opts = [
    cfg.StrOpt('email_server', help='The email server'),
    cfg.StrOpt('email_name', help='The email username'),
    cfg.StrOpt('email_password', help='The email password'),
    cfg.StrOpt('email_cc', default=[], help='The email cc to'),
    cfg.IntOpt('email_timeout', default=10, help='The email timeout'),
]

CONF = cfg.CONF
CONF.register_opts(mail_opts)

env = Environment(loader=PackageLoader('daoliproxy', 'mail/templates'))

def render(tpl, **context):
    template = env.get_template('%s.html' % tpl)
    return template.render(**context)

def send(receivers, timeout=None):
    if timeout is None:
        timeout = CONF.email_timeout
    #sender = '%s@%s' % (CONF.email_name, CONF.email_server)
    sender = CONF.email_name
    smtp = smtplib.SMTP(timeout=timeout)
    smtp.connect('smtp.%s' % CONF.email_server)
    smtp.login(CONF.email_name, CONF.email_password)
    for rec in receivers:
        msg = MIMEText(rec['body'], 'html', 'utf-8')
        msg.add_header('Subject', rec['subject'])
        msg.add_header('From', sender)
        msg.add_header('To', rec['email'])
        msg.add_header('Date', formatdate(localtime=True))
        smtp.sendmail(sender, rec['email'], msg.as_string())
    smtp.quit()
