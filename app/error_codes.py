
class ErrorExtra(dict):  # noqa: WPS600
    error_code: int
    message: str


username_not_unique = ErrorExtra(
    error_code=1,
    message='Username not unique'
)

email_not_unique = ErrorExtra(
    error_code=2,
    message='Email not unique'
)

email_non_existent = ErrorExtra(
    error_code=3,
    message='Email does not exist'
)

registration_token_invalid = ErrorExtra(
    error_code=4,
    message='Registration token is invalid'
)

access_token_invalid = ErrorExtra(
    error_code=5,
    message='Access token is invalid'
)

refresh_token_invalid = ErrorExtra(
    error_code=6,
    message='Refresh token is invalid'
)

user_is_active = ErrorExtra(
    error_code=7,
    message='The user is already active'
)
