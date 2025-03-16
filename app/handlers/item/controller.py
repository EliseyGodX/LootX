# flake8-in-file-ignores: noqa: B904, WPS110, WPS400

from litestar.handlers import get
from litestar.openapi.spec import Example

from app import errors as error
from app import openapi_tags as tags
from app.config import DataBase, ItemConfig, Language, WoWAPI
from app.db.enums import EnumAddons, EnumLanguages
from app.db.exc import ItemNotFoundError
from app.errors import litestar_raise, litestar_response_spec
from app.handlers.abc.controller import BaseController
from app.handlers.item.dto import ResponseItemDTO
from app.types import WoWItemId


def lang_to_enumlang(lang: Language) -> EnumLanguages:
    try:
        return EnumLanguages(lang.value)
    except ValueError:
        return EnumLanguages.en


class ItemController(BaseController[ItemConfig]):
    config = ItemConfig()
    path = '/item'

    @get('/id/{item_id:str}', responses={
        422: litestar_response_spec(examples=[
            Example('ItemNotExists', value=error.ItemNotExists())
        ])
    }, tags=[tags.item_handler])
    async def get_item_by_id(
        self, db: DataBase, item_id: WoWItemId
    ) -> ResponseItemDTO:
        try:
            wow_item = await db.get_wow_item(item_id)
            return ResponseItemDTO(
                id=wow_item.id,
                wow_id=wow_item.wow_id,
                addon=wow_item.addon,
                lang=wow_item.lang,
                html_tooltip=wow_item.html_tooltip,
                icon_url=wow_item.icon_url,
                origin_link=wow_item.origin_link
            )
        except ItemNotFoundError:
            raise litestar_raise(error.ItemNotExists)

    @get('/wow-id/{item_wow_id:str}', tags=[tags.item_handler])
    async def get_item_by_wow_id(
        self, db: DataBase, lang: Language, wow_api: WoWAPI, item_wow_id: int,
        addon: EnumAddons = EnumAddons.retail
    ) -> ResponseItemDTO | None:
        try:
            wow_item = await db.get_wow_item_by_wow_id(
                wow_id=item_wow_id,
                addon=addon,
                lang=lang_to_enumlang(lang),
                wow_api=wow_api
            )
            if not wow_item:
                return None
            return ResponseItemDTO(
                id=wow_item.id,
                wow_id=wow_item.wow_id,
                addon=wow_item.addon,
                lang=wow_item.lang,
                html_tooltip=wow_item.html_tooltip,
                icon_url=wow_item.icon_url,
                origin_link=wow_item.origin_link
            )
        except ItemNotFoundError:
            raise litestar_raise(error.ItemNotExists)
