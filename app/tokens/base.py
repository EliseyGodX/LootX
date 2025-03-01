from abc import ABC, abstractmethod
from typing import Generic, Self, TypeVar

import jwt

from app.config import dataclass
from app.tokens.configs import BaseTokenConfig, JWTokenConfig
from app.tokens.payloads import BaseTokenPayload


class TokenError(Exception): ...
class EncodeTokenError(TokenError): ...
class DecodeTokenError(TokenError): ...


TokenConfig = TypeVar('TokenConfig', bound=BaseTokenConfig)


@dataclass
class BaseToken(ABC, Generic[TokenConfig]):
    payload: BaseTokenPayload
    config: TokenConfig

    @abstractmethod
    def encode(self) -> str: ...

    @classmethod
    @abstractmethod
    def decode(cls, token: str, config: TokenConfig) -> Self: ...


class JWToken(BaseToken[JWTokenConfig]):

    def encode(self) -> str:
        try:
            return jwt.encode(
                payload=self.payload.model_dump(),
                key=self.config.key,
                algorithm=self.config.alg,
                headers={
                    'alg': self.config.alg,
                    'typ': self.config.typ
                },
                json_encoder=self.config.json_encoder,
                sort_headers=self.config.sort_headers
            )
        except Exception as e:
            raise EncodeTokenError from e

    @classmethod
    def decode(cls, token: str, config: JWTokenConfig) -> Self:
        try:
            token_payload = BaseTokenPayload(
                **jwt.decode(
                    jwt=token,
                    key=config.key,
                    algorithms=config.alg
                )
            )
            return cls(
                payload=token_payload,
                **config.model_dump()
            )
        except Exception as e:
            raise DecodeTokenError from e
