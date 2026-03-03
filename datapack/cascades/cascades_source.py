import beet
import beet.contrib.worldgen as worldgen


def make_cascades_source(ctx: beet.Context):
    for namespace in ctx.data.keys():
        namespace = ctx.data.get(namespace)

        if namespace is None:
            continue

        for ty in list(namespace.keys()):
            if ty in [
                worldgen.WorldgenBiome,
                worldgen.Dimension,
                worldgen.DimensionType,
                worldgen.WorldgenStructure,
                worldgen.WorldgenConfiguredFeature,
                worldgen.WorldgenPlacedFeature,
                worldgen.WorldgenBiomeTag,
                beet.Advancement,
            ]:
                namespace.pop(ty)
