from typing import Union

import beet.contrib.worldgen as worldgen

from .utils import mean


class Biome:
    name: str

    weirdness: list[float]
    continentalness: list[float]
    erosion: list[float]
    temperature: list[float]
    humidity: list[float]
    depth: list[float]
    offset: float

    def __init__(self, data: dict):
        self.name = data["biome"]

        params = data["parameters"]

        self.weirdness = params["weirdness"]
        self.continentalness = params["continentalness"]
        self.erosion = params["erosion"]
        self.temperature = params["temperature"]
        self.humidity = params["humidity"]
        self.depth = params["depth"]
        self.offset = params["offset"]

    def merge_noise(self, a: list[float], b: list[float]) -> list[float]:
        assert len(a) == len(b)

        return list(map(mean, a, b))

    def merge(self, other: "Biome") -> bool:
        assert self.name == other.name

        if self == other:
            return False

        self.weirdness = self.merge_noise(self.weirdness, other.weirdness)
        self.continentalness = self.merge_noise(
            self.continentalness, other.continentalness
        )
        self.erosion = self.merge_noise(self.erosion, other.erosion)
        self.temperature = self.merge_noise(self.temperature, other.temperature)
        self.humidity = self.merge_noise(self.humidity, other.humidity)
        self.depth = self.merge_noise(self.depth, other.depth)
        self.offset = mean(self.offset, other.offset)

        return True

    def __eq__(self, other: "Biome") -> bool:
        return self.into() == other.into()

    def into(self) -> dict:
        return {
            "biome": self.name,
            "parameters": {
                "weirdness": self.weirdness,
                "continentalness": self.continentalness,
                "erosion": self.erosion,
                "temperature": self.temperature,
                "humidity": self.humidity,
                "depth": self.depth,
                "offset": self.offset,
            },
        }


def get_biomes(data: dict) -> Union[list[dict], list[Biome]]:
    return data["generator"]["biome_source"]["biomes"]


def list_biomes(data: dict) -> list[str]:
    return [
        (biome.name if isinstance(biome, Biome) else biome["biome"])
        for biome in get_biomes(data)
    ]


def get_biome(biomes: list[Biome], name: str) -> Union[Biome, None]:
    for biome in biomes:
        if biome.name == name:
            return biome


def convert_to_biome(biomes: list) -> list[Biome]:
    return [Biome(biome) for biome in biomes]


def merge_dimension(self: worldgen.Dimension, other: worldgen.Dimension) -> bool:
    self.data["generator"]["biome_source"]["biomes"] = convert_to_biome(
        get_biomes(self.data)
    )
    other.data["generator"]["biome_source"]["biomes"] = convert_to_biome(
        get_biomes(other.data)
    )

    for biome in get_biomes(other.data):
        assert isinstance(biome, Biome)
        if biome.name not in list_biomes(self.data):
            get_biomes(self.data).append(biome)  # type: ignore
        else:
            other_biome = get_biome(get_biomes(other.data), biome.name)
            biome.merge(other_biome)

    self.data["generator"]["biome_source"]["biomes"] = [
        biome.into() for biome in get_biomes(self.data)
    ]
    return True
