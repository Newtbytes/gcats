import beet


def beet_default(ctx: beet.Context):
    ctx.require(fix_formats)


def major_format(format: beet.FormatSpecifier) -> int:
    if isinstance(format, int):
        return format

    if isinstance(format, tuple):
        return format[0]


def fix_formats(ctx: beet.Context):
    for overlay_meta in ctx.data.mcmeta.data["overlays"]["entries"]:
        overlay = ctx.data.overlays.get(overlay_meta["directory"])
        if overlay is not None:
            min_format: beet.FormatSpecifier
            max_format: beet.FormatSpecifier

            if "max_format" in overlay_meta and "min_format" in overlay_meta:
                min_format = overlay_meta["min_format"]
                max_format = overlay_meta["max_format"]
            elif overlay.max_format is not None and overlay.min_format is not None:
                min_format = overlay.min_format
                max_format = overlay.max_format

            formats = [
                major_format(min_format),
                major_format(max_format),
            ]

            overlay_meta["formats"] = formats
