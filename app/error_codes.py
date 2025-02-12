# flake8-in-file-ignores: noqa: WPS115


class _ErrorCodes:
    UsernameNotUnique = '1'
    EmailNotUnique = '2'
    EmailNonExistent = '3'

    def __getattribute__(self, name: str) -> str:
        return 'error_code: ' + super().__getattribute__(name)


ErrorCodes = _ErrorCodes()
