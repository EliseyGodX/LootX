from litestar import status_codes as status
from litestar.connection import Request
from litestar.exceptions import HTTPException

from app.config import Language


def get_language(request: Request) -> Language:
    lang = request.cookies.get('language', Language.en.value)
    try:
        lang = Language(lang)
    except ValueError:
        raise HTTPException(  # noqa: B904
            detail="Invalid 'language' cookie",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return lang
