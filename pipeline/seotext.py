"""Longueur des titres et descriptions pour Google : au-delà d'environ 60 et 160 caractères, il les coupe dans ses résultats.
fit() prend la première version qui tient (de la plus complète à la plus courte) ; clip() coupe proprement en dernier recours."""
TITLE_MAX = 60
DESC_MAX = 155


def fit(*versions, limit=TITLE_MAX):
    """La première version qui tient dans la limite ; à défaut, la plus courte."""
    for v in versions:
        if len(v) <= limit:
            return v
    return min(versions, key=len)


def clip(text, limit=DESC_MAX):
    """Coupe à la fin d'un mot, avec des points de suspension, si le texte dépasse."""
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    cut = cut[:cut.rfind(" ")] if " " in cut else cut
    return cut.rstrip(" ,;:.") + "…"


def fit_desc(*versions, limit=DESC_MAX):
    return clip(fit(*versions, limit=limit), limit)
