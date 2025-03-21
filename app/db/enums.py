from enum import Enum


class EnumClasses(Enum):
    warrior = 'warrior'
    paladin = 'paladin'
    hunter = 'hunter'
    rogue = 'rogue'
    priest = 'priest'
    shaman = 'shaman'
    mage = 'mage'
    warlock = 'warlock'
    monk = 'monk'
    druid = 'druid'
    demon_hunter = 'demon-hunter'
    death_knight = 'death-knight'
    evoker = 'evoker'

    def __repr__(self) -> str:
        return f'{self.value!r}'


class EnumAddons(Enum):
    retail = 'retail'
    classic = 'classic'
    cata = 'cata'
    tbc = 'tbc'
    wotlk = 'wotlk'

    def __repr__(self) -> str:
        return f'{self.value!r}'


class EnumLanguages(Enum):
    ru = 'ru'
    de = 'de'
    en = 'en'
    es = 'es'
    fr = 'fr'
    it = 'it'
    pt = 'pt'
    ko = 'ko'
    cn = 'cn'
