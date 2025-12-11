from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

import beet
import beet.contrib.worldgen as worldgen


def beet_default(ctx: beet.Context):
    worldgen.worldgen(ctx)
    ctx.require("beet_plugins.mergeables")


def mean(a, b):
    return (a + b) / 2


def floor_mean(a: int, b: int) -> int:
    return int(mean(a, b))


class Color:
    r: int
    g: int
    b: int

    def __init__(self, color: int):
        b = color.to_bytes(length=3)

        self.r = b[0]
        self.g = b[1]
        self.b = b[2]

    def merge(self, other: "Color") -> bool:
        self.r = floor_mean(self.r, other.r)
        self.g = floor_mean(self.g, other.g)
        self.b = floor_mean(self.b, other.b)

        return True

    def into(self) -> int:
        return int.from_bytes([self.r, self.g, self.b])


class GrassColorModifier(Enum):
    NONE = 1
    DARK_FOREST = 2
    SWAMP = 3

    @classmethod
    def from_str(cls, val: str) -> "GrassColorModifier":
        match val:
            case "none":
                return cls.NONE
            case "dark_forest":
                return cls.DARK_FOREST
            case "swamp":
                return cls.SWAMP
            case _:
                raise ValueError

    def merge(self, other: "GrassColorModifier") -> bool:
        # prefer dark_forest
        match (self, other):
            case (GrassColorModifier.NONE, _) | (
                GrassColorModifier.SWAMP,
                GrassColorModifier.DARK_FOREST,
            ):
                self = other
            case (_, _):
                return False

        return True

    def into(self) -> str:
        match self:
            case GrassColorModifier.NONE:
                return "none"
            case GrassColorModifier.DARK_FOREST:
                return "dark_forest"
            case GrassColorModifier.SWAMP:
                return "swamp"


class TemperatureModifier(Enum):
    NONE = 1
    FROZEN = 2

    @classmethod
    def from_str(cls, val: str) -> "TemperatureModifier":
        match val:
            case "none":
                return cls.NONE
            case "frozen":
                return cls.FROZEN
            case _:
                raise ValueError

    def merge(self, other: "GrassColorModifier") -> bool:
        # prefer frozen
        match (self, other):
            case (TemperatureModifier.NONE, TemperatureModifier.FROZEN):
                self = other
            case (_, _):
                return False

        return True

    def into(self) -> str:
        match self:
            case TemperatureModifier.NONE:
                return "none"
            case TemperatureModifier.FROZEN:
                return "frozen"


@dataclass
class FeatureStep(beet.SupportsMerge):
    features: list[str]

    # TODO: merge and diff are definitely overcomplicated and can be simplified
    def merge(self, other: "FeatureStep") -> bool:
        if self == other:
            return False

        changes = self.diff(other)

        self.features = [dict(value=f, delete=False) for f in self.features]

        for i, ops in changes.items():
            for op in ops:
                fn = op[0]
                args = op[1:] if len(op) > 1 else tuple()

                if fn is list.insert:
                    fn(self.features, i, dict(value=args[0], delete=False))
                elif fn is list.append:
                    fn(self.features, dict(value=args[0], delete=False))

                self[i]["delete"] = fn is list.pop and self[i]["value"].startswith(
                    "minecraft:"
                )

        self.features = [f["value"] for f in self.features if not f["delete"]]

        return True

    def diff(self, other: "FeatureStep") -> dict[int, list]:
        changes = defaultdict(list)

        self_i = 0
        other_i = 0
        while True:
            if self_i >= len(self) and other_i >= len(other):
                break

            if self_i >= len(self):
                changes[self_i].append((list.insert, other[other_i]))
                self_i += 1
                other_i += 1
                continue

            if other_i >= len(other):
                changes[self_i].append((list.pop,))
                self_i += 1
                continue

            previous_same = self[self_i - 1] == other[other_i - 1]
            current_same = self[self_i] == other[other_i]
            next_same = False

            if self_i + 1 < len(self) and other_i + 1 < len(other):
                next_same = self[self_i + 1] == other[other_i + 1]

            if current_same:
                self_i += 1
                other_i += 1
                continue

            if not current_same:
                if (
                    self_i + 1 < len(self)
                    and previous_same
                    and other[other_i] == self[self_i + 1]
                ) or self[self_i] not in other:
                    changes[self_i].append((list.pop,))
                    self_i += 1
                    continue

                if previous_same or not next_same:
                    changes[self_i] = [(list.insert, other[other_i])] + changes[self_i]
                    other_i += 1
                    continue

        return changes

    def __contains__(self, feature: str):
        return feature in self.features

    def __getitem__(self, i: int) -> str:
        return self.features[i]

    def __setitem__(self, i: int, feature: str):
        self.features[i] = feature

    def __len__(self):
        return len(self.features)

    def into(self):
        return self.features


@dataclass
class FeatureStepList(beet.SupportsMerge):
    steps: list[FeatureStep]

    def __post_init__(self):
        self.steps = [
            FeatureStep(step)
            for step in self.steps
            if not isinstance(step, FeatureStep)
        ]

    def merge(self, other: "FeatureStepList") -> bool:
        length = len(self)

        if length < len(other):
            self.steps += other[len(self) :]

        for i in range(length):
            self[i].merge(other[i])

        return True

    def __getitem__(self, i: int) -> FeatureStep:
        return self.steps[i]

    def __setindex__(self, i: int, step: FeatureStep):
        self.steps[i] = step

    def __len__(self):
        return len(self.steps)

    def into(self) -> list[list[str]]:
        return [step.into() for step in self.steps]


@dataclass
class Probability(beet.SupportsMerge):
    prob: float

    def merge(self, other: "Probability") -> bool:
        self.prob = mean(self.prob, other.prob)

        return True

    def into(self) -> float:
        return self.prob


@dataclass
class MergeableFloat:
    value: float

    def merge(self, other: "MergeableFloat") -> bool:
        self.value = mean(self.value, other.value)

        return True

    def into(self) -> float:
        return self.value


biome_type_map = {
    "temperature": MergeableFloat,
    "temperature_modifier": TemperatureModifier,
    "downfall": MergeableFloat,
    "water_color": Color,
    "foliage_color": Color,
    "dry_foliage_color": Color,
    "grass_color": Color,
    "grass_color_modifier": GrassColorModifier.from_str,
    "features": FeatureStepList,
    "creature_spawn_probability": Probability,
}


def convert_types(data: dict):
    for k, v in data.items():
        if k in biome_type_map:
            data[k] = biome_type_map[k](v)
            continue

        if isinstance(v, dict):
            convert_types(v)


def data_into(data: dict):
    for k in data.keys():
        if hasattr(data[k], "into"):
            data[k] = data[k].into()
            continue

        if isinstance(data[k], dict):
            data_into(data[k])


def merge_data(a: dict, b: dict):
    for k in b.keys():
        if k not in a:
            a[k] = b[k]

        if a[k] == b[k]:
            continue

        if hasattr(a[k], "merge"):
            a[k].merge(b[k])

        if isinstance(a[k], dict) and isinstance(b[k], dict):
            merge_data(a[k], b[k])

    data_into(a)


def merge_biome(self: worldgen.WorldgenBiome, other: worldgen.WorldgenBiome) -> bool:
    convert_types(self.data)
    convert_types(other.data)

    merge_data(self.data, other.data)

    return True


worldgen.WorldgenBiome.merge = merge_biome
