__all__ = ["biome", "mergeables"]

import beet

from . import biome, mergeables


def beet_default(ctx: beet.Context):
    ctx.require(beet.subproject("@beet_plugins"))
