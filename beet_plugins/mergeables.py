import beet
import beet.contrib.worldgen as worldgen

from .biome import merge_biome


def beet_default(ctx: beet.Context):
    worldgen.worldgen(ctx)
    ctx.require("beet_plugins.mergeables")


worldgen.WorldgenBiome.merge = merge_biome
