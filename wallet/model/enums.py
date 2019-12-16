from enum import IntEnum

from pytz import timezone, utc


class Currency(IntEnum):
    USD = 1
    RMB = 2

    @property
    def symbol(self):
        return {
            Currency.USD: '$',
            Currency.RMB: '¥',
        }[self]


class Timezone(IntEnum):
    US = 1
    CN = 2

    def from_utc(self, dt):
        return utc.localize(dt).astimezone(_TZ[self])

    def to_utc(self, dt):
        return _TZ[self].localize(dt).astimezone(utc)


_TZ = {
    Timezone.US: timezone('America/Los_Angeles'),
    Timezone.CN: timezone('Asia/Shanghai'),
}
