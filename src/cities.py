"""Offline city list used for search suggestions.

Built from the geonamescache package, so suggestions need no API calls.
"""

from functools import lru_cache

import geonamescache

MIN_POPULATION = 50_000


@lru_cache(maxsize=1)
def city_options() -> tuple[str, ...]:
    """Return "Name, CC" labels for cities above MIN_POPULATION, largest first."""
    cities = geonamescache.GeonamesCache().get_cities().values()
    big = sorted(
        (c for c in cities if c["population"] >= MIN_POPULATION),
        key=lambda c: -c["population"],
    )
    return tuple(f"{c['name']}, {c['countrycode']}" for c in big)


def to_query(label: str) -> str:
    """Turn a "Name, CC" label into the "Name,CC" form OpenWeather expects."""
    return label.replace(", ", ",").strip()
