import beet
import beet.contrib.worldgen as worldgen

from .biome import merge_biome
from .noise import merge_noise


def beet_default(ctx: beet.Context):
    worldgen.worldgen(ctx)
    ctx.require("beet_plugins.mergeables")


worldgen.WorldgenBiome.merge = merge_biome
worldgen.WorldgenNoise.merge = merge_noise
