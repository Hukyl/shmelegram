import string


def validate_password(password: str) -> bool:
    valid_chars = set(string.printable) - set(string.whitespace)
    if not (password and 6 < len(password) < 15):
        return False
    # An iterative approach is twice as fast as with `all` and `any`
    any_uppercase = any_special = any_lowercase = any_digit = False
    for symbol in password:
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
    valid_chars = string.ascii_letters + string.digits 
    return username and all(
        x in valid_chars for x in username
    ) and 4 < len(username) < 30
