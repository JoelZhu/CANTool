from enum import Enum

SHORT_INTEL = "Intel"
SHORT_MOTOROLA_LSB = "M-LSB"
SHORT_MOTOROLA_MSB = "M-MSB"


class Format(Enum):
    UNDEFINED = ""
    INTEL = "Intel"
    MOTOROLA_LSB = "Motorola LSB"
    MOTOROLA_MSB = "Motorola MSB"

    @classmethod
    def get_short(cls, fmt: "Format") -> str:
        if fmt == Format.INTEL:
            return SHORT_INTEL
        elif fmt == Format.MOTOROLA_LSB:
            return SHORT_MOTOROLA_LSB
        elif fmt == Format.MOTOROLA_MSB:
            return SHORT_MOTOROLA_MSB
        else:
            return str(fmt)

    @classmethod
    def get_format(cls, short_format: str) -> "Format":
        if short_format == SHORT_INTEL:
            return Format.INTEL
        elif short_format == SHORT_MOTOROLA_LSB:
            return Format.MOTOROLA_LSB
        elif short_format == SHORT_MOTOROLA_MSB:
            return Format.MOTOROLA_MSB
        else:
            return Format.UNDEFINED
