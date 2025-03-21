from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Self, TypeVar
from xml.etree import ElementTree as ET

import httpx

from app.db.enums import EnumAddons, EnumLanguages
from app.db.wow_api.configs import BaseWoWAPIConfig, WoWHeadAPIConfig


class WoWAPIError(Exception): ...


@dataclass
class WoWAPIItem:
    wow_id: int
    addon: EnumAddons
    lang: EnumLanguages
    html_tooltip: str
    icon_url: str
    origin_link: str


WoWAPIConfig = TypeVar('WoWAPIConfig', bound=BaseWoWAPIConfig)


@dataclass
class BaseAsyncWoWAPI(ABC, Generic[WoWAPIConfig]):
    config: WoWAPIConfig

    @abstractmethod
    async def connect(self) -> Self: ...

    @abstractmethod
    async def get_item(
        self, id: int, addon: EnumAddons, lang: EnumLanguages
    ) -> WoWAPIItem | None: ...

    @abstractmethod
    async def close(self) -> None: ...


@dataclass
class WoWHeadAPI(BaseAsyncWoWAPI[WoWHeadAPIConfig]):

    async def connect(self) -> Self:
        self.client: httpx.AsyncClient = self.config.httpx_client
        return self

    async def get_item(
        self, id: int, addon: EnumAddons, lang: EnumLanguages
    ) -> WoWAPIItem | None:
        url = self.config.url.format(
            id=id,
            addon=addon.value if addon != EnumAddons.retail else '',
            lang=lang.value if lang != EnumLanguages.en else ''
        )
        response = await self.client.get(url)
        if response.status_code != 200:  # noqa: WPS432
            return None

        root = ET.fromstring(response.text)
        item_elem = root.find('item')
        if item_elem is None:
            return None

        return WoWAPIItem(
            wow_id=int(id),
            addon=addon,
            lang=lang,
            html_tooltip=item_elem.findtext('htmlTooltip', ''),
            icon_url=self.config.icon_url.format(
                icon=item_elem.findtext('icon', '')
            ),
            origin_link=item_elem.findtext('link', '')
        )

    async def close(self) -> None:
        await self.client.aclose()
