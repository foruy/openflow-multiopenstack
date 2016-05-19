import re
import netaddr

from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

def phone_heads():
    phones = range(130, 140) + range(150, 160) + range(180, 190)
    phones.remove(154)
    phones.remove(181)
    return phones

def _validate_phone(phone):
    #if len(phone) != 11 or int(phone[:3]) not in phone_heads():
    #    raise ValidationError(_('Enter a invalid phone number.'))
    if not re.match('^\d{4,}$', phone):
        raise ValidationError(_('Enter a invalid phone number.'))

def _validate_username(username):
    if not re.match('^[\w\.-]{4,20}$', username):
        raise ValidationError(_('Enter a valid username.'))

def _validate_password(password):
    if not re.match('^[\@A-Za-z0-9\!\#\$\%\^\&\*\.\~]{6,20}$', password):
        raise ValidationError(_('Enter a valid password.'))

def check_ignore(email):
    return email.split('@')[1] == 'daolicloud.com'

def check_data(name, value):
    if 'username' == name:
        _validate_username(value)
    elif 'email' == name:
        validators.validate_email(value)
    elif 'phone' == name:
        _validate_phone(value)
    else:
        raise ValidationError(_('Invalid request.'))

def validate_data(data):
    errors = {}
    valid_err = False
    cleaned_data = {}
    cleaned_data['username'] = data.get('name')
    cleaned_data['password'] = data.get('password')
    cleaned_data['email'] = data.get('email')
    cleaned_data['phone'] = data.get('phone')
    cleaned_data['company'] = data.get('company')
    cleaned_data['reason'] = data.get('reason')

    for key, val in cleaned_data.items():
        errors[key] = []
        if val in validators.EMPTY_VALUES or val.strip() == '':
            errors[key].append(_('This field is required.'))
            valid_err = True

    if not valid_err:
        try:
            _validate_username(cleaned_data['username'])
        except ValidationError as e:
            valid_err = True
            errors['username'].append(e)

        try:
            _validate_password(cleaned_data['password'])
        except ValidationError as e:
            valid_err = True
            errors['password'].append(e)

        try:
            validators.validate_email(cleaned_data['email'])
        except ValidationError as e:
            valid_err = True
            errors['email'].append(e)

        try:
            _validate_phone(cleaned_data['phone'])
        except ValidationError as e:
            valid_err = True
            errors['phone'].append(e)

    if not valid_err:
        errors = None

    return cleaned_data, errors

def validate_address(value):
    if not value.strip():
        raise ValidationError("Cann't be empty.")

    try:
        netaddr.IPAddress(value)
    except Exception:
        raise ValidationError("Invalid ip address.")
