from typing import Any, Literal, TypeAlias


class _Sentinel:

    def __bool__(self) -> Literal[False]:
        return False


Sentinel: Any = _Sentinel()
Seconds: TypeAlias = int
RegistrationToken: TypeAlias = str
AccessToken: TypeAlias = str
RefreshToken: TypeAlias = str
