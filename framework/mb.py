from html import escape


MB_BASE = "https://musicbrainz.org"


def entity_url(entity_type, mbid):
    return f"{MB_BASE}/{entity_type}/{mbid}"


def mbid_link(value, entity_type="artist"):
    value = str(value)
    return f'<a href="{entity_url(entity_type, value)}" target="_blank" rel="noopener">{escape(value)}</a>'
