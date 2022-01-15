"""
This module introduces util functions.
Defines following functions:
    - `validate_password`
    - `validate_username`

Defines following classes:
    - `redis_client/RedisClient`
"""

import string


def validate_password(password: str) -> bool:
    """
    Check if password is valid and return boolean.
    Introduces following requirements:
        - 6 < password length < 16
        - password is not empty
        - at least one digit
        - at least one uppercase
        - at least one special
        - at least one lowercase
        - all characters are ASCII

    Args:
        password (str): password to check

    Returns:
        bool: is password valid.
    """
    valid_chars = set(string.printable) - set(string.whitespace)
    if not (password and 6 < len(password) < 15):
        return False
    # An iterative approach is twice as fast as with `all` and `any`
    any_uppercase = any_special = any_lowercase = any_digit = False
    for symbol in password:
        if symbol not in valid_chars:
            return False
        if symbol.isupper():
            any_uppercase = True
        elif symbol.islower():
            any_lowercase = True
        elif symbol.isdigit():
            any_digit = True
        elif symbol in string.punctuation:
            any_special = True
    return any_special and any_uppercase and any_lowercase and any_digit



def validate_username(username: str) -> bool:
    """
    Check if username if valid and return boolean.
    Introduces following requirements:
        - 4 < username length < 30
        - username not empty
        - all characters are ASCII or digits

    Args:
        username (str): username to check

    Returns:
        bool: is username valid
    """
    valid_chars = string.ascii_letters + string.digits
    return username and all(
        x in valid_chars for x in username
    ) and 4 < len(username) < 30
