import datetime

def now():
    return datetime.datetime.now()

def after(window, dt=None):
    if dt is None:
        dt = now()
    return dt + datetime.timedelta(seconds=window)
