"""Icône et écran de démarrage de l'appli (proposition « A · Nuit » : le h sable sur fond nuit), tirés du logo fourni
(web/brand/symbol.png et lockup.png, produits par tools.trace_logo). Écrit dans app/assets/.
Usage : python -m tools.app_icons"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BRAND, OUT = ROOT / "web" / "brand", ROOT / "app" / "assets"
NIGHT, SAND, WHITE = (10, 17, 20), (233, 198, 148), (255, 255, 255)


def stamp(canvas, src, width, color, dy=0):
    """Pose le logo (sa transparence seule) en `color`, centré, à la largeur `width`."""
    a = Image.open(BRAND / src).convert("RGBA").split()[3]
    a = a.point(lambda v: 0 if v < 12 else v)   # le PNG du logo a un voile presque transparent (alpha 1-11) qui dessinait un carré
    h = round(width * a.height / a.width)
    a = a.resize((width, h), Image.LANCZOS)
    canvas.paste(Image.new("RGBA", (width, h), color + (255,)), ((canvas.width - width) // 2, (canvas.height - h) // 2 + dy), a)
    return canvas


def main():
    S = 1024
    # iPhone : carré plein (iOS arrondit lui-même les coins), le h sur 62 % de la largeur, un peu remonté pour l'équilibre optique
    stamp(Image.new("RGBA", (S, S), NIGHT + (255,)), "symbol.png", round(S * 0.62), SAND, dy=-12).convert("RGB").save(OUT / "icon.png")
    # Android : fond et dessin séparés ; le dessin reste dans le cercle central (66 %) que tous les téléphones gardent
    Image.new("RGB", (S, S), NIGHT).save(OUT / "android-icon-background.png")
    stamp(Image.new("RGBA", (S, S), (0, 0, 0, 0)), "symbol.png", round(S * 0.48), SAND, dy=-8).save(OUT / "android-icon-foreground.png")
    stamp(Image.new("RGBA", (S, S), (0, 0, 0, 0)), "symbol.png", round(S * 0.48), WHITE, dy=-8).save(OUT / "android-icon-monochrome.png")
    # Écran de démarrage : le h et le mot « houlalah », sur fond transparent (la couleur de fond est réglée dans app.json)
    stamp(Image.new("RGBA", (1200, 830), (0, 0, 0, 0)), "lockup.png", 1006, SAND).save(OUT / "splash-icon.png")
    # Onglet du navigateur (version web de l'appli)
    stamp(Image.new("RGBA", (196, 196), NIGHT + (255,)), "symbol.png", 122, SAND, dy=-2).resize((48, 48), Image.LANCZOS).save(OUT / "favicon.png")
    print("OK", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
