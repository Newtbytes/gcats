import beet.contrib.worldgen as worldgen


def get_biomes(data: dict) -> list[dict]:
    return data["generator"]["biome_source"]["biomes"]


def merge_dimension(self: worldgen.Dimension, other: worldgen.Dimension) -> bool:
    self_biomes = get_biomes(self.data)
    other_biomes = get_biomes(other.data)

    for biome in other_biomes:
        if biome not in self_biomes:
            get_biomes(self.data).append(biome)

    return True
