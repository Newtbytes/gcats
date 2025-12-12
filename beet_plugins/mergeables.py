import beet
import beet.contrib.worldgen as worldgen

from .biome import merge_biome
from .noise import merge_noise
from .dimension import merge_dimension


def beet_default(ctx: beet.Context):
    worldgen.worldgen(ctx)
    ctx.require("beet_plugins.mergeables")


worldgen.WorldgenBiome.merge = merge_biome
worldgen.WorldgenNoise.merge = merge_noise
worldgen.Dimension.merge = merge_dimension


def merge_with_warning(self: beet.File, other: beet.File) -> bool:
    name = self.__class__.__name__

    if name not in getattr(beet.File, "failed_merge_types") and name not in [
        "PngFile",
        "Advancement",
    ]:
        print(f"failed to merge: '{self.__class__.__name__}'")
        getattr(beet.File, "failed_merge_types").add(name)

    return False


setattr(beet.File, "failed_merge_types", set())
beet.File.merge = merge_with_warning
