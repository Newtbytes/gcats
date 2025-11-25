from beet import Context


# FIXME: this just sets supported_formats to null instead of removing the key
# from the output pack.mcmeta
def remove_deprecated_fields(ctx: Context):
    deprecated_fields = ["supported_formats"]

    for field in deprecated_fields:
        if hasattr(ctx.assets, field):
            setattr(ctx.assets, field, None)

        if hasattr(ctx.data, field):
            setattr(ctx.assets, field, None)
