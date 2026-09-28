from dataclasses import dataclass


@dataclass
class Link:
    text: str
    url: str
    new_tab: bool = True


@dataclass
class MBID:
    value: str
    entity_type: str = "artist"
    text: str | None = None


@dataclass
class LinkGroup:
    """A value with one or more links, rendered vertically in a cell."""
    items: list


def link(text, url, new_tab=True):
    return Link(text, url, new_tab)


def mbid(value, entity_type="artist", text=None):
    return MBID(str(value), entity_type, text)
