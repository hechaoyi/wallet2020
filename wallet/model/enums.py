from enum import IntEnum


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

    @property
    def tzname(self):
        return {
            Timezone.US: 'America/Los_Angeles',
            Timezone.CN: 'Asia/Shanghai',
        }[self]
