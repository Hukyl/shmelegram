import string


valid_chars = set(string.printable) - set(string.whitespace)


def validate_credential_characters(chars: str) -> bool:
    """
    Validate credentials characters.
    Characters must contain at least one uppercase

    Args:
        chars (str): [characters to check]

    Returns:
        bool: [are all characters valid]
    """
    # An iterative approach is twice as fast as with `all` and `any`
    any_uppercase = any_special = any_lowercase = any_digit = False
    for symbol in chars:
        if symbol not in valid_chars:
            return False
        elif symbol.isupper():
            any_uppercase = True
        elif symbol.islower():
            any_lowercase = True
        elif symbol.isdigit():
            any_digit = True
        elif symbol in string.punctuation:
            any_special = True
    return any_special and any_uppercase and any_lowercase and any_digit



def validate_username(username: str) -> bool:
    return username and validate_credential_characters(
        username
    ) and 4 < len(username) < 30


def validate_password(password: str) -> bool:
    return password and validate_credential_characters(
        password
    ) and 6 < len(password) < 15
