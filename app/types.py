from typing import Any, Literal, TypeAlias

from app.config import MAILER_TYPE, CACHE_TYPE


class _Sentinel:

    def __bool__(self) -> Literal[False]:
        return False


Sentinel: Any = _Sentinel()
Seconds: TypeAlias = int

RegistrationToken: TypeAlias = str
AccessToken: TypeAlias = str
RefreshToken: TypeAlias = str

Mailer: TypeAlias = MAILER_TYPE
Cache: TypeAlias = CACHE_TYPE

UserId: TypeAlias = str
Username: TypeAlias = str
