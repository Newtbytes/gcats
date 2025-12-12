import beet.contrib.worldgen as worldgen

from .utils import mean


def pad(x: list, length: int, value=0) -> list:
    return x + [value] * max(length - len(x), 0)


def merge_amplitudes(a: list[float], b: list[float]) -> bool:
    length = max(len(a), len(b))

    a = list(map(mean, pad(a, length), pad(b, length)))

    return True


def merge_noise(self: worldgen.WorldgenNoise, other: worldgen.WorldgenNoise) -> bool:
    merge_amplitudes(self.data["amplitudes"], other.data["amplitudes"])

    return True
