import bcrypt


def get_hashed_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return hashed_password


def verify_password(password: str, hashed_password: str) -> bool:
    is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    return is_valid
