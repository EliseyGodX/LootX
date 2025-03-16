from app.db.enums import EnumAddons, EnumLanguages
from app.handlers.abc.dto import BaseDTO
from app.types import WoWItemId


class ResponseItemDTO(BaseDTO):
    id: WoWItemId
    wow_id: int
    addon: EnumAddons
    lang: EnumLanguages
    html_tooltip: str
    icon_url: str
    origin_link: str
