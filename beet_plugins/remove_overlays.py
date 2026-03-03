import beet
from beet.core.utils import JsonDict


def beet_default(ctx: beet.Context):
    ctx.require(remove_overlays)


@beet.configurable
def remove_overlays(ctx: beet.Context, opts: JsonDict):
    for overlay in opts["overlays"]:
        ctx.data.overlays.pop(overlay)
