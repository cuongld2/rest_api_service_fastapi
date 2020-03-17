

def test_debug():
    from app_utils import create_access_token
    from datetime import timedelta
    access_token_expires = timedelta(minutes=10)
    access_token = create_access_token(data={"sub": "cuongld"}, expires_delta=access_token_expires)
    print(access_token)
    from app_utils import decode_access_token
    decoded_access_token = decode_access_token(data=access_token)
    print(decoded_access_token)


