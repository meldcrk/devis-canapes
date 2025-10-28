# -*- coding: utf-8 -*-
# canape_complet_v6_palette_legende_U.py
# Base validée + ajouts :
#   - Choix des couleurs par noms FR (gris, beige, gris foncé/foncée, taupe, crème, etc.) ou #hex
#   - Préréglage demandé : accoudoirs=gris ; dossiers=gris (plus clair) ;
#                          assises=gris très clair (presque blanc) ; coussins=taupe
#   - Dossiers automatiquement un ton plus clair que accoudoirs si non précisé
#   - Légende "U" déplacée en haut-centré (hors canapé) ; autres : haut-droite
#   - Légende affiche la couleur choisie ("Dossier (gris clair)", etc.)
#   - Correctifs nommage 'coussins_count' -> 'cushions_count'

import turtle, math, unicodedata

# =========================
# Réglages / constantes
# =========================
WIN_W, WIN_H       = 900, 700
PAD_PX             = 60
ZOOM               = 0.85
LINE_WIDTH         = 2

# ========= PALETTE / THÈME =========
# Couleurs par défaut, selon la demande :
# - accoudoirs = gris (moyen)
# - dossiers = gris (un ton plus clair)
# - assises/banquettes = gris très clair (presque blanc)
# - coussins = taupe
# NB : Ces valeurs seront éventuellement écrasées à chaque render_* via _resolve_and_apply_colors()
COLOR_ASSISE       = "#f6f6f6"  # gris très clair / presque blanc
COLOR_ACC          = "#8f8f8f"  # gris
COLOR_DOSSIER      = "#b8b8b8"  # gris plus clair que accoudoirs
COLOR_CUSHION      = "#8B7E74"  # taupe
COLOR_CONTOUR      = "black"

# (Conservés mais non utilisés car quadrillage/repères supprimés)
GRID_MINOR_STEP    = 10
GRID_MAJOR_STEP    = 50
COLOR_GRID_MINOR   = "#f0f0f0"
COLOR_GRID_MAJOR   = "#dcdcdc"
AXIS_LABEL_STEP    = 50
AXIS_LABEL_MAX     = 800

DEPTH_STD          = 70
ACCOUDOIR_THICK    = 15
DOSSIER_THICK      = 10
CUSHION_DEPTH      = 15

# *** Seuil strict de scission ***
MAX_BANQUETTE      = 250
SPLIT_THRESHOLD    = 250  # scission dès que longueur > 250 (aucune tolérance)

# --- Coins arrondis coussins ---
CUSHION_ROUND_R_CM = 3.0  # rayon ~3 cm, léger

# --- Traversins (bolsters) ---
TRAVERSIN_LEN   = 70     # longueur selon la profondeur
TRAVERSIN_THK   = 30     # retrait sur la ligne de coussins
COLOR_TRAVERSIN = "#e0d9c7"

# --- Polices / légende / titres (lisibilité accrue) ---
FONT_LABEL      = ("Arial", 12, "bold")   # libellés banquettes/dossiers/accoudoirs
FONT_CUSHION    = ("Arial", 11, "bold")   # tailles des coussins + "70x30"
FONT_DIM        = ("Arial", 12, "bold")   # flèches d’encombrement
FONT_LEGEND     = ("Arial", 12, "normal") # texte de légende
FONT_TITLE      = ("Arial", 14, "bold")   # titre "Canapé en U …"
LEGEND_BOX_PX   = 14
LEGEND_GAP_PX   = 6
TITLE_MARGIN_PX = 28  # marge sous le bord haut du dessin

# =============================================================================
# ================     OUTILS PALETTE / COULEURS (NOUVEAU)     ================
# =============================================================================

# Palette de base (nuanciers simples)
_BASE_COLORS = {
    "gris":   "#9e9e9e",
    "beige":  "#d8c4a8",
    "taupe":  "#8B7E74",
    "crème":  "#f4f1e9",
    "creme":  "#f4f1e9",
    "blanc":  "#ffffff",
    "noir":   "#111111",
    "sable":  "#e6d8b8",
    "anthracite": "#4b4b4b",
}

# Helpers accents/normalisation
def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = _strip_accents(s)
    return ' '.join(s.split())

def _clamp(x, lo=0, hi=255):
    return int(max(lo, min(hi, round(x))))

def _hex_to_rgb(h):
    h = h.strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) == 3:
        h = ''.join([c*2 for c in h])
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def _lighten(hexcol, factor):
    """factor in [0,1] vers blanc; 0 = identique; 1 = blanc complet."""
    r,g,b = _hex_to_rgb(hexcol)
    r = _clamp(r + (255-r)*factor)
    g = _clamp(g + (255-g)*factor)
    b = _clamp(b + (255-b)*factor)
    return _rgb_to_hex((r,g,b))

def _darken(hexcol, factor):
    """factor in [0,1] vers noir; 0 = identique; 1 = noir complet."""
    r,g,b = _hex_to_rgb(hexcol)
    r = _clamp(r*(1-factor))
    g = _clamp(g*(1-factor))
    b = _clamp(b*(1-factor))
    return _rgb_to_hex((r,g,b))

def _apply_shade(hexcol, tokens):
    """
    tokens: contient éventuellement 'clair', 'tres clair', 'fonce', 'tres fonce', 'presque blanc'
    """
    t = ' '.join(tokens)
    t_norm = _norm(t)
    if "presque blanc" in t_norm:
        return _lighten(hexcol, 0.75)
    if "tres clair" in t_norm:
        return _lighten(hexcol, 0.40)
    if "clair" in t_norm:
        return _lighten(hexcol, 0.22)
    if "tres fonce" in t_norm:
        return _darken(hexcol, 0.40)
    if "fonce" in t_norm or "foncee" in t_norm:
        return _darken(hexcol, 0.22)
    return hexcol

def _pretty_shade(tokens):
    t = _norm(' '.join(tokens))
    t = t.replace("tres", "très")
    t = t.replace("fonce", "foncé")
    return t

def _parse_color_value(val):
    """
    Convertit un nom FR (évent. qualifié) ou un #hex en (#hex, nom jolis mots ou None)
    Ex : "gris foncé" -> (#..., "gris foncé")
         "#c0ffee"    -> ("#c0ffee", None)
    """
    if val is None:
        return None, None
    s_raw = str(val).strip()
    s = _norm(s_raw)

    # cas hex
    if s.startswith("#") or all(c in "0123456789abcdef" for c in s.replace("#","")) and len(s.replace("#","")) in (3,6):
        try:
            _ = _hex_to_rgb(s)
            if not s.startswith("#"): s = "#" + s
            return s, None
        except Exception:
            pass

    # cherche base connue
    tokens = s.split()
    if not tokens:
        return None, None

    # base candidates (un ou deux mots, ex "gris", "blanc", "beige", "taupe")
    base = tokens[0]
    base_hex = _BASE_COLORS.get(base)
    if base_hex is None and len(tokens)>=2:
        # ex: "gris clair" = base "gris" + shade "clair"
        base_hex = _BASE_COLORS.get(tokens[0])
    if base_hex is None:
        # fallback : gris
        base_hex = _BASE_COLORS["gris"]; base = "gris"

    shade = tokens[1:] if len(tokens)>1 else []
    hexcol = _apply_shade(base_hex, shade)
    pretty = base
    if shade:
        pretty += " " + _pretty_shade(shade)
    return hexcol, pretty

def _parse_couleurs_argument(couleurs):
    """
    Accepte dict, ou string "clé:val; clé:val".
    Normalise les clés en {'accoudoirs','dossiers','assise','coussins'}
    """
    if couleurs is None:
        return {}

    if isinstance(couleurs, dict):
        raw = { _norm(k): str(v) for k,v in couleurs.items() }
    else:
        raw = {}
        for part in str(couleurs).split(";"):
            if ":" in part:
                k,v = part.split(":",1)
                raw[_norm(k)] = v.strip()

    keymap = {
        "accoudoir":"accoudoirs", "accoudoirs":"accoudoirs",
        "dossier":"dossiers", "dossiers":"dossiers",
        "assise":"assise", "assises":"assise", "banquette":"assise", "banquettes":"assise",
        "coussin":"coussins", "coussins":"coussins"
    }
    res={}
    for k,v in raw.items():
        kn = keymap.get(k, k)
        if kn in ("accoudoirs","dossiers","assise","coussins"):
            res[kn] = v
    return res

def _resolve_and_apply_colors(couleurs):
    """
    Résout la palette utilisateur puis applique aux variables globales:
      COLOR_ASSISE, COLOR_ACC, COLOR_DOSSIER, COLOR_CUSHION
    Retourne une liste d'items pour la légende: [(libellé, hex, nom)]
    Règle : si dossiers non spécifié mais accoudoirs oui => dossiers = accoudoirs éclaircis.
    """
    global COLOR_ASSISE, COLOR_ACC, COLOR_DOSSIER, COLOR_CUSHION

    # base par défaut (demande client)
    default = {
        "accoudoirs": "gris",
        "dossiers":   None,  # sera éclairci à partir des accoudoirs si None
        "assise":     "gris très clair presque blanc",
        "coussins":   "taupe",
    }
    user = _parse_couleurs_argument(couleurs)
    spec = {**default, **user}

    # accoudoirs
    acc_hex, acc_name = _parse_color_value(spec["accoudoirs"])
    # dossiers
    if spec["dossiers"] is None:
        # auto : un ton plus clair que accoudoirs
        dos_hex = _lighten(acc_hex, 0.20)
        dos_name = (acc_name+" clair") if acc_name else "gris clair"
    else:
        dos_hex, dos_name = _parse_color_value(spec["dossiers"])
    # assise
    ass_hex, ass_name = _parse_color_value(spec["assise"])
    # coussins
    cush_hex, cush_name = _parse_color_value(spec["coussins"])

    # applique globals
    COLOR_ACC     = acc_hex
    COLOR_DOSSIER = dos_hex
    COLOR_ASSISE  = ass_hex
    COLOR_CUSHION = cush_hex

    # Items de légende (texte + nom de couleur si dispo)
    items = [
        ("Dossier",   COLOR_DOSSIER, dos_name),
        ("Accoudoir", COLOR_ACC,     acc_name),
        ("Coussins",  COLOR_CUSHION, cush_name),
        ("Assise",    COLOR_ASSISE,  ass_name),
    ]
    return items

# =========================
# Transform cm → px (isométrique & centré)
# =========================
class WorldToScreen:
    def __init__(self, tx_cm, ty_cm, win_w=WIN_W, win_h=WIN_H, pad_px=PAD_PX, zoom=ZOOM):
        sx = (win_w - 2*pad_px) / float(tx_cm or 1)
        sy = (win_h - 2*pad_px) / float(ty_cm or 1)
        self.scale = min(sx, sy) * zoom
        used_w = tx_cm * self.scale
        used_h = ty_cm * self.scale
        self.left_px   = -used_w / 2.0
        self.bottom_px = -used_h / 2.0
    def pt(self, x_cm, y_cm):
        return (self.left_px + x_cm*self.scale, self.bottom_px + y_cm*self.scale)

# =========================
# Outils dessin
# =========================
def pen_up_to(t, x, y):
    t.up(); t.goto(x, y)

def _is_axis_aligned_rect(pts):
    """Détecte un rectangle axis‑aligné fermé (le dernier point répète le premier)."""
    if not pts or len(pts) < 4:
        return False
    body = pts[:-1] if pts[0] == pts[-1] else pts
    if len(body) != 4:
        return False
    xs = {round(x, 6) for x, _ in body}
    ys = {round(y, 6) for _, y in body}
    return len(xs) == 2 and len(ys) == 2

def draw_rounded_rect_cm(t, tr, x0, y0, x1, y1, r_cm=CUSHION_ROUND_R_CM,
                         fill=None, outline=COLOR_CONTOUR, width=LINE_WIDTH):
    # normalise
    if x0 > x1: x0, x1 = x1, x0
    if y0 > y1: y0, y1 = y1, y0
    rx = max(0.0, min(r_cm, (x1-x0)/2.0, (y1-y0)/2.0))
    wpx = (x1 - x0) * tr.scale
    hpx = (y1 - y0) * tr.scale
    rpx = rx * tr.scale
    sx, sy = tr.pt(x0 + rx, y0)

    t.pensize(width)
    t.pencolor(outline)
    pen_up_to(t, sx, sy)
    if fill:
        t.fillcolor(fill)
        t.begin_fill()
    t.setheading(0)
    t.down()
    for _ in range(2):
        t.forward(max(0.0, wpx - 2*rpx)); t.circle(rpx, 90)
        t.forward(max(0.0, hpx - 2*rpx)); t.circle(rpx, 90)
    t.up()
    if fill:
        t.end_fill()

def draw_polygon_cm(t, tr, pts, fill=None, outline=COLOR_CONTOUR, width=LINE_WIDTH):
    if not pts: return
    # Arrondi auto pour coussins rectangulaires axis‑alignés
    if fill == COLOR_CUSHION and _is_axis_aligned_rect(pts):
        xs = [x for x, _ in pts[:-1]] if pts[0] == pts[-1] else [x for x, _ in pts]
        ys = [y for _, y in pts[:-1]] if pts[0] == pts[-1] else [y for _, y in pts]
        x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
        draw_rounded_rect_cm(t, tr, x0, y0, x1, y1, r_cm=CUSHION_ROUND_R_CM,
                             fill=fill, outline=outline, width=width)
        return
    # Fallback polygonal
    t.pensize(width); t.pencolor(outline)
    x0, y0 = tr.pt(*pts[0]); pen_up_to(t, x0, y0)
    if fill: t.fillcolor(fill); t.begin_fill()
    t.down()
    for x, y in pts[1:]:
        t.goto(*tr.pt(x, y))
    t.goto(x0, y0)
    if fill: t.end_fill()
    t.up()

# (Quadrillage & repères supprimés à la demande client → fonctions conservées mais non appelées)
def draw_grid_cm(t, tr, tx, ty, step, color, width):  # non utilisé
    pass

def draw_axis_labels_cm(t, tr, tx, ty, step=AXIS_LABEL_STEP, max_mark=AXIS_LABEL_MAX):  # non utilisé
    pass

def _unit(vx, vy):
    n = math.hypot(vx, vy)
    return (vx/n, vy/n) if n else (0, 0)

def draw_double_arrow_px(t, p1, p2, text=None, text_perp_offset_px=0, text_tang_shift_px=0):
    t.pensize(1.5); t.pencolor("black")
    pen_up_to(t, *p1); t.down(); t.goto(*p2); t.up()
    vx, vy = (p2[0]-p1[0], p2[1]-p1[1]); ux, uy = _unit(vx, vy); px, py = -uy, ux
    ah, spread = 12, 5
    for base, sgn in [(p1, +1), (p2, -1)]:
        a = (base[0] + ux*ah*sgn + px*spread, base[1] + uy*ah*sgn + py*spread)
        b = (base[0] + ux*ah*sgn - px*spread, base[1] + uy*ah*sgn - py*spread)
        pen_up_to(t, *base); t.down(); t.goto(*a); t.up()
        pen_up_to(t, *base); t.down(); t.goto(*b); t.up()
    if text:
        cx, cy = ((p1[0]+p2[0])/2.0, (p1[1]+p2[1])/2.0)
        tx = cx + px*text_perp_offset_px + ux*text_tang_shift_px
        ty = cy + py*text_perp_offset_px + uy*text_tang_shift_px
        pen_up_to(t, tx, ty); t.write(text, align="center", font=FONT_DIM)

def draw_double_arrow_vertical_cm(t, tr, x_cm, y0_cm, y1_cm, label):
    draw_double_arrow_px(t, tr.pt(x_cm, y0_cm), tr.pt(x_cm, y1_cm), text=label, text_perp_offset_px=+12)

def draw_double_arrow_horizontal_cm(t, tr, y_cm, x0_cm, x1_cm, label):
    draw_double_arrow_px(t, tr.pt(x0_cm, y_cm), tr.pt(x1_cm, y_cm), text=label,
                         text_perp_offset_px=-12, text_tang_shift_px=20)

def centroid(poly):
    return (sum(x for x,y in poly)/len(poly), sum(y for x,y in poly)/len(poly))

def label_poly(t, tr, poly, text, font=FONT_LABEL):
    cx, cy = centroid(poly); pen_up_to(t, *tr.pt(cx, cy))
    t.write(text, align="center", font=font)

def label_poly_offset_cm(t, tr, poly, text, dx_cm=0.0, dy_cm=0.0, font=FONT_LABEL):
    cx, cy = centroid(poly); x, y = tr.pt(cx + dx_cm, cy + dy_cm)
    pen_up_to(t, x, y); t.write(text, align="center", font=font)

def banquette_dims(poly):
    xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
    L=max(max(xs)-min(xs), max(ys)-min(ys)); P=min(max(xs)-min(xs), max(ys)-min(ys))
    return int(round(L)), int(round(P))

def _split_mid_int(a, b):
    delta = b - a; L = abs(delta); left = L // 2
    return a + (left if delta >= 0 else -left)

def _rectU(x0, y0, x1, y1):
    return [(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)]

def _poly_has_area(p):
    if not p or len(p) < 4: return False
    xs=[x for x,y in p]; ys=[y for x,y in p]
    return (max(xs)-min(xs) > 1e-9) and (max(ys)-min(ys) > 1e-9)

def _assert_banquettes_max_250(polys):
    for poly in polys.get("banquettes", []):
        L, P = banquette_dims(poly)
        if L > MAX_BANQUETTE:
            raise ValueError(f"Banquette de {L}×{P} cm > {MAX_BANQUETTE} cm — scission supplémentaire nécessaire.")

# =====================================================================
# ================  Outils légende & titres (lisibilité)  =============
# =====================================================================

def _draw_rect_px(t, x, y, w, h, fill=None, outline=COLOR_CONTOUR, width=1):
    t.pensize(width); t.pencolor(outline)
    pen_up_to(t, x, y)
    if fill:
        t.fillcolor(fill); t.begin_fill()
    t.setheading(0); t.down()
    for _ in range(2):
        t.forward(w); t.left(90); t.forward(h); t.left(90)
    t.up()
    if fill:
        t.end_fill()

def _wrap_text(text, max_len=28):
    words = str(text).split()
    if not words: return [""]
    lines=[]; cur=words[0]
    for w in words[1:]:
        if len(cur)+1+len(w) <= max_len:
            cur += " " + w
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines

def draw_title_center(t, tr, tx_cm, ty_cm, text):
    """Titre centré en haut de la scène, à l’intérieur de l’espace visible."""
    left = tr.left_px; bottom = tr.bottom_px
    right = left + tx_cm*tr.scale; top = bottom + ty_cm*tr.scale
    cx = (left + right)/2.0
    y  = top - TITLE_MARGIN_PX
    lines = _wrap_text(text, max_len=34)
    for i, line in enumerate(lines):
        pen_up_to(t, cx, y - i*18)
        t.write(line, align="center", font=FONT_TITLE)

def draw_legend(t, tr, tx_cm, ty_cm, items=None, pos="top-right"):
    """
    Légende avec items = [(label, hex, name), ...]
      - pos: "top-right" (par défaut) ou "top-center" (pour U afin d'éviter recouvrement)
    """
    left = tr.left_px; bottom = tr.bottom_px
    right = left + tx_cm*tr.scale; top = bottom + ty_cm*tr.scale

    # Items / couleurs
    if not items:
        items = [
            ("Dossier",   COLOR_DOSSIER, None),
            ("Accoudoir", COLOR_ACC,     None),
            ("Coussins",  COLOR_CUSHION, None),
            ("Assise",    COLOR_ASSISE,  None),
        ]
    # Taille & position
    box = LEGEND_BOX_PX; gap = LEGEND_GAP_PX
    # largeur texte (un peu plus pour nom de teinte)
    max_text_w_px = 220
    total_h = len(items)*(box) + (len(items)-1)*gap
    total_w = box + 8 + max_text_w_px

    if pos == "top-center":
        cx = (left + right) / 2.0
        x0 = cx - total_w/2.0
        y0 = top - 12
    else:  # top-right
        x0 = right - total_w - 12
        y0 = top - 12

    # Fond (léger)
    _draw_rect_px(t, x0-8, y0 - total_h - 8, total_w+16, total_h+16, fill="#ffffff", outline="#aaaaaa", width=1)

    # Lignes
    cur_y = y0 - box
    for label, col, name in items:
        _draw_rect_px(t, x0, cur_y, box, box, fill=col, outline=COLOR_CONTOUR, width=1)
        pen_up_to(t, x0 + box + 8, cur_y + box/2 - 6)
        lbl = f"{label}" + ("" if not name else f" ({name})")
        t.write(lbl, align="left", font=FONT_LEGEND)
        cur_y -= (box + gap)

# =====================================================================
# ================  COUSSINS — utilitaires limites méridienne =========
# =====================================================================

def _lim_x(pts, key):
    """Récupère x d’extrémité pour dessin coussins : supporte <key>, <key>_mer et <key>_."""
    if f"{key}_mer" in pts: return pts[f"{key}_mer"][0]
    if f"{key}_"   in pts: return pts[f"{key}_"][0]
    return pts[key][0]

def _lim_y(pts, key):
    """Récupère y d’extrémité pour dessin coussins : supporte <key>, <key>_mer et <key>_."""
    if f"{key}_mer" in pts: return pts[f"{key}_mer"][1]
    if f"{key}_"   in pts: return pts[f"{key}_"][1]
    return pts[key][1]

# =====================================================================
# ================  COUSSINS — moteur "valise" (utilitaires)  =========
# =====================================================================

def _parse_coussins_spec(coussins):
    """
    Retourne un dict :
      - mode: "auto" | "fixed" | "valise"
      - fixed: int (si mode=fixed)
      - range: (min,max)  (si mode=valise)
      - same: bool        (si mode=valise, 'same' pour :s)
    Règles:
      auto          -> ancien auto (65,80,90)
      entier        -> taille globale fixe (toutes branches)
      valise        -> 60..100,  Δ global ≤ 5
      p             -> 60..74,   Δ global ≤ 5
      g             -> 76..100,  Δ global ≤ 5
      s             -> same global, 60..100
      p:s           -> same global, 60..74
      g:s           -> same global, 76..100
    """
    if isinstance(coussins, int):
        return {"mode":"fixed", "fixed": int(coussins)}
    s = str(coussins).strip().lower()
    if s == "auto":
        return {"mode":"auto"}
    if s.isdigit():
        return {"mode":"fixed", "fixed": int(s)}
    same = (":s" in s) or (s == "s")
    base = s.replace(":s", "")
    if base == "s":
        base = "valise"
    if base not in ("valise", "p", "g"):
        raise ValueError(f"Spécification coussins invalide: {coussins}")
    if base == "p":
        r = (60, 74)
    elif base == "g":
        r = (76, 100)
    else:
        r = (60, 100)
    return {"mode":"valise", "range": r, "same": bool(same)}

def _parse_traversins_spec(traversins, allowed={"g","b","d"}):
    """
    Renvoie un set parmi {'g','b','d'} selon la demande utilisateur.
    - traversins peut être None, 'g', 'd', 'b', 'g,d', ['g','d'], ...
    - allowed restreint selon le type de canapé.
    """
    if not traversins:
        return set()
    if isinstance(traversins, (list, tuple, set)):
        raw = {str(x).strip().lower() for x in traversins}
    else:
        raw = {p.strip().lower() for p in str(traversins).replace(";", ",").split(",") if p.strip()}
    return raw & set(allowed)

def _waste_and_count_1d(length, size):
    """Retourne (count, waste) pour un segment 1D de longueur 'length' avec modules de 'size'."""
    if length <= 0 or size <= 0:
        return 0, max(0, length)
    n = int(length // size)
    waste = length - n*size
    return n, waste

# ----- Traversins : dessin -----
def _draw_traversin_block(t, tr, x0, y0, x1, y1):
    draw_rounded_rect_cm(t, tr, x0, y0, x1, y1,
                         r_cm=CUSHION_ROUND_R_CM,
                         fill=COLOR_TRAVERSIN, outline=COLOR_CONTOUR, width=1)
    cx, cy = (x0+x1)/2.0, (y0+y1)/2.0
    pen_up_to(t, *tr.pt(cx, cy))
    t.write("70x30", align="center", font=FONT_CUSHION)

# ----- L-like / U / S1 : placement traversins -----
def _draw_traversins_simple_S1(t, tr, pts, profondeur, dossier, traversins):
    if not traversins: return 0
    y_base = DOSSIER_THICK if dossier else 0
    usable_h = max(0.0, profondeur - y_base)
    y0 = y_base + max(0.0, (usable_h - TRAVERSIN_LEN)/2.0)
    y1 = y0 + min(TRAVERSIN_LEN, usable_h)

    n = 0
    if "g" in traversins:
        x0 = pts["B0"][0]; x1 = x0 + TRAVERSIN_THK
        _draw_traversin_block(t, tr, x0, y0, x1, y1); n += 1
    if "d" in traversins:
        x1 = pts["Bx"][0]; x0 = x1 - TRAVERSIN_THK
        _draw_traversin_block(t, tr, x0, y0, x1, y1); n += 1
    return n

def _draw_traversins_L_like(t, tr, pts, profondeur, traversins):
    if not traversins: return 0
    F0x, F0y = pts["F0"]
    depth_len = min(TRAVERSIN_LEN, max(0.0, profondeur))

    n = 0
    # gauche (horizontal)
    if "g" in traversins:
        y_end = _lim_y(pts, "By")
        y0 = y_end - TRAVERSIN_THK; y1 = y_end
        _draw_traversin_block(t, tr, F0x, y0, F0x + depth_len, y1); n += 1
    # bas (vertical)
    if "b" in traversins:
        x_end = _lim_x(pts, "Bx")
        x0 = x_end - TRAVERSIN_THK; x1 = x_end
        _draw_traversin_block(t, tr, x0, F0y, x1, F0y + depth_len); n += 1
    return n

def _u_right_col_x(variant, pts):
    return pts["Bx"][0] if variant in ("v1","v4") else pts["F02"][0]

def _draw_traversins_U_common(t, tr, variant, pts, profondeur, traversins):
    if not traversins: return 0
    F0x, F0y = pts["F0"]
    depth_len = min(TRAVERSIN_LEN, max(0.0, profondeur))

    n = 0
    if "g" in traversins:
        y_end_L = _lim_y(pts, "By")
        y0 = y_end_L - TRAVERSIN_THK; y1 = y_end_L
        _draw_traversin_block(t, tr, F0x, y0, F0x + depth_len, y1); n += 1
    if "d" in traversins:
        xr = _u_right_col_x(variant, pts)
        y_end_R = _lim_y(pts, "By4")
        y0 = y_end_R - TRAVERSIN_THK; y1 = y_end_R
        _draw_traversin_block(t, tr, xr - depth_len, y0, xr, y1); n += 1
    return n

def _draw_traversins_U_side_F02(t, tr, pts, profondeur, traversins):
    if not traversins: return 0
    F0x, F0y = pts["F0"]; F02x = pts["F02"][0]
    depth_len = min(TRAVERSIN_LEN, max(0.0, profondeur))

    n = 0
    if "g" in traversins:
        y_end_L = _lim_y(pts, "By")
        y0 = y_end_L - TRAVERSIN_THK; y1 = y_end_L
        _draw_traversin_block(t, tr, F0x, y0, F0x + depth_len, y1); n += 1
    if "d" in traversins:
        y_end_R = _lim_y(pts, "By4")
        y0 = y_end_R - TRAVERSIN_THK; y1 = y_end_R
        _draw_traversin_block(t, tr, F02x - depth_len, y0, F02x, y1); n += 1
    return n

# =====================================================================
# ================  COUSSINS — moteur "valise" (utilitaires)  =========
# =====================================================================

def _apply_traversin_limits_L_like(pts, x_end_key, y_end_key, traversins):
    x_end = _lim_x(pts, x_end_key); y_end = _lim_y(pts, y_end_key)
    if traversins:
        if "b" in traversins: x_end -= TRAVERSIN_THK
        if "g" in traversins: y_end -= TRAVERSIN_THK
    return x_end, y_end

def _eval_L_like_counts(pts, size_bas, size_g, shift_bas, x_end_key="Bx", y_end_key="By", traversins=None):
    F0x, F0y = pts["F0"]
    x_end, y_end = _apply_traversin_limits_L_like(pts, x_end_key, y_end_key, traversins)

    xs = F0x + (CUSHION_DEPTH if shift_bas else 0)
    xe = x_end
    y0 = F0y + (0 if shift_bas else CUSHION_DEPTH)
    ye = y_end

    len_b = max(0, xe - xs)
    len_g = max(0, ye - y0)

    nb_b, wb = _waste_and_count_1d(len_b, size_bas)
    nb_g, wg = _waste_and_count_1d(len_g, size_g)
    waste_tot = wb + wg
    cover = nb_b*size_bas + nb_g*size_g
    return {
        "counts": {"bas": nb_b, "gauche": nb_g},
        "waste": waste_tot,
        "cover": cover,
        "geom": {"xs": xs, "xe": xe, "y0": y0, "ye": ye}
    }

def _optimize_valise_L_like(pts, rng, same, x_end_key="Bx", y_end_key="By", traversins=None):
    best = None
    r0, r1 = rng
    for size_g in range(r0, r1+1):
        cand_b = [size_g] if same else range(r0, r1+1)
        for size_b in cand_b:
            if abs(size_b - size_g) > 5:
                continue
            eval_A = _eval_L_like_counts(pts, size_b, size_g, shift_bas=False, x_end_key=x_end_key, y_end_key=y_end_key, traversins=traversins)
            eval_B = _eval_L_like_counts(pts, size_b, size_g, shift_bas=True,  x_end_key=x_end_key, y_end_key=y_end_key, traversins=traversins)
            e = min([eval_A, eval_B], key=lambda E: (E["waste"], -E["cover"], -size_b, -size_g))
            score = (e["waste"], -e["cover"], -size_b, -size_g)
            if (best is None) or (score < best["score"]):
                best = {"score": score, "sizes": {"bas": size_b, "gauche": size_g}, "eval": e,
                        "shift_bas": (e is eval_B)}
    return best

def _draw_L_like_with_sizes(t, tr, pts, sizes, shift_bas, x_end_key="Bx", y_end_key="By", traversins=None):
    F0x, F0y = pts["F0"]
    x_end, y_end = _apply_traversin_limits_L_like(pts, x_end_key, y_end_key, traversins)

    # bas
    xs = F0x + (CUSHION_DEPTH if shift_bas else 0)
    xe = x_end; yb = F0y
    nb = 0; x = xs
    sb = sizes["bas"]
    while x + sb <= xe + 1e-6:
        poly = [(x,yb), (x+sb,yb), (x+sb,yb+CUSHION_DEPTH), (x,yb+CUSHION_DEPTH), (x,yb)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{sb}", font=FONT_CUSHION)
        x += sb; nb += 1

    # gauche
    yg0 = F0y + (0 if shift_bas else CUSHION_DEPTH)
    yg1 = y_end; xg = F0x
    ng = 0; y = yg0
    sg = sizes["gauche"]
    while y + sg <= yg1 + 1e-6:
        poly = [(xg,y), (xg+CUSHION_DEPTH,y), (xg+CUSHION_DEPTH,y+sg), (xg,y+sg), (xg,y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{sg}", font=FONT_CUSHION)
        y += sg; ng += 1

    return nb + ng, sb, sg

# ----- U2f : évaluation / dessin -----
def _eval_U2f_counts(pts, sb, sg, sd, shiftL, shiftR, traversins=None):
    F0x, F0y = pts["F0"]
    F02x = pts["F02"][0]
    y_end_L = pts.get("By_", pts["By"])[1]
    y_end_R = pts.get("By4_", pts["By4"])[1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK

    xs = F0x + (CUSHION_DEPTH if shiftL else 0)
    xe = F02x - (CUSHION_DEPTH if shiftR else 0)
    yL0 = F0y + (0 if shiftL else CUSHION_DEPTH)
    yR0 = F0y + (0 if shiftR else CUSHION_DEPTH)

    len_b = max(0, xe - xs)
    len_g = max(0, y_end_L - yL0)
    len_d = max(0, y_end_R - yR0)

    nb, wb = _waste_and_count_1d(len_b, sb)
    ng, wg = _waste_and_count_1d(len_g, sg)
    nd, wd = _waste_and_count_1d(len_d, sd)
    waste = wb + wg + wd
    cover = nb*sb + ng*sg + nd*sd
    return {"counts": {"bas": nb, "gauche": ng, "droite": nd},
            "waste": waste, "cover": cover,
            "geom": {"xs": xs, "xe": xe, "yL0": yL0, "yR0": yR0}}

def _optimize_valise_U2f(pts, rng, same, traversins=None):
    best=None; r0,r1=rng
    for sg in range(r0, r1+1):
        cand_b = [sg] if same else range(r0, r1+1)
        for sb in cand_b:
            cand_d = [sg] if same else range(r0, r1+1)
            for sd in cand_d:
                if max(sb, sg, sd) - min(sb, sg, sd) > 5:
                    continue
                E = []
                for sl in (False, True):
                    for sr in (False, True):
                        E.append(_eval_U2f_counts(pts, sb, sg, sd, sl, sr, traversins=traversins))
                e = min(E, key=lambda x: (x["waste"], -x["cover"], -sb, -sg, -sd))
                score = (e["waste"], -e["cover"], -sb, -sg, -sd)
                if (best is None) or (score < best["score"]):
                    best = {"score": score, "sizes": {"bas": sb, "gauche": sg, "droite": sd}, "eval": e}
    if best:
        chosen = best["eval"]
        for sl in (False, True):
            for sr in (False, True):
                chk = _eval_U2f_counts(pts, best["sizes"]["bas"], best["sizes"]["gauche"], best["sizes"]["droite"], sl, sr, traversins=traversins)
                if abs(chk["waste"] - chosen["waste"])<1e-9 and chk["cover"]==chosen["cover"]:
                    best["shiftL"], best["shiftR"] = sl, sr
                    return best
    return best

def _draw_U2f_with_sizes(t, tr, pts, sizes, shiftL, shiftR, traversins=None):
    F0x, F0y = pts["F0"]
    F02x = pts["F02"][0]
    y_end_L = pts.get("By_", pts["By"])[1]
    y_end_R = pts.get("By4_", pts["By4"])[1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK

    # Bas
    xs = F0x + (CUSHION_DEPTH if shiftL else 0)
    xe = F02x - (CUSHION_DEPTH if shiftR else 0)
    yb = F0y; sb = sizes["bas"]; nb=0; x=xs
    while x + sb <= xe + 1e-6:
        poly=[(x,yb),(x+sb,yb),(x+sb,yb+CUSHION_DEPTH),(x,yb+CUSHION_DEPTH),(x,yb)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sb}",font=FONT_CUSHION)
        x+=sb; nb+=1

    # Gauche
    yL0 = F0y + (0 if shiftL else CUSHION_DEPTH)
    xg = F0x; sg = sizes["gauche"]; ng=0; y=yL0
    while y + sg <= y_end_L + 1e-6:
        poly=[(xg,y),(xg+CUSHION_DEPTH,y),(xg+CUSHION_DEPTH,y+sg),(xg,y+sg),(xg,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sg}",font=FONT_CUSHION)
        y+=sg; ng+=1

    # Droite
    yR0 = F0y + (0 if shiftR else CUSHION_DEPTH)
    xr = F02x; sd = sizes["droite"]; nd=0; y=yR0
    while y + sd <= y_end_R + 1e-6:
        poly=[(xr-CUSHION_DEPTH,y),(xr,y),(xr,y+sd),(xr-CUSHION_DEPTH,y+sd),(xr-CUSHION_DEPTH,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sd}",font=FONT_CUSHION)
        y+=sd; nd+=1

    return nb+ng+nd

def _draw_cushions_U2f_optimized(t, tr, pts, size, traversins=None):
    F0x, F0y = pts["F0"]
    F02x = pts["F02"][0]
    y_end_L = pts.get("By_", pts["By"])[1]
    y_end_R = pts.get("By4_", pts["By4"])[1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK

    def cnt_h(x0, x1):
        return int(max(0, x1-x0) // size)
    def cnt_v(y0, y1):
        return int(max(0, y1-y0) // size)

    def score(shift_left, shift_right):
        xs = F0x + (CUSHION_DEPTH if shift_left else 0)
        xe = F02x - (CUSHION_DEPTH if shift_right else 0)
        bas = cnt_h(xs, xe)
        yL0 = F0y + (0 if shift_left else CUSHION_DEPTH)
        yR0 = F0y + (0 if shift_right else CUSHION_DEPTH)
        g = cnt_v(yL0, y_end_L)
        d = cnt_v(yR0, y_end_R)
        w = (max(0, xe-xs) % size) + (max(0, y_end_L-yL0) % size) + (max(0, y_end_R-yR0) % size)
        return (bas+g+d, -w), xs, xe, yL0, yR0

    candidates = [score(False,False), score(True,False), score(False,True), score(True,True)]
    best = max(candidates, key=lambda s: s[0])
    _, xs, xe, yL0, yR0 = best

    count = 0
    # Bas
    y, x = F0y, xs
    while x + size <= xe + 1e-6:
        poly = [(x,y),(x+size,y),(x+size,y+CUSHION_DEPTH),(x,y+CUSHION_DEPTH),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
        x += size; count += 1
    # Gauche
    x, y = F0x, yL0
    while y + size <= y_end_L + 1e-6:
        poly = [(x,y),(x+CUSHION_DEPTH,y),(x+CUSHION_DEPTH,y+size),(x,y+size),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
        y += size; count += 1
    # Droite
    x, y = F02x, yR0
    while y + size <= y_end_R + 1e-6:
        poly = [(x-CUSHION_DEPTH,y),(x,y),(x,y+size),(x-CUSHION_DEPTH,y+size),(x-CUSHION_DEPTH,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
        y += size; count += 1
    return count

# ----- U1F : évaluation / dessin -----
def _eval_U1F_counts(pts, sb, sg, sd, shiftL, shiftR, traversins=None):
    F0x, F0y = pts["F0"]; F02x = pts["F02"][0]
    y_end_L = pts["By_cush"][1]; y_end_R = pts["By4_cush"][1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK
    xs = F0x + (CUSHION_DEPTH if shiftL else 0)
    xe = F02x - (CUSHION_DEPTH if shiftR else 0)
    yL0 = F0y + (0 if shiftL else CUSHION_DEPTH)
    yR0 = F0y + (0 if shiftR else CUSHION_DEPTH)
    len_b = max(0, xe-xs); len_g=max(0, y_end_L-yL0); len_d=max(0, y_end_R-yR0)
    nb, wb = _waste_and_count_1d(len_b, sb)
    ng, wg = _waste_and_count_1d(len_g, sg)
    nd, wd = _waste_and_count_1d(len_d, sd)
    waste = wb+wg+wd; cover=nb*sb+ng*sg+nd*sd
    return {"counts":{"bas":nb,"gauche":ng,"droite":nd},"waste":waste,"cover":cover}

def _optimize_valise_U1F(pts, rng, same, traversins=None):
    best=None; r0,r1=rng
    for sg in range(r0,r1+1):
        for sb in ([sg] if same else range(r0,r1+1)):
            for sd in ([sg] if same else range(r0,r1+1)):
                if max(sb,sg,sd)-min(sb,sg,sd) > 5:
                    continue
                E=[]
                for sl in (False,True):
                    for sr in (False,True):
                        E.append(_eval_U1F_counts(pts,sb,sg,sd,sl,sr,traversins=traversins))
                e = min(E, key=lambda x: (x["waste"], -x["cover"], -sb, -sg, -sd))
                score=(e["waste"], -e["cover"], -sb, -sg, -sd)
                if (best is None) or (score < best["score"]):
                    best={"score":score, "sizes":{"bas":sb,"gauche":sg,"droite":sd}, "shifts":("?", "?")}
    # Retrouver shifts exacts
    if best:
        tgt = best["score"]
        for sl in (False,True):
            for sr in (False,True):
                chk=_eval_U1F_counts(pts,best["sizes"]["bas"],best["sizes"]["gauche"],best["sizes"]["droite"],sl,sr,traversins=traversins)
                score=(chk["waste"], -chk["cover"], -best["sizes"]["bas"], -best["sizes"]["gauche"], -best["sizes"]["droite"])
                if score==tgt:
                    best["shifts"]=(sl,sr); break
    return best

def _draw_U1F_with_sizes(t,tr,pts,sizes,shiftL,shiftR,traversins=None):
    F0x, F0y = pts["F0"]; F02x=pts["F02"][0]
    y_end_L = pts["By_cush"][1]; y_end_R=pts["By4_cush"][1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK

    # Bas
    xs = F0x + (CUSHION_DEPTH if shiftL else 0)
    xe = F02x - (CUSHION_DEPTH if shiftR else 0)
    sb=sizes["bas"]; nb=0; x=xs; y=F0y
    while x + sb <= xe + 1e-6:
        poly=[(x,y),(x+sb,y),(x+sb,y+CUSHION_DEPTH),(x,y+CUSHION_DEPTH),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sb}",font=FONT_CUSHION)
        nb+=1; x+=sb

    # Gauche
    yL0 = F0y + (0 if shiftL else CUSHION_DEPTH)
    sg=sizes["gauche"]; ng=0; xg=F0x; y_=yL0
    while y_ + sg <= y_end_L + 1e-6:
        poly=[(xg,y_),(xg+CUSHION_DEPTH,y_),(xg+CUSHION_DEPTH,y_+sg),(xg,y_+sg),(xg,y_)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sg}",font=FONT_CUSHION)
        ng+=1; y_+=sg

    # Droite
    yR0 = F0y + (0 if shiftR else CUSHION_DEPTH)
    sd=sizes["droite"]; nd=0; xr=F02x; y_=yR0
    while y_ + sd <= y_end_R + 1e-6:
        poly=[(xr-CUSHION_DEPTH,y_),(xr,y_),(xr,y_+sd),(xr-CUSHION_DEPTH,y_+sd),(xr-CUSHION_DEPTH,y_)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sd}",font=FONT_CUSHION)
        nd+=1; y_+=sd

    return nb+ng+nd

# ----- U (no fromage) : fonctions de choix et dessin coussins -----
def _u_variant_x_end(variant, pts):
    if variant in ("v1","v4"):
        return pts["Bx"][0]
    else:
        return pts["F02"][0]

def _eval_U_counts(variant, pts, drawn, sb, sg, sd, shiftL, shiftR, traversins=None):
    F0x, F0y = pts["F0"]
    x_end = _u_variant_x_end(variant, pts)
    xs = F0x + (CUSHION_DEPTH if shiftL else 0)
    xe = x_end - (CUSHION_DEPTH if shiftR else 0)

    y_end_L = pts["By"][1]
    y_end_R = pts["By4"][1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK
    yL0 = F0y + (0 if (not drawn.get("D1", False) or shiftL) else CUSHION_DEPTH)
    has_right = drawn.get("D4", False) or drawn.get("D5", False)
    yR0 = F0y + (0 if (not has_right or shiftR) else CUSHION_DEPTH)

    nb, wb = _waste_and_count_1d(max(0, xe - xs), sb)
    ng, wg = _waste_and_count_1d(max(0, y_end_L - yL0), sg)
    nd, wd = _waste_and_count_1d(max(0, y_end_R - yR0), sd)
    waste = wb + wg + wd
    cover = nb*sb + ng*sg + nd*sd
    return {"counts":{"bas":nb,"gauche":ng,"droite":nd}, "waste":waste, "cover":cover}

def _optimize_valise_U(variant, pts, drawn, rng, same, traversins=None):
    best=None; r0,r1=rng
    for sg in range(r0,r1+1):
        for sb in ([sg] if same else range(r0,r1+1)):
            for sd in ([sg] if same else range(r0,r1+1)):
                if max(sb,sg,sd)-min(sb,sg,sd) > 5:
                    continue
                E=[]
                for sl in (False,True):
                    for sr in (False,True):
                        E.append(_eval_U_counts(variant, pts, drawn, sb, sg, sd, sl, sr, traversins=traversins))
                e = min(E, key=lambda x: (x["waste"], -x["cover"], -sb, -sg, -sd))
                score=(e["waste"], -e["cover"], -sb, -sg, -sd)
                if (best is None) or (score < best["score"]):
                    best={"score":score, "sizes":{"bas":sb,"gauche":sg,"droite":sd}}
    if best:
        tgt=best["score"]
        for sl in (False,True):
            for sr in (False,True):
                chk=_eval_U_counts(variant, pts, drawn, best["sizes"]["bas"], best["sizes"]["gauche"], best["sizes"]["droite"], sl, sr, traversins=traversins)
                score=(chk["waste"], -chk["cover"], -best["sizes"]["bas"], -best["sizes"]["gauche"], -best["sizes"]["droite"])
                if score==tgt:
                    best["shiftL"], best["shiftR"] = sl, sr
                    break
    return best

def _draw_U_with_sizes(variant, t, tr, pts, sizes, drawn, shiftL, shiftR, traversins=None):
    F0x, F0y = pts["F0"]
    x_end = _u_variant_x_end(variant, pts)
    # Bas
    xs = F0x + (CUSHION_DEPTH if shiftL else 0)
    xe = x_end - (CUSHION_DEPTH if shiftR else 0)
    sb = sizes["bas"]; nb=0; x=xs; y=F0y
    while x + sb <= xe + 1e-6:
        poly=[(x,y),(x+sb,y),(x+sb,y+CUSHION_DEPTH),(x,y+CUSHION_DEPTH),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sb}",font=FONT_CUSHION)
        nb+=1; x+=sb

    # Gauche
    y_end_L = pts["By"][1]
    if traversins and "g" in traversins: y_end_L -= TRAVERSIN_THK
    yL0 = F0y + (0 if (not drawn.get("D1", False) or shiftL) else CUSHION_DEPTH)
    sg = sizes["gauche"]; ng=0; xg=F0x; y_=yL0
    while y_ + sg <= y_end_L + 1e-6:
        poly=[(xg,y_),(xg+CUSHION_DEPTH,y_),(xg+CUSHION_DEPTH,y_+sg),(xg,y_+sg),(xg,y_)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sg}",font=FONT_CUSHION)
        ng+=1; y_+=sg

    # Droite
    y_end_R = pts["By4"][1]
    if traversins and "d" in traversins: y_end_R -= TRAVERSIN_THK
    has_right = drawn.get("D4", False) or drawn.get("D5", False)
    yR0 = F0y + (0 if (not has_right or shiftR) else CUSHION_DEPTH)
    sd = sizes["droite"]; nd=0
    x_col = (pts["Bx"][0] if variant in ("v1","v4") else pts["F02"][0])
    y_=yR0
    while y_ + sd <= y_end_R + 1e-6:
        poly=[(x_col-CUSHION_DEPTH,y_),(x_col,y_),(x_col,y_+sd),(x_col-CUSHION_DEPTH,y_+sd),(x_col-CUSHION_DEPTH,y_)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sd}",font=FONT_CUSHION)
        nd+=1; y_+=sd

    return nb+ng+nd

# ----- Simple S1 -----
def _optimize_valise_simple(pts, rng, mer_side=None, mer_len=0, traversins=None):
    x0 = pts["B0"][0]; x1 = pts["Bx"][0]
    if mer_side == 'g' and mer_len>0:
        x0 = max(x0, pts.get("B0_m", (x0,0))[0])
    if mer_side == 'd' and mer_len>0:
        x1 = min(x1, pts.get("Bx_m", (x1,0))[0])
    if traversins:
        if "g" in traversins: x0 += TRAVERSIN_THK
        if "d" in traversins: x1 -= TRAVERSIN_THK

    best=None; r0,r1=rng
    for s in range(r0, r1+1):
        n0, w0 = _waste_and_count_1d(max(0, x1-x0), s)
        n1, w1 = _waste_and_count_1d(max(0, x1-(x0+CUSHION_DEPTH)), s)
        if w1 < w0 or (w1==w0 and n1>n0):
            n, waste, off = n1, w1, CUSHION_DEPTH
        else:
            n, waste, off = n0, w0, 0
        score=(waste, -n, -s)
        if (best is None) or (score < best["score"]):
            best={"score":score, "size":s, "offset":off, "count":n}
    return best

def _draw_simple_with_size(t,tr,pts,size,mer_side=None,mer_len=0, traversins=None):
    x0 = pts["B0"][0]; x1 = pts["Bx"][0]
    if mer_side == 'g' and mer_len>0:
        x0 = max(x0, pts.get("B0_m", (x0,0))[0])
    if mer_side == 'd' and mer_len>0:
        x1 = min(x1, pts.get("Bx_m", pts["Bx"])[0])
    if traversins:
        if "g" in traversins: x0 += TRAVERSIN_THK
        if "d" in traversins: x1 -= TRAVERSIN_THK

    n0, w0 = _waste_and_count_1d(max(0,x1-x0), size)
    n1, w1 = _waste_and_count_1d(max(0,x1-(x0+CUSHION_DEPTH)), size)
    off = CUSHION_DEPTH if (w1 < w0 or (w1==w0 and n1>n0)) else 0
    x = x0 + off; y = pts["B0"][1]; n=0
    while x + size <= x1 + 1e-6:
        poly=[(x,y),(x+size,y),(x+size,y+CUSHION_DEPTH),(x,y+CUSHION_DEPTH),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
        x+=size; n+=1
    return n

# =====================================================================
# =======================  LF (L avec angle fromage)  ==================
# =====================================================================
def compute_points_LF_variant(tx, ty, profondeur=DEPTH_STD,
                              dossier_left=True, dossier_bas=True,
                              acc_left=True, acc_bas=True,
                              meridienne_side=None, meridienne_len=0):
    A = profondeur + 20
    prof = profondeur
    pts = {}
    if dossier_left and dossier_bas:
        F0x, F0y = 10, 10
    elif (not dossier_left) and dossier_bas:
        F0x, F0y = 0, 10
    elif dossier_left and (not dossier_bas):
        F0x, F0y = 10, 0
    else:
        F0x, F0y = 0, 0

    pts["F0"]  = (F0x, F0y)
    pts["Fy"]  = (F0x, F0y + A)
    pts["Fx"]  = (F0x + A, F0y)
    pts["Fy2"] = (F0x + prof, F0y + A)
    pts["Fx2"] = (F0x + A, F0y + prof)

    top_y = ty - (ACCOUDOIR_THICK if acc_left else 0)
    pts["By"]  = (F0x, top_y)
    pts["By2"] = (F0x + prof, top_y)

    pts["D0"]  = (0, 0)
    pts["D0x"] = (F0x, 0)
    pts["D0y"] = (0, F0y)
    pts["Dy"]  = (0, F0y + A)
    pts["Dy2"] = (0, top_y)

    pts["Ay"]  = (0, ty)
    pts["Ay2"] = (F0x + prof, ty)
    pts["Ay_"] = (F0x, ty)

    banq_stop_x = tx - (ACCOUDOIR_THICK if acc_bas else 0)
    pts["Dx"]  = (F0x + A, 0)
    pts["Dx2"] = (banq_stop_x, 0)
    pts["Bx"]  = (banq_stop_x, F0y)
    pts["Bx2"] = (banq_stop_x, F0y + prof)

    pts["Ax"]  = (tx, 0)
    pts["Ax2"] = (tx, F0y + prof)
    pts["Ax_"] = (tx, F0y)

    if meridienne_side == 'b' and meridienne_len > 0:
        dx2_stop = min(banq_stop_x, tx - meridienne_len)
        pts["Dx2"] = (dx2_stop, 0)
        pts["Bx_"] = (tx - meridienne_len, F0y)

    if meridienne_side == 'g' and meridienne_len > 0:
        mer_y = max(F0y + A, top_y - meridienne_len); mer_y = min(mer_y, top_y)
        pts["By_"] = (F0x, mer_y)
        pts["Dy2"] = (0, min(top_y, mer_y))

    if dossier_left and not dossier_bas:
        pts["D0y"] = (0, 0)
    if dossier_bas and not dossier_left:
        pts["D0x"] = (0, 0)

    return pts

def _choose_cushion_size_auto(pts, tx, ty, meridienne_side=None, meridienne_len=0, traversins=None):
    xF, yF = pts["F0"]
    x_end = pts.get("Bx_", pts.get("Bx", (tx, yF)))[0]
    if meridienne_side == 'b' and meridienne_len > 0:
        x_end = min(x_end, tx - meridienne_len)
    y_start = yF + CUSHION_DEPTH
    y_end = pts.get("By_", pts.get("By", (xF, ty)))[1]
    if traversins:
        if "b" in traversins: x_end -= TRAVERSIN_THK
        if "g" in traversins: y_end -= TRAVERSIN_THK
    usable_h = max(0.0, x_end - xF)
    usable_v = max(0.0, y_end - y_start)

    candidates = [65, 80, 90]
    def score(s):
        waste_h = usable_h % s if usable_h > 0 else 0
        waste_v = usable_v % s if usable_v > 0 else 0
        return (max(waste_h, waste_v), -s)
    return min(candidates, key=score)

def draw_cousins_and_return_count(t, tr, pts, tx, ty, coussins, meridienne_side, meridienne_len, traversins=None):
    if isinstance(coussins, str) and coussins.strip().lower() == "auto":
        size = _choose_cushion_size_auto(pts, tx, ty, meridienne_side, meridienne_len, traversins=traversins)
    else:
        size = int(coussins)

    F0x, F0y = pts["F0"]
    x_end = pts.get("Bx_", pts.get("Bx", (tx, F0y)))[0]
    y_end = pts.get("By_", pts.get("By", (F0x, ty)))[1]
    if traversins:
        if "b" in traversins: x_end -= TRAVERSIN_THK
        if "g" in traversins: y_end -= TRAVERSIN_THK

    def count_bas(x_start, x_stop):
        L = max(0, x_stop - x_start)
        return int(L // size)
    def count_gauche(y_start, y_stop):
        L = max(0, y_stop - y_start)
        return int(L // size)

    # Compare orientation A vs B
    A_bas = count_bas(F0x, x_end); A_g = count_gauche(F0y + CUSHION_DEPTH, y_end)
    B_bas = count_bas(F0x + CUSHION_DEPTH, x_end); B_g = count_gauche(F0y, y_end)
    use_shift = (B_bas + B_g, -( (x_end-(F0x+CUSHION_DEPTH))%size + (y_end-F0y)%size )) > (A_bas + A_g, -((x_end-F0x)%size + (y_end-(F0y+CUSHION_DEPTH))%size))

    count = 0
    # bas
    y = F0y
    x_cur = F0x + (CUSHION_DEPTH if use_shift else 0)
    while x_cur + size <= x_end + 1e-6:
        poly = [(x_cur, y), (x_cur+size, y), (x_cur+size, y+CUSHION_DEPTH), (x_cur, y+CUSHION_DEPTH), (x_cur, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{size}", font=FONT_CUSHION)
        x_cur += size; count += 1
    # gauche
    x = F0x
    y_cur = F0y + (0 if use_shift else CUSHION_DEPTH)
    while y_cur + size <= y_end + 1e-6:
        poly = [(x, y_cur), (x+CUSHION_DEPTH, y_cur), (x+CUSHION_DEPTH, y_cur+size), (x, y_cur+size), (x, y_cur)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{size}", font=FONT_CUSHION)
        y_cur += size; count += 1

    return count, size

def build_polys_LF_variant(pts, tx, ty, profondeur=DEPTH_STD,
                           dossier_left=True, dossier_bas=True,
                           acc_left=True, acc_bas=True,
                           meridienne_side=None, meridienne_len=0):
    polys={"angle":[],"banquettes":[],"dossiers":[],"accoudoirs":[]}

    angle=[pts["F0"],pts["Fx"],pts["Fx2"],pts["Fy2"],pts["Fy"],pts["F0"]]
    polys["angle"].append(angle)

    ban_g=[pts["Fy"],pts["Fy2"],pts["By2"],pts["By"],pts["Fy"]]
    Lg=abs(pts["By"][1]-pts["Fy"][1])
    split_g = False
    if Lg>SPLIT_THRESHOLD:
        split_g = True
        mid_y=_split_mid_int(pts["Fy"][1],pts["By"][1])
        Fy_mid=(pts["Fy"][0],mid_y); Fy2_mid=(pts["Fy2"][0],mid_y)
        polys["banquettes"]+=[
            [pts["Fy"],pts["Fy2"],Fy2_mid,Fy_mid,pts["Fy"]],
            [Fy_mid,Fy2_mid,pts["By2"],pts["By"],Fy_mid]
        ]
    else:
        polys["banquettes"].append(ban_g)

    ban_b=[pts["Fx"],pts["Fx2"],pts["Bx2"],pts["Bx"],pts["Fx"]]
    Lb=abs(pts["Bx"][0]-pts["Fx"][0])
    split_b = False
    if Lb>SPLIT_THRESHOLD:
        split_b = True
        mid_x=_split_mid_int(pts["Fx"][0],pts["Bx"][0])
        Fx_mid=(mid_x,pts["Fx"][1]); Fx2_mid=(mid_x,pts["Fx2"][1])
        polys["banquettes"]+=[
            [pts["Fx"],pts["Fx2"],Fx2_mid,Fx_mid,pts["Fx"]],
            [Fx_mid,Fx2_mid,pts["Bx2"],pts["Bx"],Fx_mid]
        ]
    else:
        polys["banquettes"].append(ban_b)

    if dossier_left:
        dos_g_from=[pts["D0"],pts["D0x"],pts["F0"],pts["Fy"],pts["Dy"],pts["D0"]] if dossier_bas \
            else [pts["D0y"],pts["F0"],pts["Fy"],pts["Dy"],pts["D0y"]]
        dos_g_banc=[pts["Dy"],pts["Dy2"],pts.get("By_",pts["By"]),pts["Fy"],pts["Dy"]]
        polys["dossiers"]+=[dos_g_from,dos_g_banc]
    if dossier_bas:
        dos_b_from=[pts["D0x"],pts["Dx"],pts["Fx"],pts["F0"],pts["D0x"]] if dossier_left \
            else [pts["D0x"],pts["F0"],pts["Fx"],pts["Dx"],pts["D0x"]]
        dos_b_banc=[pts["Dx"],pts["Dx2"],pts.get("Bx_",pts["Bx"]),pts["Fx"],pts["Dx"]]
        polys["dossiers"]+=[dos_b_from,dos_b_banc]

    if acc_left:
        acc_g=[pts["Dy2"],pts["Ay"],pts["Ay2"],pts["By2"],pts["Dy2"]] if dossier_left \
            else [pts["By"],pts["Ay_"],pts["Ay2"],pts["By2"],pts["By"]]
        polys["accoudoirs"].append(acc_g)
    if acc_bas:
        acc_b=[pts["Dx2"],pts["Ax"],pts["Ax2"],pts["Bx2"],pts["Dx2"]] if dossier_bas \
            else [pts["Bx"],pts["Ax_"],pts["Ax2"],pts["Bx2"],pts["Bx"]]
        polys["accoudoirs"].append(acc_b)

    polys["split_flags"]={"left":split_g,"bottom":split_b,"right":False}
    return polys

def render_LF_variant(tx, ty, profondeur=DEPTH_STD,
                      dossier_left=True, dossier_bas=True,
                      acc_left=True, acc_bas=True,
                      meridienne_side=None, meridienne_len=0,
                      coussins="auto",
                      traversins=None,
                      couleurs=None,
                      window_title="LF — variantes"):
    if meridienne_side == 'g' and acc_left:
        raise ValueError("Erreur: une méridienne gauche ne peut pas coexister avec un accoudoir gauche.")
    if meridienne_side == 'b' and acc_bas:
        raise ValueError("Erreur: une méridienne bas ne peut pas coexister avec un accoudoir bas.")

    trv = _parse_traversins_spec(traversins, allowed={"g","b"})
    legend_items = _resolve_and_apply_colors(couleurs)

    pts=compute_points_LF_variant(tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    polys=build_polys_LF_variant(pts,tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    _assert_banquettes_max_250(polys)

    screen=turtle.Screen(); screen.setup(WIN_W,WIN_H)
    screen.title(f"{window_title} — {tx}x{ty} cm — prof={profondeur} — méridienne {meridienne_side or '-'}={meridienne_len} — coussins={coussins}")
    t=turtle.Turtle(visible=False); t.speed(0); screen.tracer(False)
    tr=WorldToScreen(tx,ty,WIN_W,WIN_H,PAD_PX,ZOOM)

    # (Quadrillage et repères supprimés)

    for poly in polys["dossiers"]:   draw_polygon_cm(t,tr,poly,fill=COLOR_DOSSIER)
    for poly in polys["banquettes"]: draw_polygon_cm(t,tr,poly,fill=COLOR_ASSISE)
    for poly in polys["accoudoirs"]: draw_polygon_cm(t,tr,poly,fill=COLOR_ACC)
    for poly in polys["angle"]:      draw_polygon_cm(t,tr,poly,fill=COLOR_ASSISE)

    # Traversins (visuel) + comptage
    n_traversins = _draw_traversins_L_like(t, tr, pts, profondeur, trv)

    draw_double_arrow_vertical_cm(t,tr,-25,0,ty,f"{ty} cm")
    draw_double_arrow_horizontal_cm(t,tr,-25,0,tx,f"{tx} cm")

    banquette_sizes=[]
    if polys["angle"]:
        side=int(round(pts["Fy"][1]-pts["F0"][1])); label_poly(t,tr,polys["angle"][0],f"{side}×{side} cm")
    for poly in polys["banquettes"]:
        L,P=banquette_dims(poly); text=f"{L}×{P} cm"; banquette_sizes.append((L,P))
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]; bb_w=max(xs)-min(xs); bb_h=max(ys)-min(ys)
        if bb_h>=bb_w:
            label_poly_offset_cm(t,tr,poly,text,dx_cm=(CUSHION_DEPTH+10),dy_cm=0.0)
        else:
            label_poly(t,tr,poly,text)
    for poly in polys["dossiers"]: label_poly(t,tr,poly,"10")
    for poly in polys["accoudoirs"]: label_poly(t,tr,poly,"15")

    # ===== COUSSINS =====
    spec = _parse_coussins_spec(coussins)
    if spec["mode"] == "auto":
        cushions_count, chosen_size = draw_cousins_and_return_count(t,tr,pts,tx,ty,"auto",meridienne_side,meridienne_len,traversins=trv)
        total_line = f"{coussins} → {cushions_count} × {chosen_size} cm"
    elif spec["mode"] == "fixed":
        cushions_count, chosen_size = draw_cousins_and_return_count(t,tr,pts,tx,ty,int(spec["fixed"]),meridienne_side,meridienne_len,traversins=trv)
        total_line = f"{coussins} → {coussins} × {chosen_size} cm"
    else:
        best = _optimize_valise_L_like(pts, spec["range"], spec["same"], x_end_key="Bx", y_end_key="By", traversins=trv)
        if not best:
            raise ValueError("Aucune configuration valise valide pour LF.")
        sizes = best["sizes"]; shift = best["shift_bas"]
        n, sb, sg = _draw_L_like_with_sizes(t, tr, pts, sizes, shift, x_end_key="Bx", y_end_key="By", traversins=trv)
        cushions_count = n; total_line = f"bas={sb} / gauche={sg} (Δ={abs(sb-sg)}) — total: {n}"

    # Légende (couleurs)
    draw_legend(t, tr, tx, ty, items=legend_items, pos="top-right")

    screen.tracer(True); t.hideturtle()
    add_split = int(polys["split_flags"]["left"] and dossier_left) + int(polys["split_flags"]["bottom"] and dossier_bas)
    A = profondeur + 20
    print("=== Rapport canapé (LF) ===")
    print(f"Dimensions : {tx}×{ty} cm — profondeur : {profondeur} cm")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers : {len(polys['dossiers'])} (+{add_split} via scission) | Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 1")
    print(f"Angles : 1 × {A}×{A} cm")
    print(f"Traversins : {n_traversins} × 70x30")
    print(f"Coussins : {total_line}")
    turtle.done()

# =====================================================================
# ========================  U2f (2 angles fromage)  ====================
# =====================================================================
def compute_points_U2f(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True, dossier_right=True,
                       acc_left=True, acc_bas=True, acc_right=True,
                       meridienne_side=None, meridienne_len=0):
    A = profondeur + 20
    pts = {}
    pts["D0"]=(0,0); pts["D0x"]=(10,0); pts["D0y"]=(0,10)
    pts["F0"]=(10,10); pts["Fy"]=(10,10+A); pts["Fy2"]=(10+profondeur, 10+A)
    pts["Fx"]=(10+A,10); pts["Fx2"]=(10+A,10+profondeur)

    top_y_L = ty_left - (ACCOUDOIR_THICK if acc_left else 0)
    pts["Dy"]=(0,10+A); pts["Dy2"]=(0, top_y_L)
    pts["By"]=(10, top_y_L); pts["By2"]=(10+profondeur, top_y_L)
    pts["Ay"]=(0, ty_left); pts["Ay2"]=(10+profondeur, ty_left); pts["Ay_"]=(10, ty_left)

    BxL = tx - A - 10
    pts["Dx"]=(10+A,0); pts["Dx2"]=(BxL,0)
    pts["Bx"]=(BxL,10); pts["Bx2"]=(BxL,10+profondeur)

    F02x = tx - 10
    pts["F02"]=(F02x,10); pts["Fy4"]=(F02x,10+A); pts["Fy3"]=(F02x - profondeur, 10+A)
    top_y_R = tz_right - (ACCOUDOIR_THICK if acc_right else 0)
    pts["By3"]=(pts["Fy3"][0], top_y_R); pts["By4"]=(F02x, top_y_R)
    pts["D02"]=(tx,0); pts["D02y"]=(tx,10); pts["Dy_r"]=(tx,10+A); pts["Dy2_r"]=(tx, top_y_R)
    pts["Ax"]=(pts["By3"][0], tz_right); pts["Ax2"]=(tx, tz_right); pts["Ax_par"]=(tx - 10, tz_right)

    if meridienne_side == 'g' and meridienne_len > 0:
        mer_y_L = max(10 + A, ty_left - meridienne_len); mer_y_L = min(mer_y_L, top_y_L)
        pts["By_"]=(pts["By"][0], mer_y_L); pts["By2_"]=(pts["By2"][0], mer_y_L)
        pts["Dy2"]=(0, mer_y_L)
    if meridienne_side == 'd' and meridienne_len > 0:
        mer_y_R = max(10 + A, tz_right - meridienne_len); mer_y_R = min(mer_y_R, top_y_R)
        pts["By4_"]=(pts["By4"][0], mer_y_R); pts["Dy2_r"]=(tx, mer_y_R)

    pts["_ty_canvas"] = max(ty_left, tz_right)
    return pts

def build_polys_U2f(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                    dossier_left=True, dossier_bas=True, dossier_right=True,
                    acc_left=True, acc_bas=True, acc_right=True):
    polys = {"angles": [], "banquettes": [], "dossiers": [], "accoudoirs": []}

    angle_L = [pts["F0"], pts["Fx"], pts["Fx2"], pts["Fy2"], pts["Fy"], pts["F0"]]
    polys["angles"].append(angle_L)
    angle_R = [pts["Bx2"], pts["Bx"], pts["F02"], pts["Fy4"], pts["Fy3"], pts["Bx2"]]
    polys["angles"].append(angle_R)

    # G
    ban_g = [pts["Fy"], pts["Fy2"], pts["By2"], pts["By"], pts["Fy"]]
    Lg = abs(pts["By"][1] - pts["Fy"][1])
    split_g = False
    if Lg > SPLIT_THRESHOLD:
        split_g = True
        mid_y = _split_mid_int(pts["Fy"][1], pts["By"][1])
        Fy_mid  = (pts["Fy"][0],  mid_y); Fy2_mid = (pts["Fy2"][0], mid_y)
        polys["banquettes"] += [[pts["Fy"],pts["Fy2"],Fy2_mid,Fy_mid,pts["Fy"]],
                                [Fy_mid,Fy2_mid,pts["By2"],pts["By"],Fy_mid]]
    else:
        polys["banquettes"].append(ban_g)

    # Bas
    ban_b = [pts["Fx"], pts["Fx2"], pts["Bx2"], pts["Bx"], pts["Fx"]]
    Lb = abs(pts["Bx"][0] - pts["Fx"][0])
    split_b = False
    if Lb > SPLIT_THRESHOLD:
        split_b = True
        mid_x = _split_mid_int(pts["Fx"][0], pts["Bx"][0])
        Fx_mid  = (mid_x, pts["Fx"][1]); Fx2_mid = (mid_x, pts["Fx2"][1])
        polys["banquettes"] += [[pts["Fx"],pts["Fx2"],Fx2_mid,Fx_mid,pts["Fx"]],
                                [Fx_mid,Fx2_mid,pts["Bx2"],pts["Bx"],Fx_mid]]
    else:
        polys["banquettes"].append(ban_b)

    # Droite
    ban_r = [pts["Fy3"], pts["By3"], pts["By4"], pts["Fy4"], pts["Fy3"]]
    Lr = abs(pts["By4"][1] - pts["Fy4"][1])
    split_r = False
    if Lr > SPLIT_THRESHOLD:
        split_r = True
        mid_y = _split_mid_int(pts["Fy4"][1], pts["By4"][1])
        Fy3_mid = (pts["Fy3"][0], mid_y); Fy4_mid = (pts["Fy4"][0], mid_y)
        polys["banquettes"] += [[pts["Fy3"],Fy3_mid,Fy4_mid,pts["Fy4"],pts["Fy3"]],
                                [Fy3_mid,pts["By3"],pts["By4"],Fy4_mid,Fy3_mid]]
    else:
        polys["banquettes"].append(ban_r)

    if dossier_left:
        polys["dossiers"].append([pts["D0"], pts["D0x"], pts["F0"], pts["Fy"], pts["Dy"], pts["D0"]])
        polys["dossiers"].append([pts["Dy"], pts["Dy2"], pts.get("By_", pts["By"]), pts["Fy"], pts["Dy"]])
    if dossier_bas:
        polys["dossiers"].append([pts["D0x"], pts["Dx"], pts["Fx"], pts["F0"], pts["D0x"]])
        polys["dossiers"].append([pts["Dx"], pts["Dx2"], pts["Bx"], pts["Fx"], pts["Dx"]])
        polys["dossiers"].append([pts["Dx2"], pts["Bx"], pts["D02y"], pts["D02"], pts["Dx2"]])
    if dossier_right:
        polys["dossiers"].append([pts["D02y"], pts["F02"], pts["Fy4"], pts["Dy_r"], pts["D02y"]])
        polys["dossiers"].append([pts["Dy_r"], pts["Fy4"], pts.get("By4_", pts["By4"]), pts["Dy2_r"], pts["Dy_r"]])

    if acc_left and dossier_left:
        polys["accoudoirs"].append([pts["Dy2"], pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"]])
    elif acc_left and not dossier_left:
        polys["accoudoirs"].append([pts["By"], pts["Ay_"], pts["Ay2"], pts["By2"], pts["By"]])

    if acc_right and dossier_right:
        polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], pts["Dy2_r"], pts["By3"]])
    elif acc_right and not dossier_right:
        polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts.get("Ax_par", (tx-10, max(ty_left, tz_right))), pts["By4"], pts["By3"]])

    polys["split_flags"]={"left":split_g,"bottom":split_b,"right":split_r}
    return polys

def _draw_cushions_U2f_optimized_wrapper(t, tr, pts, size, traversins=None):
    return _draw_cushions_U2f_optimized(t, tr, pts, size, traversins=traversins)

def render_U2f_variant(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True, dossier_right=True,
                       acc_left=True, acc_bas=True, acc_right=True,
                       meridienne_side=None, meridienne_len=0,
                       coussins="auto",
                       traversins=None,
                       couleurs=None,
                       window_title="U2F — variantes"):
    if meridienne_side == 'g' and acc_left:
        raise ValueError("Erreur: une méridienne gauche ne peut pas coexister avec un accoudoir gauche.")
    if meridienne_side == 'd' and acc_right:
        raise ValueError("Erreur: une méridienne droite ne peut pas coexister avec un accoudoir droit.")

    trv = _parse_traversins_spec(traversins, allowed={"g","d"})
    legend_items = _resolve_and_apply_colors(couleurs)

    pts = compute_points_U2f(tx, ty_left, tz_right, profondeur,
                             dossier_left, dossier_bas, dossier_right,
                             acc_left, acc_bas, acc_right,
                             meridienne_side, meridienne_len)
    polys = build_polys_U2f(pts, tx, ty_left, tz_right, profondeur,
                            dossier_left, dossier_bas, dossier_right,
                            acc_left, acc_bas, acc_right)
    _assert_banquettes_max_250(polys)

    ty_canvas = pts["_ty_canvas"]
    screen = turtle.Screen(); screen.setup(WIN_W, WIN_H)
    screen.title(f"{window_title} — tx={tx} / ty(left)={ty_left} / tz(right)={tz_right} — prof={profondeur}")
    t = turtle.Turtle(visible=False); t.speed(0); screen.tracer(False)
    tr = WorldToScreen(tx, ty_canvas, WIN_W, WIN_H, PAD_PX, ZOOM)

    # (Quadrillage et repères supprimés)

    for poly in polys["dossiers"]:   draw_polygon_cm(t, tr, poly, fill=COLOR_DOSSIER)
    for poly in polys["banquettes"]: draw_polygon_cm(t, tr, poly, fill=COLOR_ASSISE)
    for poly in polys["accoudoirs"]: draw_polygon_cm(t, tr, poly, fill=COLOR_ACC)
    for poly in polys["angles"]:     draw_polygon_cm(t, tr, poly, fill=COLOR_ASSISE)

    # Traversins (visuel) + comptage
    n_traversins = _draw_traversins_U_side_F02(t, tr, pts, profondeur, trv)

    draw_double_arrow_vertical_cm(t, tr, -25,    0, ty_left,  f"{ty_left} cm")
    draw_double_arrow_vertical_cm(t, tr,  tx+25, 0, tz_right, f"{tz_right} cm")
    draw_double_arrow_horizontal_cm(t, tr, -25,  0, tx, f"{tx} cm")

    A = profondeur + 20
    for poly in polys["angles"]:
        label_poly(t, tr, poly, f"{A}×{A} cm")

    banquette_sizes=[]
    for poly in polys["banquettes"]:
        L, P = banquette_dims(poly); banquette_sizes.append((L, P))
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        bb_w=max(xs)-min(xs); bb_h=max(ys)-min(ys)
        cx = sum(xs)/len(xs)
        text=f"{L}×{P} cm"
        if bb_h >= bb_w:
            dx = (CUSHION_DEPTH+10) if cx < tx/2 else -(CUSHION_DEPTH+10)
            label_poly_offset_cm(t, tr, poly, text, dx_cm=dx, dy_cm=0.0)
        else:
            label_poly(t, tr, poly, text)

    # ===== COUSSINS =====
    spec = _parse_coussins_spec(coussins)
    if spec["mode"] == "auto":
        # ancien auto (65,80,90)
        F0x, F0y = pts["F0"]; F02x = pts["F02"][0]
        y_end_L = pts.get("By_", pts["By"])[1]
        y_end_R = pts.get("By4_", pts["By4"])[1]
        if trv:
            if "g" in trv: y_end_L -= TRAVERSIN_THK
            if "d" in trv: y_end_R -= TRAVERSIN_THK
        best, best_score = 65, (1e9, -1)
        for s in (65,80,90):
            usable_h = max(0, F02x - F0x)
            usable_v_L = max(0, y_end_L - (F0y + CUSHION_DEPTH))
            usable_v_R = max(0, y_end_R - (F0y + CUSHION_DEPTH))
            waste_h = usable_h % s if usable_h > 0 else 0
            waste_v = max(usable_v_L % s if usable_v_L > 0 else 0,
                          usable_v_R % s if usable_v_R > 0 else 0)
            score = (max(waste_h, waste_v), -s)
            if score < best_score:
                best_score, best = score, s
        size = best
        cushions_count = _draw_cushions_U2f_optimized_wrapper(t, tr, pts, size, traversins=trv)
        total_line = f"{coussins} → {cushions_count} × {size} cm"
    elif spec["mode"] == "fixed":
        size = int(spec["fixed"])
        cushions_count = _draw_cushions_U2f_optimized_wrapper(t, tr, pts, size, traversins=trv)
        total_line = f"{coussins} → {coussins} × {size} cm"
    else:
        best = _optimize_valise_U2f(pts, spec["range"], spec["same"], traversins=trv)
        if not best:
            raise ValueError("Aucune configuration valise valide pour U2f.")
        sizes = best["sizes"]; shiftL = best["shiftL"]; shiftR = best["shiftR"]
        cushions_count = _draw_U2f_with_sizes(t, tr, pts, sizes, shiftL, shiftR, traversins=trv)
        sb, sg, sd = sizes["bas"], sizes["gauche"], sizes["droite"]
        total_line = f"bas={sb} / gauche={sg} / droite={sd} (Δ={max(sb,sg,sd)-min(sb,sg,sd)}) — total: {cushions_count}"

    # Titre demandé + légende (U → légende en haut-centre)
    draw_title_center(t, tr, tx, ty_canvas, "Canapé en U avec deux angles")
    draw_legend(t, tr, tx, ty_canvas, items=legend_items, pos="top-center")

    screen.tracer(True); t.hideturtle()
    add_split = sum(int(v) for v in polys.get("split_flags", {}).values())
    print("=== Rapport canapé U2f ===")
    print(f"Dimensions : tx={tx} / ty(left)={ty_left} / tz(right)={tz_right} — prof={profondeur} (A={A})")
    print(f"Méridienne : {meridienne_side or '-'} ({meridienne_len} cm)")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    dossier_bonus = int(polys["split_flags"].get("left", False) and dossier_left) + \
                   int(polys["split_flags"].get("bottom", False) and dossier_bas) + \
                   int(polys["split_flags"].get("right", False) and dossier_right)
    print(f"Dossiers : {len(polys['dossiers'])} (+{dossier_bonus} via scission) | Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d'angle : 2")
    print(f"Angles : 2 × {A}×{A} cm")
    print(f"Traversins : {n_traversins} × 70x30")
    print(f"Coussins : {total_line}")
    turtle.done()

# =====================================================================
# ===================  U1F (1 angle fromage) — v1..v4  =================
# =====================================================================
# (version validée + palette + légende U en haut-centre)

def _split_banquette_if_needed_U1F(poly):
    xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
    x0,x1=min(xs),max(xs); y0,y1=min(ys),max(ys)
    w=x1-x0; h=y1-y0
    if w<=SPLIT_THRESHOLD and h<=SPLIT_THRESHOLD:
        return [poly], False
    res=[]
    split=True
    if w>=h and w>SPLIT_THRESHOLD:
        mx=_split_mid_int(x0,x1)
        left = [(x0,y0),(mx,y0),(mx,y1),(x0,y1),(x0,y0)]
        right=[(mx,y0),(x1,y0),(x1,y1),(mx,y1),(mx,y0)]
        res += [left,right]
    else:
        my=_split_mid_int(y0,y1)
        low =[(x0,y0),(x1,y0),(x1,my),(x0,my),(x0,y0)]
        high=[(x0,my),(x1,my),(x1,y1),(x0,y1),(x0,my)]
        res += [low,high]
    return res, split

def _common_offsets_u1f(profondeur, dossier_left, dossier_bas, dossier_right):
    A = profondeur + 20
    F0x = 10 if dossier_left else 0
    F0y = 10 if dossier_bas  else 0
    return A, F0x, F0y

def _choose_cushion_size_auto_U1F(pts, traversins=None):
    F0x, F0y = pts["F0"]; F02x = pts["F02"][0]
    x_len = max(0, F02x - F0x)
    y_end_L = pts["By_cush"][1]
    y_end_R = pts["By4_cush"][1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK
    yL0 = F0y + CUSHION_DEPTH
    yR0 = F0y + CUSHION_DEPTH
    best, score_best = 65, (1e9,-1)
    for s in (65,80,90):
        waste_bas = x_len % s if x_len>0 else 0
        waste_g   = max(0, y_end_L - yL0) % s if y_end_L>yL0 else 0
        waste_d   = max(0, y_end_R - yR0) % s if y_end_R>yR0 else 0
        sc = (max(waste_bas,waste_g,waste_d), -s)
        if sc < score_best: best, score_best = s, sc
    return best

def _draw_coussins_U1F(t, tr, pts, size, traversins=None):
    F0x, F0y = pts["F0"]; F02x = pts["F02"][0]
    y_end_L = pts["By_cush"][1]; y_end_R = pts["By4_cush"][1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK
    def cnt_h(x0,x1): return int(max(0,x1-x0)//size)
    def cnt_v(y0,y1): return int(max(0,y1-y0)//size)
    def score(sL,sR):
        xs = F0x + (CUSHION_DEPTH if sL else 0)
        xe = F02x - (CUSHION_DEPTH if sR else 0)
        bas = cnt_h(xs,xe)
        yL0 = F0y + (0 if sL else CUSHION_DEPTH)
        yR0 = F0y + (0 if sR else CUSHION_DEPTH)
        g = cnt_v(yL0,y_end_L); d = cnt_v(yR0,y_end_R)
        w = (max(0,xe-xs)%size) + (max(0,y_end_L-yL0)%size) + (max(0,y_end_R-yR0)%size)
        return (bas+g+d, -w), xs, xe, yL0, yR0
    candidates=[score(False,False),score(True,False),score(False,True),score(True,True)]
    _, xs, xe, yL0, yR0 = max(candidates, key=lambda s:s[0])

    count=0
    # BAS
    y = F0y; x = xs
    while x + size <= xe + 1e-6:
        poly=[(x,y),(x+size,y),(x+size,y+CUSHION_DEPTH),(x,y+CUSHION_DEPTH),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
        count+=1; x+=size
    # GAUCHE
    x = F0x; y = yL0
    while y + size <= y_end_L + 1e-6:
        poly=[(x,y),(x+CUSHION_DEPTH,y),(x+CUSHION_DEPTH,y+size),(x,y+size),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
        count+=1; y+=size
    # DROITE
    x = F02x; y = yR0
    while y + size <= y_end_R + 1e-6:
        poly=[(x-CUSHION_DEPTH,y),(x,y),(x,y+size),(x-CUSHION_DEPTH,y+size),(x-CUSHION_DEPTH,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
        count+=1; y+=size
    return count

def compute_points_U1F_v1(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                          dossier_left=True, dossier_bas=True, dossier_right=True,
                          acc_left=True, acc_right=True,
                          meridienne_side=None, meridienne_len=0):
    if meridienne_side == 'g' and acc_left:  raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
    if meridienne_side == 'd' and acc_right: raise ValueError("Méridienne droite interdite avec accoudoir droit.")

    A, F0x, F0y = _common_offsets_u1f(profondeur, dossier_left, dossier_bas, dossier_right)
    pts={}
    pts["D0"]=(0,0); pts["D0x"]=(F0x,0); pts["D0y"]=(0,F0y); pts["F0"]=(F0x,F0y)

    # Gauche
    pts["Fy"]  = (F0x, F0y + A); pts["Fy2"]=(F0x+profondeur, F0y + A)
    pts["Fx"]  = (F0x + A, F0y); pts["Fx2"]=(F0x + A, F0y + profondeur); pts["Dx"]=(F0x + A, 0)

    top_y_L_full = ty_left - (ACCOUDOIR_THICK if acc_left else 0)
    top_y_L_dos  = (max(F0y + A, top_y_L_full - meridienne_len) if meridienne_side=='g' else top_y_L_full)
    pts["By"]=(F0x, top_y_L_full); pts["By2"]=(F0x+profondeur, top_y_L_full)
    pts["Dy"]=(0, F0y + A); pts["Dy2"]=(0, top_y_L_dos)
    pts["By_dL"]=(F0x, top_y_L_dos)   # stop dossier G avec méridienne G
    pts["Ay"]=(0, ty_left); pts["Ay2"]=(F0x+profondeur, ty_left); pts["Ay_"]=(F0x, ty_left)

    # Bas/droite
    D02x_x = tx - (10 if (dossier_right or dossier_bas) else 0)
    pts["D02x"]=(D02x_x,0); pts["F02"]=(D02x_x, F0y)
    Dx2_x = D02x_x - profondeur
    pts["Dx2"]=(Dx2_x,0); pts["Bx"]=(Dx2_x, F0y); pts["Bx2"]=(Dx2_x, F0y + profondeur)
    top_y_R_full = tz_right - (ACCOUDOIR_THICK if acc_right else 0)
    top_y_R_dos  = (max(F0y + A, top_y_R_full - meridienne_len) if meridienne_side=='d' else top_y_R_full)
    pts["By3"]=(Dx2_x, top_y_R_full); pts["By4"]=(D02x_x, top_y_R_full); pts["By4_d"]=(D02x_x, top_y_R_dos)
    pts["D02"]=(tx,0); pts["D02y"]=(tx, F0y); pts["Dy3"]=(tx, top_y_R_dos)
    pts["Ax"]=(Dx2_x, tz_right); pts["Ax2"]=(tx, tz_right); pts["Ax_par"]=(D02x_x, tz_right)

    if not dossier_bas:
        pts["D0y"]=(0,0); pts["D02y"]=(tx,0)

    pts["By_cush"]=(pts["By"][0], min(pts["By"][1], pts["Dy2"][1]))
    pts["By4_cush"]=(pts["By4"][0], min(pts["By4"][1], pts["By4_d"][1]))

    pts["_A"]=A; pts["_ty_canvas"]=max(ty_left, tz_right)
    pts["_draw"]={
        "D1": bool(dossier_left), "D2": bool(dossier_left),
        "D3": bool(dossier_bas),  "D4": bool(dossier_bas), "D5": bool(dossier_bas),
        "D6": bool(dossier_right),
    }
    pts["_acc"]={"L":acc_left, "R":acc_right}
    return pts

def build_polys_U1F_v1(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True, dossier_right=True,
                       acc_left=True, acc_right=True):
    polys={"angle": [], "banquettes": [], "dossiers": [], "accoudoirs": []}
    d={"D1":dossier_left,"D2":dossier_left,"D3":dossier_bas,"D4":dossier_bas,"D5":dossier_bas,"D6":dossier_right}

    polys["angle"].append([pts["F0"], pts["Fx"], pts["Fx2"], pts["Fy2"], pts["Fy"], pts["F0"]])

    split_any=False
    for ban in (
        [pts["Fy"], pts["Fy2"], pts["By2"], pts["By"], pts["Fy"]],
        [pts["Fx2"], pts["Fx"], pts["Bx"], pts["Bx2"], pts["Fx2"]],
        [pts["Bx"], pts["F02"], pts["By4"], pts["By3"], pts["Bx"]],
    ):
        pieces, split = _split_banquette_if_needed_U1F(ban)
        polys["banquettes"] += pieces
        split_any = split_any or split

    if d["D1"]: polys["dossiers"].append([pts["Dy"], pts["Dy2"], pts["By_dL"], pts["Fy"], pts["Dy"]])
    if d["D2"]: polys["dossiers"].append([pts["D0x"], pts["D0"], pts["Dy"], pts["Fy"], pts["D0x"]])
    if d["D3"]: polys["dossiers"].append([pts["D0x"], pts["Dx"], pts["Fx"], pts["F0"], pts["D0x"]])
    if d["D4"]: polys["dossiers"].append([pts["Dx"], pts["Dx2"], pts["Bx"], pts["Fx"], pts["Dx"]])
    if d["D5"]: polys["dossiers"].append([pts["Dx2"], pts["D02x"], pts["F02"], pts["Bx"], pts["Dx2"]])
    if d["D6"]: polys["dossiers"].append([pts["Dy3"], pts["By4_d"], pts["D02x"], pts["D02"], pts["Dy3"]])

    if acc_left:
        if d["D1"]:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_"], pts["Ay2"], pts["By2"], pts["By"], pts["Ay_"]])
    if acc_right:
        if d["D6"]:
            dy_top = pts.get("Dy3", None) or pts.get("Dy4", None)
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], dy_top, pts["By3"]])
        else:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax_par"], pts["By4"], pts["By3"]])

    polys["split_flags"]={"any":split_any}
    return polys

def compute_points_U1F_v2(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                          dossier_left=True, dossier_bas=True, dossier_right=True,
                          acc_left=True, acc_right=True,
                          meridienne_side=None, meridienne_len=0):
    if meridienne_side == 'g' and acc_left:  raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
    if meridienne_side == 'd' and acc_right: raise ValueError("Méridienne droite interdite avec accoudoir droit.")

    A, F0x, F0y = _common_offsets_u1f(profondeur, dossier_left, dossier_bas, dossier_right)
    pts={}
    pts["D0"]=(0,0); pts["D0x"]=(F0x,0); pts["D0y"]=(0,F0y); pts["F0"]=(F0x,F0y)

    # Gauche
    pts["Fy"]=(F0x, F0y + A); pts["Fy2"]=(F0x+profondeur, F0y + A)
    pts["Fx"]=(F0x + A, F0y); pts["Fx2"]=(F0x + A, F0y + profondeur); pts["Dx"]=(F0x + A, 0)

    top_y_L_full = ty_left - (ACCOUDOIR_THICK if acc_left else 0)
    top_y_L_dos  = (max(F0y + A, top_y_L_full - meridienne_len) if meridienne_side=='g' else top_y_L_full)
    pts["By"]=(F0x, top_y_L_full); pts["By2"]=(F0x+profondeur, top_y_L_full)
    pts["Dy"]=(0, F0y + A); pts["Dy2"]=(0, top_y_L_dos)
    pts["By_dL"]=(F0x, top_y_L_dos)
    pts["Ay"]=(0, ty_left); pts["Ay2"]=(F0x+profondeur, ty_left); pts["Ay_"]=(F0x, ty_left)

    # Droite interne F02 (dep. dossier_right)
    F02x = tx - (10 if dossier_right else 0)
    pts["F02"]=(F02x, F0y)

    # Bas v2
    pts["Dx2"]=(F02x, 0); pts["Bx2"]=(F02x, F0y + profondeur)

    # Colonne droite (x = F02x - profondeur)
    col_x = F02x - profondeur
    pts["Fy3"]=(col_x, F0y + profondeur); pts["By3"]=(col_x, tz_right - (ACCOUDOIR_THICK if acc_right else 0))

    # Extrémité droite
    top_y_R_full = tz_right - (ACCOUDOIR_THICK if acc_right else 0)
    top_y_R_dos  = (max(F0y + A, top_y_R_full - meridienne_len) if meridienne_side=='d' else top_y_R_full)
    pts["By4"]=(F02x, top_y_R_full); pts["By4_d"]=(F02x, top_y_R_dos)
    pts["D02"]=(tx,0); pts["D02y"]=(tx, F0y); pts["Dy3"]=(tx, F0y + profondeur); pts["Dy4"]=(tx, top_y_R_dos)
    pts["Ax"]=(col_x, tz_right); pts["Ax2"]=(tx, tz_right); pts["Ax_par"]=(F02x, tz_right)

    if not dossier_bas:
        pts["D0y"]=(0,0); pts["D02y"]=(tx,0)

    pts["By_cush"]=(pts["By"][0], min(pts["By"][1], pts["Dy2"][1]))
    pts["By4_cush"]=(pts["By4"][0], min(pts["By4"][1], pts["By4_d"][1]))

    pts["_A"]=A; pts["_ty_canvas"]=max(ty_left, tz_right)
    pts["_draw"]={
        "D1": bool(dossier_left), "D2": bool(dossier_left),
        "D3": bool(dossier_bas),  "D4": bool(dossier_bas), "D5": bool(dossier_bas),
        "D6": bool(dossier_right),
    }
    pts["_acc"]={"L":acc_left, "R":acc_right}
    return pts

def build_polys_U1F_v2(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True, dossier_right=True,
                       acc_left=True, acc_right=True):
    polys={"angle": [], "banquettes": [], "dossiers": [], "accoudoirs": []}
    d={"D1":dossier_left,"D2":dossier_left,"D3":dossier_bas,"D4":dossier_bas,"D5":dossier_bas,"D6":dossier_right}

    polys["angle"].append([pts["F0"], pts["Fx"], pts["Fx2"], pts["Fy2"], pts["Fy"], pts["F0"]])

    split_any=False
    for ban in (
        [pts["Fy"], pts["Fy2"], pts["By2"], pts["By"], pts["Fy"]],
        [pts["Fx2"], pts["Fx"], pts["F02"], pts["Bx2"], pts["Fx2"]],
        [pts["By3"], pts["Fy3"], pts["Bx2"], pts["By4"], pts["By3"]],
    ):
        pieces, split = _split_banquette_if_needed_U1F(ban)
        polys["banquettes"] += pieces
        split_any = split_any or split

    # D1 avec By_dL
    if d["D1"]: polys["dossiers"].append([pts["Dy"], pts["Dy2"], pts["By_dL"], pts["Fy"], pts["Dy"]])
    if d["D2"]: polys["dossiers"].append([pts["D0x"], pts["D0"], pts["Dy"], pts["Fy"], pts["D0x"]])
    if d["D3"]: polys["dossiers"].append([pts["D0x"], pts["Dx"], pts["Fx"], pts["F0"], pts["D0x"]])
    if d["D4"]: polys["dossiers"].append([pts["Dx"], pts["Dx2"], pts["F02"], pts["Fx"], pts["Dx"]])
    if d["D5"]: polys["dossiers"].append([pts["Dx2"], pts["D02"], pts["Dy3"], pts["Bx2"], pts["Dx2"]])
    if d["D6"]: polys["dossiers"].append([pts["Dy3"], pts["Bx2"], pts["By4_d"], pts["Dy4"], pts["Dy3"]])

    if acc_left:
        if d["D1"]:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_"], pts["Ay2"], pts["By2"], pts["By"], pts["Ay_"]])
    if acc_right:
        if d["D6"]:
            dy_top = pts.get("Dy4", pts.get("Dy3"))
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], dy_top, pts["By3"]])
        else:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax_par"], pts["By4"], pts["By3"]])

    polys["split_flags"]={"any":split_any}
    return polys

def compute_points_U1F_v3(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                          dossier_left=True, dossier_bas=True, dossier_right=True,
                          acc_left=True, acc_right=True,
                          meridienne_side=None, meridienne_len=0):
    if meridienne_side == 'g' and acc_left:
        raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
    if meridienne_side == 'd' and acc_right:
        raise ValueError("Méridienne droite interdite avec accoudoir droit.")

    A = profondeur + 20
    F0x = 10 if dossier_left else 0
    F0y = 10 if dossier_bas  else 0

    pts = {}
    pts["D0"]=(0,0); pts["D0x"]=(F0x,0); pts["D0y"]=(0,F0y); pts["F0"]=(F0x, F0y)

    # Gauche
    pts["Fx"]  = (F0x + profondeur, F0y)
    pts["Fx2"] = (F0x + profondeur, F0y + profondeur)
    pts["Dx"]  = (F0x + profondeur, 0)

    top_y_L_full = ty_left - (ACCOUDOIR_THICK if acc_left else 0)
    top_y_L_dos  = (max(F0y + A, top_y_L_full - meridienne_len) if meridienne_side == 'g' else top_y_L_full)
    pts["By"]=(F0x, top_y_L_full); pts["By2"]=(F0x + profondeur, top_y_L_full)
    pts["Dy"]=(0, F0y + A); pts["Dy2"]=(0, top_y_L_dos); pts["By_dL"]=(F0x, top_y_L_dos)
    pts["Ay"]=(0, ty_left); pts["Ay2"]=(F0x + profondeur, ty_left); pts["Ay_"]=(F0x, ty_left)

    # Droite globale
    F02x = tx - (10 if dossier_right else 0)
    pts["F02"]=(F02x, F0y)
    pts["D02x"]=(F02x, 0)

    # Assise bas (côté angle)
    bx_x = F02x - (profondeur + 20)
    pts["Bx"]=(bx_x, F0y); pts["Bx2"]=(bx_x, F0y + profondeur); pts["Dx2"]=(bx_x, 0)

    # Colonne droite et hautesurs
    col_x = F02x - profondeur
    top_y_R_full = tz_right - (ACCOUDOIR_THICK if acc_right else 0)
    top_y_R_dos  = (max(F0y + A, top_y_R_full - meridienne_len) if meridienne_side == 'd' else top_y_R_full)
    pts["Fy"]  = (col_x, F0y + A)
    pts["Fy2"] = (F02x,  F0y + A)
    pts["By3"] = (col_x, top_y_R_full)
    pts["By4"] = (F02x,  top_y_R_full)
    pts["By4_d"]=(F02x,  top_y_R_dos)
    pts["D02"]  = (tx, 0)
    pts["D02y"] = (tx, F0y)
    pts["Dy3"]  = (tx, top_y_R_dos)
    pts["Dy2R"] = (tx, F0y + A)  # pour D5/D6

    pts["Ax"]=(col_x, tz_right); pts["Ax2"]=(tx, tz_right); pts["Ax_par"]=(F02x, tz_right)

    if not dossier_bas:
        pts["D0y"]=(0, 0); pts["D02y"]=(tx, 0)

    # Bornes coussins (arrêt si méridienne)
    pts["By_cush"]  = (pts["By"][0],  min(pts["By"][1],  pts["Dy2"][1]))
    pts["By4_cush"] = (pts["By4"][0], min(pts["By4"][1], pts["By4_d"][1]))

    pts["_A"]=A; pts["_ty_canvas"]=max(ty_left, tz_right)
    pts["_draw"] = {"D1":bool(dossier_left), "D2":bool(dossier_bas), "D3":bool(dossier_bas),
                    "D4":bool(dossier_bas), "D5":bool(dossier_right), "D6":bool(dossier_right)}
    pts["_acc"]={"L":acc_left, "R":acc_right}
    return pts

def build_polys_U1F_v3(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True, dossier_right=True,
                       acc_left=True, acc_right=True):
    polys={"angle": [], "banquettes": [], "dossiers": [], "accoudoirs": []}
    d={"D1":dossier_left,"D2":dossier_bas,"D3":dossier_bas,"D4":dossier_bas,"D5":dossier_right,"D6":dossier_right}

    # Banquettes
    split_any=False
    ban_g = [pts["F0"], pts["By"], pts["By2"], pts["Fx"],  pts["F0"]]
    ban_b = [pts["Fx"], pts["Bx"], pts["Bx2"], pts["Fx2"], pts["Fx"]]
    ban_d = [pts["Fy"], pts["By3"], pts["By4"], pts["Fy2"], pts["Fy"]]
    for ban in (ban_g, ban_b, ban_d):
        pieces, split = _split_banquette_if_needed_U1F(ban)
        polys["banquettes"] += pieces
        split_any = split_any or split

    # Angle fromage gauche
    polys["angle"].append([pts["Bx"], pts["F02"], pts["Fy2"], pts["Fy"], pts["Bx2"], pts["Bx"]])

    # Dossiers
    if d["D1"]:
        polys["dossiers"].append([pts["D0x"], pts["By_dL"], pts["Dy2"], pts["D0"],  pts["D0x"]])
    if d["D2"]:
        polys["dossiers"].append([pts["D0x"], pts["Dx"],   pts["Fx"],  pts["F0"],  pts["D0x"]])
    if d["D3"]:
        polys["dossiers"].append([pts["Dx"],  pts["Dx2"],  pts["Bx"],  pts["Fx"],  pts["Dx"]])
    if d["D4"]:
        polys["dossiers"].append([pts["Dx2"], (pts["F02"][0],0), pts["F02"], pts["Bx"], pts["Dx2"]])
    if d["D5"]:
        polys["dossiers"].append([pts["D02x"], pts["Fy2"], pts["Dy2R"], pts["D02"], pts["D02x"]])
    if d["D6"]:
        polys["dossiers"].append([pts["Dy2R"], pts["Fy2"], pts["By4_d"], pts["Dy3"], pts["Dy2R"]])

    # Accoudoirs
    if acc_left:
        if d["D1"]:
            polys["accoudoirs"].append([pts["Ay"],  pts["Ay2"],  pts["By2"],  pts["Dy2"],  pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_"], pts["Ay2"],  pts["By2"],  pts["By"],   pts["Ay_"]])
    if acc_right:
        if d["D5"] or d["D6"]:
            dy_top = pts.get("Dy3", pts.get("Dy4"))
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], dy_top, pts["By3"]])
        else:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax_par"], pts["By4"], pts["By3"]])

    polys["split_flags"]={"any":split_any}
    return polys

def compute_points_U1F_v4(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                          dossier_left=True, dossier_bas=True, dossier_right=True,
                          acc_left=True, acc_right=True,
                          meridienne_side=None, meridienne_len=0):
    if meridienne_side == 'g' and acc_left:
        raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
    if meridienne_side == 'd' and acc_right:
        raise ValueError("Méridienne droite interdite avec accoudoir droit.")

    A, F0x, F0y = _common_offsets_u1f(profondeur, dossier_left, dossier_bas, dossier_right)
    F02x = tx - (10 if dossier_right else 0)

    pts={}
    pts["D0"]=(0,0); pts["D0x"]=(F0x,0); pts["D0y"]=(0,F0y); pts["F0"]=(F0x,F0y)

    # GAUCHE
    pts["Dy"]=(0, F0y+profondeur)
    top_y_L_full = ty_left - (ACCOUDOIR_THICK if acc_left else 0)
    top_y_L_dos  = top_y_L_full if meridienne_side!='g' else max(F0y+profondeur, top_y_L_full - meridienne_len)

    pts["Fy"]=(F0x, F0y+profondeur); pts["Fy2"]=(F0x+profondeur, F0y+profondeur)
    pts["By"]=(F0x, top_y_L_full);   pts["By2"]=(F0x+profondeur, top_y_L_full)
    pts["Dy2"]=(0, top_y_L_dos)
    pts["By_dL"]=(F0x, top_y_L_dos)
    pts["Ay"]=(0, ty_left); pts["Ay2"]=(F0x+profondeur, ty_left); pts["Ay_"]=(F0x, ty_left)

    # BAS + angle droite
    pts["Fx"]=(F0x+profondeur, F0y); pts["Fx2"]=(F0x+profondeur, F0y+profondeur)
    bx_x = F02x - (profondeur+20)
    pts["Bx"]=(bx_x, F0y); pts["Bx2"]=(bx_x, F0y+profondeur); pts["Dx"]=(bx_x, 0)

    # DROITE
    col_x = F02x - profondeur
    top_y_R_full = tz_right - (ACCOUDOIR_THICK if acc_right else 0)
    top_y_R_dos  = top_y_R_full if meridienne_side!='d' else max(F0y + (profondeur+20), top_y_R_full - meridienne_len)

    pts["Fy3"]=(col_x, F0y + (profondeur+20)); pts["Fy4"]=(F02x, F0y + (profondeur+20))
    pts["By3"]=(col_x, top_y_R_full); pts["By4"]=(F02x, top_y_R_full); pts["By4_d"]=(F02x, top_y_R_dos)
    pts["Ax"]=(col_x, tz_right); pts["Ax2"]=(tx, tz_right); pts["Ax_par"]=(F02x, tz_right)

    pts["D02x"]=(F02x, 0); pts["F02"]=(F02x, F0y)
    pts["D02"]=(tx, 0); pts["D02y"]=(tx, F0y)
    pts["Dy3"]=(tx, F0y + (profondeur+20)); pts["Dy4"]=(tx, top_y_R_dos)

    if not dossier_bas:
        pts["D0y"]=(0,0); pts["D02y"]=(tx,0)

    pts["By_cush"]  = (pts["By"][0],  min(pts["By"][1],  top_y_L_dos))
    pts["By4_cush"] = (pts["By4"][0], min(pts["By4"][1], top_y_R_dos))

    pts["_A"]=profondeur+20; pts["_ty_canvas"]=max(ty_left, tz_right)
    pts["_draw"]={
        "D1": bool(dossier_left), "D2": bool(dossier_left),
        "D3": bool(dossier_bas),  "D4": bool(dossier_bas),
        "D5": bool(dossier_right),"D6": bool(dossier_right),
    }
    pts["_acc"]={"L":acc_left, "R":acc_right}
    return pts

def build_polys_U1F_v4(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True, dossier_right=True,
                       acc_left=True, acc_right=True):
    polys={"angle": [], "banquettes": [], "dossiers": [], "accoudoirs": []}
    d=pts["_draw"]

    split_any=False
    for ban in (
        [pts["Fy"], pts["By"], pts["By2"], pts["Fy2"], pts["Fy"]],
        [pts["F0"], pts["Bx"], pts["Bx2"], pts["Fy"],  pts["F0"]],
        [pts["Fy4"], pts["By4"], pts["By3"], pts["Fy3"], pts["Fy4"]],
    ):
        pieces, split = _split_banquette_if_needed_U1F(ban)
        polys["banquettes"] += pieces
        split_any = split_any or split

    polys["angle"].append([pts["Bx"], pts["F02"], pts["Fy4"], pts["Fy3"], pts["Bx2"], pts["Bx"]])

    if d["D1"]:
        polys["dossiers"].append([pts["Dy"], pts["Dy2"], pts["By_dL"], pts["Fy"], pts["Dy"]])
    if d["D2"]:
        polys["dossiers"].append([pts["D0x"], pts["D0"], pts["Dy"], pts["Fy"], pts["D0x"]])
    if d["D3"]:
        polys["dossiers"].append([pts["F0"], pts["Bx"], pts["Dx"], pts["D0x"], pts["F0"]])
    if d["D4"]:
        polys["dossiers"].append([pts["Dx"], pts["D02x"], pts["F02"], pts["Bx"], pts["Dx"]])
    if d["D5"]:
        polys["dossiers"].append([pts["D02x"], pts["Fy4"], pts["Dy3"], pts["D02"], pts["D02x"]])
    if d["D6"]:
        polys["dossiers"].append([pts["Dy3"], pts["Fy4"], pts["By4_d"], pts["Dy4"], pts["Dy3"]])

    if acc_left:
        if d["D1"]:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_"], pts["Ay2"], pts["By2"], pts["By"], pts["Ay_"]])

    if acc_right:
        has_right = (d["D5"] or d["D6"])
        if has_right:
            dy_top = pts.get("Dy4", pts.get("Dy3"))
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], dy_top, pts["By3"]])
        else:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax_par"], pts["By4"], pts["By3"]])

    polys["split_flags"]={"any":split_any}
    return polys

# --- rendu commun + wrappers (U1F) ---
def _render_common_U1F(variant, tx, ty, tz, profondeur,
                       dossier_left, dossier_bas, dossier_right,
                       acc_left, acc_right,
                       meridienne_side, meridienne_len,
                       coussins, traversins, couleurs, window_title):
    comp = {"v1":compute_points_U1F_v1, "v2":compute_points_U1F_v2,
            "v3":compute_points_U1F_v3, "v4":compute_points_U1F_v4}[variant]
    build= {"v1":build_polys_U1F_v1,   "v2":build_polys_U1F_v2,
            "v3":build_polys_U1F_v3,   "v4":build_polys_U1F_v4}[variant]

    trv = _parse_traversins_spec(traversins, allowed={"g","d"})
    legend_items = _resolve_and_apply_colors(couleurs)

    pts = comp(tx, ty, tz, profondeur,
               dossier_left, dossier_bas, dossier_right,
               acc_left, acc_right,
               meridienne_side, meridienne_len)
    polys = build(pts, tx, ty, tz, profondeur,
                  dossier_left, dossier_bas, dossier_right,
                  acc_left, acc_right)
    _assert_banquettes_max_250(polys)

    ty_canvas = max(ty, tz)
    screen = turtle.Screen(); screen.setup(WIN_W, WIN_H)
    screen.title(f"U1F {variant} — {window_title} — tx={tx} / ty={ty} / tz={tz} — prof={profondeur}")
    t = turtle.Turtle(visible=False); t.speed(0); screen.tracer(False)
    tr = WorldToScreen(tx, ty_canvas, WIN_W, WIN_H, PAD_PX, ZOOM)

    # (Quadrillage et repères supprimés)

    for p in polys["dossiers"]:
        xs=[pp[0] for pp in p]; ys=[pp[1] for pp in p]
        if (max(xs)-min(xs) > 1e-9) and (max(ys)-min(ys) > 1e-9):
            draw_polygon_cm(t, tr, p, fill=COLOR_DOSSIER)
    for p in polys["banquettes"]: draw_polygon_cm(t, tr, p, fill=COLOR_ASSISE)
    for p in polys["accoudoirs"]: draw_polygon_cm(t, tr, p, fill=COLOR_ACC)
    for p in polys["angle"]:      draw_polygon_cm(t, tr, p, fill=COLOR_ASSISE)

    # Traversins + comptage
    n_traversins = _draw_traversins_U_side_F02(t, tr, pts, profondeur, trv)

    draw_double_arrow_vertical_cm(t, tr, -25,   0, ty,   f"{ty} cm")
    draw_double_arrow_vertical_cm(t, tr,  tx+25,0, tz,   f"{tz} cm")
    draw_double_arrow_horizontal_cm(t, tr, -25, 0, tx,   f"{tx} cm")

    A = pts["_A"]
    if polys["angle"]:
        label_poly(t, tr, polys["angle"][0], f"{A}×{A} cm")
    banquette_sizes=[]
    for poly in polys["banquettes"]:
        L,P = banquette_dims(poly); banquette_sizes.append((L,P))
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        bb_w=max(xs)-min(xs); bb_h=max(ys)-min(ys)
        text=f"{L}×{P} cm"
        if bb_h >= bb_w: label_poly_offset_cm(t,tr,poly,text,dx_cm=CUSHION_DEPTH+10,dy_cm=0)
        else:            label_poly(t,tr,poly,text)
    for p in polys["dossiers"]:
        xs=[pp[0] for pp in p]; ys=[pp[1] for pp in p]
        if (max(xs)-min(xs) > 1e-9) and (max(ys)-min(ys) > 1e-9):
            label_poly(t,tr,p,"10")
    for p in polys["accoudoirs"]:
        xs=[pp[0] for pp in p]; ys=[pp[1] for pp in p]
        if (max(xs)-min(xs) > 1e-9) and (max(ys)-min(ys) > 1e-9):
            label_poly(t,tr,p,"15")

    # ===== COUSSINS =====
    spec = _parse_coussins_spec(coussins)
    if spec["mode"] == "auto":
        size = _choose_cushion_size_auto_U1F(pts, traversins=trv)
        nb_coussins = _draw_coussins_U1F(t, tr, pts, size, traversins=trv)
        total_line = f"{coussins} → {nb_coussins} × {size} cm"
    elif spec["mode"] == "fixed":
        size = int(spec["fixed"])
        nb_coussins = _draw_coussins_U1F(t, tr, pts, size, traversins=trv)
        total_line = f"{coussins} → {nb_coussins} × {size} cm"
    else:
        best = _optimize_valise_U1F(pts, spec["range"], spec["same"], traversins=trv)
        if not best:
            raise ValueError("Aucune configuration valise valide pour U1F.")
        sizes = best["sizes"]; shiftL, shiftR = best["shifts"]
        nb_coussins = _draw_U1F_with_sizes(t, tr, pts, sizes, shiftL, shiftR, traversins=trv)
        sb, sg, sd = sizes["bas"], sizes["gauche"], sizes["droite"]
        total_line = f"bas={sb} / gauche={sg} / droite={sd} (Δ={max(sb,sg,sd)-min(sb,sg,sd)}) — total: {nb_coussins}"

    # Titre + légende (U → haut-centre)
    draw_title_center(t, tr, tx, ty_canvas, "Canapé en U avec un angle")
    draw_legend(t, tr, tx, ty_canvas, items=legend_items, pos="top-center")

    screen.tracer(True); t.hideturtle()

    add_split = int(polys.get("split_flags",{}).get("any",False))
    print(f"=== Rapport U1F {variant} ===")
    print(f"Dimensions : tx={tx} / ty={ty} / tz={tz} — profondeur={profondeur} (A={A})")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers : {len(polys['dossiers'])} (+{add_split} via scission) | Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 1")
    print(f"Angles : 1 × {A}×{A} cm")
    print(f"Traversins : {n_traversins} × 70x30")
    print(f"Coussins : {total_line}")
    turtle.done()

def render_U1F_v1(*args, **kwargs):
    if "traversins" not in kwargs: kwargs["traversins"]=None
    if "couleurs" not in kwargs: kwargs["couleurs"]=None
    _render_common_U1F("v1", *args, **kwargs)
def render_U1F_v2(*args, **kwargs):
    if "traversins" not in kwargs: kwargs["traversins"]=None
    if "couleurs" not in kwargs: kwargs["couleurs"]=None
    _render_common_U1F("v2", *args, **kwargs)
def render_U1F_v3(*args, **kwargs):
    if "traversins" not in kwargs: kwargs["traversins"]=None
    if "couleurs" not in kwargs: kwargs["couleurs"]=None
    _render_common_U1F("v3", *args, **kwargs)
def render_U1F_v4(*args, **kwargs):
    if "traversins" not in kwargs: kwargs["traversins"]=None
    if "couleurs" not in kwargs: kwargs["couleurs"]=None
    _render_common_U1F("v4", *args, **kwargs)

# =====================================================================
# ======================  L (no fromage) v1 + v2  =====================
# =====================================================================
def compute_points_LNF_v2(tx, ty, profondeur=DEPTH_STD,
                          dossier_left=True, dossier_bas=True,
                          acc_left=True, acc_bas=True,
                          meridienne_side=None, meridienne_len=0):
    prof = profondeur; pts = {}
    if dossier_left and dossier_bas:         F0x, F0y = 10, 10; D0x0=(10,0); D0y0=(0,10)
    elif (not dossier_left) and dossier_bas: F0x, F0y = 0, 10;  D0x0=(0,0);  D0y0=(0,10)
    elif dossier_left and (not dossier_bas): F0x, F0y = 10, 0;  D0x0=(10,0); D0y0=(0,0)
    else:                                    F0x, F0y = 0, 0;   D0x0=(0,0);  D0y0=(0,0)

    pts["D0"]=(0,0); pts["D0x"]=D0x0; pts["D0y"]=D0y0; pts["F0"]=(F0x,F0y)

    top_y = ty - (ACCOUDOIR_THICK if acc_left else 0)
    pts["Dy"]  =(0, F0y+prof); pts["Dy2"]=(0, top_y); pts["Ay"]=(0, ty)
    pts["Fy"]  =(F0x, F0y+prof); pts["By"]=(F0x, top_y)
    pts["Ay2"] =(F0x+prof, ty); pts["By2"]=(F0x+prof, top_y); pts["Ay_par"]=(F0x, ty)

    stop_x = tx - (ACCOUDOIR_THICK if acc_bas else 0)
    pts["Dx"]=(stop_x,0); pts["Bx"]=(stop_x,F0y); pts["Bx2"]=(stop_x,F0y+prof)
    pts["Ax"]=(tx,0); pts["Ax2"]=(tx,F0y+prof); pts["Ax_par"]=(tx,F0y)

    if meridienne_side=='g' and meridienne_len>0:
        mer_y=max(pts["Fy"][1], top_y - meridienne_len); mer_y=min(mer_y, top_y)
        pts["By_mer"]=(pts["By"][0],mer_y); pts["By2_mer"]=(pts["By2"][0],mer_y); pts["Dy2"]=(0,mer_y)
    if meridienne_side=='b' and meridienne_len>0:
        mer_x=min(stop_x, tx - meridienne_len)
        pts["Bx_mer"]=(mer_x, pts["Bx"][1]); pts["Bx2_mer"]=(mer_x, pts["Bx2"][1]); pts["Dx_mer"]=(mer_x,0)

    pts["_tx"], pts["_ty"] = tx, ty
    return pts

def build_polys_LNF_v2(pts, tx, ty, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True,
                       acc_left=True, acc_bas=True,
                       meridienne_side=None, meridienne_len=0):
    polys={"banquettes":[],"dossiers":[],"accoudoirs":[]}

    Fy=(pts["Fy"][0], pts["Fy"][1]); Fy2=(pts["Fy"][0]+profondeur, pts["Fy"][1])
    By=pts.get("By"); By2=pts.get("By2")
    ban_g=[Fy, By, By2, Fy2, Fy]
    split_left=False; mid_y_left=None
    Lg = abs(By2[1] - Fy2[1])
    if Lg > SPLIT_THRESHOLD:
        split_left=True; mid_y_left=_split_mid_int(Fy2[1], By2[1])
        low  = [(Fy[0],Fy[1]),(Fy2[0],Fy2[1]),(Fy2[0],mid_y_left),(Fy[0],mid_y_left),(Fy[0],Fy[1])]
        high = [(Fy[0],mid_y_left),(Fy2[0],mid_y_left),(By2[0],By2[1]),(By[0],By[1]),(Fy[0],mid_y_left)]
        polys["banquettes"] += [low, high]
    else:
        polys["banquettes"].append(ban_g)

    F0=pts["F0"]; Bx=pts["Bx"]; Bx2=pts["Bx2"]
    ban_b=[F0, Bx, Bx2, pts["Fy"], F0]
    split_bas=False; mid_x_bas=None
    Lb = abs(Bx2[0] - pts["Fy"][0])
    if Lb > SPLIT_THRESHOLD:
        split_bas=True; mid_x_bas=_split_mid_int(pts["Fy"][0], Bx2[0])
        left  = [(F0[0],F0[1]),(mid_x_bas,F0[1]),(mid_x_bas,pts["Fy"][1]),(pts["Fy"][0],pts["Fy"][1]),(F0[0],F0[1])]
        right = [(mid_x_bas,F0[1]),(Bx[0],Bx[1]),(Bx2[0],Bx2[1]),(mid_x_bas,pts["Fy"][1]),(mid_x_bas,F0[1])]
        polys["banquettes"] += [left, right]
    else:
        polys["banquettes"].append(ban_b)

    if dossier_left:
        if split_left:
            F0x=pts["F0"][0]; y0=pts["Dy"][1]; yTop=pts.get("By_mer", pts["By"])[1]
            d1b=[(0,y0),(F0x,y0),(F0x,mid_y_left),(0,mid_y_left),(0,y0)]
            d1h=[(0,mid_y_left),(F0x,mid_y_left),(F0x,yTop),(0,yTop),(0,mid_y_left)]
            polys["dossiers"] += [d1b, d1h]
        else:
            By_use = pts.get("By_mer", pts["By"])
            polys["dossiers"].append([pts["Dy2"], By_use, pts["Fy"], pts["Dy"], pts["Dy2"]])
    if dossier_left:
        polys["dossiers"].append([pts["D0x"], pts["D0"], pts["Dy"], pts["Fy"], pts["D0x"]])
    if dossier_bas:
        Bx_use = pts.get("Bx_mer", pts["Bx"]); Dx_use = pts.get("Dx_mer", pts["Dx"])
        if split_bas:
            yTop=pts["F0"][1]
            d3g=[(mid_x_bas,0),(pts["D0x"][0],0),(pts["D0x"][0],yTop),(mid_x_bas,yTop),(mid_x_bas,0)]
            d3d=[(Dx_use[0],0),(mid_x_bas,0),(mid_x_bas,yTop),(Bx_use[0],yTop),(Dx_use[0],0)]
            polys["dossiers"] += [d3g, d3d]
        else:
            polys["dossiers"].append([Dx_use, pts["D0x"], pts["F0"], Bx_use, Dx_use])

    if acc_left:
        if dossier_left:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["By"], pts["Ay_par"], pts["Ay2"], pts["By2"], pts["By"]])
    if acc_bas:
        if dossier_bas:
            polys["accoudoirs"].append([pts["Dx"], pts["Ax"], pts["Ax2"], pts["Bx2"], pts["Dx"]])
        else:
            polys["accoudoirs"].append([pts["Bx"], pts["Ax_par"], pts["Ax2"], pts["Bx2"], pts["Bx"]])

    polys["split_flags"]={"left":split_left,"bottom":split_bas}
    return polys

def compute_points_LNF_v1(tx, ty, profondeur=DEPTH_STD,
                          dossier_left=True, dossier_bas=True,
                          acc_left=True, acc_bas=True,
                          meridienne_side=None, meridienne_len=0):
    prof=profondeur; pts={}
    if dossier_left and dossier_bas:         F0x,F0y=10,10; D0x0=(10,0); D0y0=(0,10)
    elif (not dossier_left) and dossier_bas: F0x,F0y=0,10;  D0x0=(0,0);  D0y0=(0,10)
    elif dossier_left and (not dossier_bas): F0x,F0y=10,0;  D0x0=(10,0); D0y0=(0,0)
    else:                                    F0x,F0y=0,0;   D0x0=(0,0);  D0y0=(0,0)

    pts["D0"]=(0,0); pts["D0x"]=D0x0; pts["D0y"]=D0y0; pts["F0"]=(F0x,F0y)
    top_y = ty - (ACCOUDOIR_THICK if acc_left else 0)
    pts["Dy2"]=(0, top_y); pts["Ay"] =(0, ty); pts["By"] =(F0x, top_y)
    pts["Ay2"]=(F0x+prof, ty); pts["By2"]=(F0x+prof, top_y)

    stop_x = tx - (ACCOUDOIR_THICK if acc_bas else 0)
    pts["Dy"] =(0, F0y+prof)
    pts["Fx"] =(F0x+prof, F0y); pts["Fx2"]=(F0x+prof, F0y+prof)
    pts["Bx"] =(stop_x, F0y);   pts["Bx2"]=(stop_x, F0y+prof)
    pts["Dx"] =(F0x+prof, 0);   pts["DxR"]=(stop_x, 0)
    pts["Ax"] =(tx, 0); pts["Ax2"]=(tx, F0y+prof)
    pts["Ay_par"]=(F0x, ty); pts["Ax_par"]=(tx, F0y)

    if meridienne_side=='g' and meridienne_len>0:
        mer_y=max(F0y, top_y - meridienne_len); mer_y=min(mer_y, top_y)
        pts["By_mer"]=(pts["By"][0],mer_y); pts["By2_mer"]=(pts["By2"][0],mer_y); pts["Dy2"]=(0,mer_y)
    if meridienne_side=='b' and meridienne_len>0:
        mer_x=min(stop_x, tx - meridienne_len)
        pts["Bx_mer"]=(mer_x, pts["Bx"][1]); pts["Bx2_mer"]=(mer_x, pts["Bx2"][1]); pts["DxR_mer"]=(mer_x,0)
    pts["_tx"], pts["_ty"]=tx,ty
    return pts

def build_polys_LNF_v1(pts, tx, ty, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True,
                       acc_left=True, acc_bas=True,
                       meridienne_side=None, meridienne_len=0):
    polys={"banquettes":[], "dossiers":[], "accoudoirs":[]}

    F0=pts["F0"]; Fx=pts["Fx"]; By=pts.get("By"); By2=pts.get("By2")
    ban_g=[F0, By, By2, Fx, F0]
    split_left=False; mid_y_left=None
    top_y = (pts.get("By2_mer", By2))[1]; base_y = F0[1]
    Lg = abs(top_y - base_y)
    if Lg > SPLIT_THRESHOLD:
        split_left=True; mid_y_left=_split_mid_int(base_y, top_y)
        lower=[(F0[0],base_y),(Fx[0],base_y),(Fx[0],mid_y_left),(F0[0],mid_y_left),(F0[0],base_y)]
        upper=[(F0[0],mid_y_left),(Fx[0],mid_y_left),(By2[0],top_y),(By[0],top_y),(F0[0],mid_y_left)]
        polys["banquettes"] += [lower, upper]
    else:
        polys["banquettes"].append(ban_g)

    Bx=pts["Bx"]; Bx2=pts["Bx2"]; Fx2=pts["Fx2"]
    ban_b=[pts["Fx"], Bx, Bx2, Fx2, pts["Fx"]]
    split_bas=False; mid_x_bas=None
    Lb = abs(Bx2[0] - pts["Fx"][0])
    if Lb > SPLIT_THRESHOLD:
        split_bas=True; mid_x_bas=_split_mid_int(pts["Fx"][0], Bx2[0])
        left =[ (pts["Fx"][0], pts["Fx"][1]), (mid_x_bas, pts["Fx"][1]),
                (mid_x_bas, Fx2[1]), (Fx2[0], Fx2[1]), (pts["Fx"][0], pts["Fx"][1]) ]
        right=[ (mid_x_bas, pts["Fx"][1]), (Bx[0],Bx[1]), (Bx2[0],Bx2[1]),
                (mid_x_bas, Fx2[1]), (mid_x_bas, pts["Fx"][1]) ]
        polys["banquettes"] += [left, right]
    else:
        polys["banquettes"].append(ban_b)

    if dossier_left:
        By_use = pts.get("By_mer", pts["By"])
        if split_left:
            x0=0; x1=pts["D0x"][0]; y_base=0; y_top=By_use[1]; y_mid=mid_y_left
            d1_bas=[(x0,y_base),(x1,y_base),(x1,y_mid),(x0,y_mid),(x0,y_base)]
            d1_haut=[(x0,y_mid),(x1,y_mid),(x1,y_top),(x0,y_top),(x0,y_mid)]
            polys["dossiers"] += [d1_bas, d1_haut]
        else:
            polys["dossiers"].append([pts["D0"], pts["Dy2"], By_use, pts["D0x"], pts["D0"]])
    if dossier_left:
        polys["dossiers"].append([pts["D0x"], pts["Dx"], pts["Fx"], pts["F0"], pts["D0x"]])
    if dossier_bas:
        DxR_use = pts.get("DxR_mer", pts["DxR"]); Bx_use = pts.get("Bx_mer", pts["Bx"])
        if split_bas:
            yTop=pts["F0"][1]
            d3_g=[(mid_x_bas,0),(pts["Dx"][0],0),(pts["Dx"][0],yTop),(mid_x_bas,yTop),(mid_x_bas,0)]
            d3_d=[(DxR_use[0],0),(mid_x_bas,0),(mid_x_bas,yTop),(Bx_use[0],yTop),(DxR_use[0],0)]
            polys["dossiers"] += [d3_g, d3_d]
        else:
            polys["dossiers"].append([pts["Dx"], DxR_use, Bx_use, pts["Fx"], pts["Dx"]])

    if acc_left:
        if dossier_left:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_par"], pts["Ay2"], pts["By2"], pts["By"], pts["Ay_par"]])
    if acc_bas:
        if dossier_bas:
            polys["accoudoirs"].append([pts["DxR"], pts["Ax"], pts["Ax2"], pts["Bx2"], pts["DxR"]])
        else:
            polys["accoudoirs"].append([pts["Bx"], pts["Ax_par"], pts["Ax2"], pts["Bx2"], pts["Bx"]])

    polys["split_flags"]={"left":split_left,"bottom":split_bas}
    return polys

def _choose_cushion_size_auto_L(pts, traversins=None):
    F0x, F0y = pts["F0"]
    x_end = pts.get("Bx_mer", pts.get("Bx", (F0x, 0)))[0]
    y_end = pts.get("By_mer", pts.get("By", (F0x, F0y)))[1]
    if traversins:
        if "b" in traversins: x_end -= TRAVERSIN_THK
        if "g" in traversins: y_end -= TRAVERSIN_THK
    usable_h = max(0, x_end - F0x)
    usable_v = max(0, y_end - (F0y + CUSHION_DEPTH))
    best=None; score_best=(1e9,-1)
    for s in (65,80,90):
        w_h = usable_h % s if usable_h>0 else 0
        w_v = usable_v % s if usable_v>0 else 0
        score=(max(w_h,w_v), -s)
        if score < score_best: score_best=score; best=s
    return best or 65

def draw_coussins_L_optimized(t, tr, pts, coussins, traversins=None):
    if isinstance(coussins, str) and coussins.strip().lower()=="auto":
        size = _choose_cushion_size_auto_L(pts, traversins=traversins)
    else:
        size = int(coussins)

    F0x, F0y = pts["F0"]
    x_end = pts.get("Bx_mer", pts["Bx"])[0]
    y_end = pts.get("By_mer", pts["By"])[1]
    if traversins:
        if "b" in traversins: x_end -= TRAVERSIN_THK
        if "g" in traversins: y_end -= TRAVERSIN_THK

    def count_bottom(x_start): return max(0, int((x_end - x_start)//size))
    def count_left(y_start):   return max(0, int((y_end - y_start)//size))

    nA = count_bottom(F0x) + count_left(F0y + CUSHION_DEPTH)  # bas collé
    nB = count_bottom(F0x + CUSHION_DEPTH) + count_left(F0y)  # bas décalé

    def draw_bottom(x_start):
        cnt=0; y=F0y; x_cur=x_start
        while x_cur + size <= x_end + 1e-6:
            poly=[(x_cur,y),(x_cur+size,y),(x_cur+size,y+CUSHION_DEPTH),(x_cur,y+CUSHION_DEPTH),(x_cur,y)]
            draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
            label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
            x_cur += size; cnt += 1
        return cnt
    def draw_left(y_start):
        cnt=0; x=F0x; y_cur=y_start
        while y_cur + size <= y_end + 1e-6:
            poly=[(x,y_cur),(x+CUSHION_DEPTH,y_cur),(x+CUSHION_DEPTH,y_cur+size),(x,y_cur+size),(x,y_cur)]
            draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
            label_poly(t,tr,poly,f"{size}",font=FONT_CUSHION)
            y_cur += size; cnt += 1
        return cnt

    # tie-break : max coussins, puis déchet minimal
    wasteA = (max(0, x_end-F0x)%size) + (max(0, y_end-(F0y+CUSHION_DEPTH))%size)
    wasteB = (max(0, x_end-(F0x+CUSHION_DEPTH))%size) + (max(0, y_end-F0y)%size)
    if (nB, -wasteB) > (nA, -wasteA):
        cb = draw_bottom(F0x + CUSHION_DEPTH); cl = draw_left(F0y)
        return cb + cl, size
    else:
        cb = draw_bottom(F0x); cl = draw_left(F0y + CUSHION_DEPTH)
        return cb + cl, size

def _render_common_L(tx, ty, pts, polys, coussins, window_title,
                     profondeur, dossier_left, dossier_bas, meridienne_side, meridienne_len,
                     traversins=None, couleurs=None):
    _assert_banquettes_max_250(polys)

    trv = _parse_traversins_spec(traversins, allowed={"g","b"})
    legend_items = _resolve_and_apply_colors(couleurs)

    screen = turtle.Screen(); screen.setup(WIN_W,WIN_H)
    screen.title(f"{window_title} — {tx}×{ty} — prof={profondeur} — méridienne {meridienne_side or '-'}={meridienne_len} — coussins={coussins}")
    t = turtle.Turtle(visible=False); t.speed(0); screen.tracer(False)
    tr = WorldToScreen(tx, ty, WIN_W, WIN_H, PAD_PX, ZOOM)

    # (Quadrillage et repères supprimés)

    for p in polys["dossiers"]:   draw_polygon_cm(t,tr,p,fill=COLOR_DOSSIER)
    for p in polys["banquettes"]: draw_polygon_cm(t,tr,p,fill=COLOR_ASSISE)
    for p in polys["accoudoirs"]: draw_polygon_cm(t,tr,p,fill=COLOR_ACC)

    # Traversins + comptage
    n_traversins = _draw_traversins_L_like(t, tr, pts, profondeur, trv)

    draw_double_arrow_vertical_cm(t,tr,-25,0,ty,f"{ty} cm")
    draw_double_arrow_horizontal_cm(t,tr,-25,0,tx,f"{tx} cm")

    banquette_sizes=[]
    for poly in polys["banquettes"]:
        L,P = banquette_dims(poly); banquette_sizes.append((L,P))
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        bb_w=max(xs)-min(xs); bb_h=max(ys)-min(ys)
        if bb_h>=bb_w: label_poly_offset_cm(t,tr,poly,f"{L}×{P} cm",dx_cm=CUSHION_DEPTH+10,dy_cm=0)
        else:          label_poly(t,tr,poly,f"{L}×{P} cm")

    for p in polys["dossiers"]:   label_poly(t,tr,p,"10")
    for p in polys["accoudoirs"]: label_poly(t,tr,p,"15")

    # ===== COUSSINS =====
    spec = _parse_coussins_spec(coussins)
    if spec["mode"] == "auto":
        cushions_count, chosen_size = draw_coussins_L_optimized(t,tr,pts,"auto", traversins=trv)
        total_line = f"{coussins} → {cushions_count} × {chosen_size} cm"
    elif spec["mode"] == "fixed":
        cushions_count, chosen_size = draw_coussins_L_optimized(t,tr,pts,int(spec["fixed"]), traversins=trv)
        total_line = f"{coussins} → {coussins} × {chosen_size} cm"
    else:
        best = _optimize_valise_L_like(pts, spec["range"], spec["same"], traversins=trv)
        if not best:
            raise ValueError("Aucune configuration valise valide pour L.")
        sizes = best["sizes"]; shift = best["shift_bas"]
        n, sb, sg = _draw_L_like_with_sizes(t, tr, pts, sizes, shift, traversins=trv)
        cushions_count = n; total_line = f"bas={sb} / gauche={sg} (Δ={abs(sb-sg)}) — total: {n}"

    # Légende
    draw_legend(t, tr, tx, ty, items=legend_items, pos="top-right")

    screen.tracer(True); t.hideturtle()

    add_split = int(polys.get("split_flags",{}).get("left",False) and dossier_left) \
              + int(polys.get("split_flags",{}).get("bottom",False) and dossier_bas)

    print("=== Rapport LNF ===")
    print(f"Dimensions : {tx}×{ty} — prof={profondeur} — méridienne {meridienne_side or '-'}={meridienne_len}")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers : {len(polys['dossiers'])} (+{add_split} via scission) | Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 0")
    print(f"Traversins : {n_traversins} × 70x30")
    print(f"Coussins : {total_line}")
    turtle.done()

def render_LNF_v1(tx, ty, profondeur=DEPTH_STD,
                  dossier_left=True, dossier_bas=True,
                  acc_left=True, acc_bas=True,
                  meridienne_side=None, meridienne_len=0,
                  coussins="auto",
                  traversins=None,
                  couleurs=None,
                  window_title="LNF v1 — pivot gauche"):
    if meridienne_side=='g':
        if acc_left: raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
        if not dossier_left: raise ValueError("Méridienne gauche impossible sans dossier gauche.")
    if meridienne_side=='b':
        if acc_bas: raise ValueError("Méridienne bas interdite avec accoudoir bas.")
        if not dossier_bas: raise ValueError("Méridienne bas impossible sans dossier bas.")
    pts = compute_points_LNF_v1(tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    polys = build_polys_LNF_v1(pts,tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    _render_common_L(tx,ty,pts,polys,coussins,window_title,profondeur,dossier_left,dossier_bas,meridienne_side,meridienne_len,traversins=traversins, couleurs=couleurs)

def render_LNF_v2(tx, ty, profondeur=DEPTH_STD,
                  dossier_left=True, dossier_bas=True,
                  acc_left=True, acc_bas=True,
                  meridienne_side=None, meridienne_len=0,
                  coussins="auto",
                  traversins=None,
                  couleurs=None,
                  window_title="LNF v2 — pivot bas"):
    if meridienne_side=='g':
        if acc_left: raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
        if not dossier_left: raise ValueError("Méridienne gauche impossible sans dossier gauche.")
    if meridienne_side=='b':
        if acc_bas: raise ValueError("Méridienne bas interdite avec accoudoir bas.")
        if not dossier_bas: raise ValueError("Méridienne bas impossible sans dossier bas.")
    pts = compute_points_LNF_v2(tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    polys = build_polys_LNF_v2(pts,tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    _render_common_L(tx,ty,pts,polys,coussins,window_title,profondeur,dossier_left,dossier_bas,meridienne_side,meridienne_len,traversins=traversins, couleurs=couleurs)

def _dry_polys_for_variant(tx, ty, profondeur,
                           dossier_left, dossier_bas,
                           acc_left, acc_bas,
                           meridienne_side, meridienne_len,
                           variant):
    if meridienne_side == 'g':
        if acc_left:        raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
        if not dossier_left:raise ValueError("Méridienne gauche impossible sans dossier gauche.")
    if meridienne_side == 'b':
        if acc_bas:         raise ValueError("Méridienne bas interdite avec accoudoir bas.")
        if not dossier_bas: raise ValueError("Méridienne bas impossible sans dossier bas.")

    if variant == "v1":
        pts = compute_points_LNF_v1(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas, meridienne_side, meridienne_len)
        polys = build_polys_LNF_v1(pts, tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas, meridienne_side, meridienne_len)
    else:
        pts = compute_points_LNF_v2(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas, meridienne_side, meridienne_len)
        polys = build_polys_LNF_v2(pts, tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas, meridienne_side, meridienne_len)
    return pts, polys

def render_LNF(tx, ty, profondeur=DEPTH_STD,
               dossier_left=True, dossier_bas=True,
               acc_left=True, acc_bas=True,
               meridienne_side=None, meridienne_len=0,
               coussins="auto",
               variant="auto",
               traversins=None,
               couleurs=None,
               window_title="LNF — auto"):
    if variant and variant.lower() in ("v1", "v2"):
        chosen = variant.lower()
        if chosen == "v2":
            render_LNF_v2(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas,
                          meridienne_side, meridienne_len, coussins, traversins=traversins, couleurs=couleurs,
                          window_title=window_title)
        else:
            render_LNF_v1(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas,
                          meridienne_side, meridienne_len, coussins, traversins=traversins, couleurs=couleurs,
                          window_title=window_title)
        return

    nb_ban_v1 = float("inf")
    nb_ban_v2 = float("inf")
    polys1 = polys2 = None
    try:
        _pts1, _polys1 = _dry_polys_for_variant(tx, ty, profondeur,
                                               dossier_left, dossier_bas,
                                               acc_left, acc_bas,
                                               meridienne_side, meridienne_len,
                                               "v1")
        nb_ban_v1 = len(_polys1["banquettes"]); polys1=_polys1
    except ValueError:
        pass
    try:
        _pts2, _polys2 = _dry_polys_for_variant(tx, ty, profondeur,
                                               dossier_left, dossier_bas,
                                               acc_left, acc_bas,
                                               meridienne_side, meridienne_len,
                                               "v2")
        nb_ban_v2 = len(_polys2["banquettes"]); polys2=_polys2
    except ValueError:
        pass

    # choix : moins de banquettes ; tie-break = moins de scissions
    def scissions(polys):
        if not polys: return 999
        base_groups = 2  # L = gauche + bas
        return max(0, len(polys["banquettes"]) - base_groups)
    if nb_ban_v1 < nb_ban_v2: chosen = "v1"
    elif nb_ban_v2 < nb_ban_v1: chosen = "v2"
    else:
        if scissions(polys1) < scissions(polys2): chosen="v1"
        elif scissions(polys2) < scissions(polys1): chosen="v2"
        else: chosen = "v1" if tx >= ty else "v2"

    if chosen == "v2":
        render_LNF_v2(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas,
                      meridienne_side, meridienne_len, coussins, traversins=traversins, couleurs=couleurs,
                      window_title=window_title)
    else:
        render_LNF_v1(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas,
                      meridienne_side, meridienne_len, coussins, traversins=traversins, couleurs=couleurs,
                      window_title=window_title)

# =====================================================================
# =====================  U (no fromage) — v1..v4  =====================
# =====================================================================

def compute_points_U_v1(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                        dossier_left=True, dossier_bas=True, dossier_right=True,
                        acc_left=True, acc_bas=True, acc_right=True):
    prof = profondeur; pts={}
    F0x = 10 if dossier_left else 0
    F0y = 10 if dossier_bas  else 0
    pts["D0"]=(0,0); pts["D0x"]=(F0x,0); pts["D0y"]=(0,F0y); pts["F0"]=(F0x,F0y)

    # gauche
    pts["Dy"]  = (0, F0y+prof)
    top_y_L = ty_left - (ACCOUDOIR_THICK if acc_left else 0)
    pts["Dy2"] = (0, top_y_L)
    pts["Ay"]  = (0, ty_left); pts["Ay2"] = (F0x+prof, ty_left); pts["Ay_"]=(F0x, ty_left)

    pts["Fy"]  = (F0x,      F0y+prof)
    pts["Fy2"] = (F0x+prof, F0y+prof)
    pts["By"]  = (F0x,      top_y_L)
    pts["By2"] = (F0x+prof, top_y_L)

    # droite (branche au-dessus du bas)
    D02x_x = tx - (10 if (dossier_right or dossier_bas) else 0)
    pts["Dx"]  = (F0x+prof, 0)
    pts["Bx"]  = (D02x_x, F0y); pts["Bx2"]=(D02x_x, F0y+prof)

    top_y_R   = tz_right - (ACCOUDOIR_THICK if acc_right else 0)
    x_left_R  = D02x_x - prof
    pts["Fy3"] = (x_left_R, F0y+prof); pts["By3"]=(x_left_R, top_y_R); pts["By4"]=(D02x_x, top_y_R)

    pts["D02x"]=(D02x_x,0); pts["D02"]=(tx,0); pts["D02y"]=(tx,F0y); pts["Dy3"]=(tx, top_y_R)
    pts["Ax"]=(x_left_R, tz_right); pts["Ax2"]=(tx, tz_right); pts["Ax_par"]=(D02x_x, tz_right)

    pts["_ty_canvas"]=max(ty_left, tz_right)
    return pts

def build_polys_U_v1(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                     dossier_left=True, dossier_bas=True, dossier_right=True,
                     acc_left=True, acc_bas=True, acc_right=True):
    polys={"banquettes":[],"dossiers":[],"accoudoirs":[]}

    draw = {
        "D1": bool(dossier_left),
        "D2": bool(dossier_left or dossier_bas),
        "D3": bool(dossier_bas),
        "D4": bool(dossier_right),              # v1 : uniquement dossier_droit
        "D5": bool(dossier_right),
    }

    F0=pts["F0"]; Fy=pts["Fy"]; Fy2=pts["Fy2"]; By=pts["By"]; By2=pts["By2"]
    Bx=pts["Bx"]; Bx2=pts["Bx2"]; Fy3=pts["Fy3"]; By3=pts["By3"]; By4=pts["By4"]

    # banquettes
    split_left=split_bottom=split_right=False
    ban_g=[Fy,By,By2,Fy2,Fy]
    Lg=abs(By[1]-Fy[1])
    if Lg>SPLIT_THRESHOLD:
        split_left=True
        mid_y=_split_mid_int(Fy[1],By[1])
        g_low=[(Fy[0],Fy[1]),(Fy2[0],Fy[1]),(Fy2[0],mid_y),(Fy[0],mid_y),(Fy[0],Fy[1])]
        g_up=[(Fy[0],mid_y),(By[0],By[1]),(By2[0],By2[1]),(Fy2[0],mid_y),(Fy[0],mid_y)]
        polys["banquettes"]+=[g_low,g_up]
    else:
        polys["banquettes"].append(ban_g)

    ban_b=[F0,Bx,Bx2,Fy,F0]
    Lb=abs(Bx[0]-F0[0])
    if Lb>SPLIT_THRESHOLD:
        split_bottom=True
        mid_x=_split_mid_int(F0[0],Bx[0])
        b_left=[(F0[0],F0[1]),(mid_x,F0[1]),(mid_x,Fy[1]),(Fy[0],Fy[1]),(F0[0],F0[1])]
        b_right=[(mid_x,F0[1]),(Bx[0],Bx[1]),(Bx2[0],Bx2[1]),(mid_x,Fy[1]),(mid_x,F0[1])]
        polys["banquettes"]+=[b_left,b_right]
    else:
        polys["banquettes"].append(ban_b)

    ban_r=[By3,By4,Bx2,Fy3,By3]
    Lr=abs(By4[1]-Fy3[1])
    if Lr>SPLIT_THRESHOLD:
        split_right=True
        mid_y=_split_mid_int(Fy3[1],By4[1])
        r_low=[(Fy3[0],Fy3[1]),(Bx2[0],Fy3[1]),(Bx2[0],mid_y),(Fy3[0],mid_y),(Fy3[0],Fy3[1])]
        r_up=[(Fy3[0],mid_y),(By3[0],By3[1]),(By4[0],By4[1]),(Bx2[0],mid_y),(Fy3[0],mid_y)]
        polys["banquettes"]+=[r_low,r_up]
    else:
        polys["banquettes"].append(ban_r)

    # dossiers (groupes par côtés)
    groups = _dossiers_groups_U("v1", pts, tx, profondeur, draw)
    _append_groups_to_polys_U(polys, groups)

    # Accoudoirs U v1
    if acc_left:
        if draw["D1"]:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_"], pts["Ay2"], pts["By2"], pts["By"], pts["Ay_"]])
    if acc_right:
        if draw["D5"]:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], pts["Dy3"], pts["By3"]])
        else:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax_par"], pts["By4"], pts["By3"]])

    polys["split_flags"]={"left":split_left,"bottom":split_bottom,"right":split_right}
    return polys, draw

def compute_points_U_v2(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                        dossier_left=True, dossier_bas=True, dossier_right=True,
                        acc_left=True, acc_bas=True, acc_right=True):
    prof = profondeur; pts={}
    F0x = 10 if dossier_left else 0
    F0y = 10 if dossier_bas  else 0
    pts["D0"]=(0,0); pts["D0x"]=(F0x,0); pts["D0y"]=(0,F0y); pts["F0"]=(F0x,F0y)

    # gauche (Fy au ras du bas)
    top_y_L = ty_left - (ACCOUDOIR_THICK if acc_left else 0)
    pts["Dy2"]=(0, top_y_L)
    pts["Ay"]=(0, ty_left); pts["Ay2"]=(F0x+prof, ty_left); pts["Ay_"]=(F0x, ty_left)
    pts["Fy"]=(F0x, F0y); pts["Fy2"]=(F0x+prof, F0y)
    pts["Fx"]=(F0x+prof, F0y); pts["Fx2"]=(F0x+prof, F0y+prof)
    pts["By"]=(F0x, top_y_L); pts["By2"]=(F0x+prof, top_y_L)

    # bas jusqu'à Dx2
    D02x_x = tx - (10 if (dossier_right or dossier_bas) else 0)
    Dx2_x  = D02x_x - prof
    pts["Dx"]=(F0x+prof,0); pts["Dx2"]=(Dx2_x,0)
    pts["Bx"]=(Dx2_x, F0y); pts["Bx2"]=(Dx2_x, F0y+prof)

    # droite (à DROITE du bas)
    top_y_R = tz_right - (ACCOUDOIR_THICK if acc_right else 0)
    pts["F02"]=(D02x_x, F0y); pts["By4"]=(D02x_x, top_y_R); pts["By3"]=(Dx2_x,   top_y_R)
    pts["D02x"]=(D02x_x,0); pts["D02"]=(tx,0); pts["D02y"]=(tx,F0y); pts["Dy3"]=(tx,top_y_R)
    pts["Ax"]=(Dx2_x, tz_right); pts["Ax2"]=(tx,tz_right); pts["Ax_par"]=(D02x_x,tz_right)

    pts["_ty_canvas"]=max(ty_left, tz_right)
    return pts

def build_polys_U_v2(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                     dossier_left=True, dossier_bas=True, dossier_right=True,
                     acc_left=True, acc_bas=True, acc_right=True):
    polys={"banquettes":[],"dossiers":[],"accoudoirs":[]}

    draw = {
        "D1": bool(dossier_left),
        "D2": bool(dossier_left or dossier_bas),
        "D3": bool(dossier_bas),
        "D4": bool(dossier_right or dossier_bas),
        "D5": bool(dossier_right),
    }

    F0=pts["F0"]; Fy=pts["Fy"]; Fx=pts["Fx"]; Fx2=pts["Fx2"]; By=pts["By"]; By2=pts["By2"]
    Bx=pts["Bx"]; Bx2=pts["Bx2"]; By3=pts["By3"]; By4=pts["By4"]; F02=pts["F02"]

    split_left=split_bottom=split_right=False

    # banquettes
    ban_g=[F0,By,By2,Fx,F0]
    Lg=abs(By[1]-F0[1])
    if Lg>SPLIT_THRESHOLD:
        split_left=True
        mid_y=_split_mid_int(F0[1],By[1])
        g_low=[(F0[0],F0[1]),(Fx[0],F0[1]),(Fx[0],mid_y),(F0[0],mid_y),(F0[0],F0[1])]
        g_up=[(F0[0],mid_y),(By[0],By[1]),(By2[0],By2[1]),(Fx[0],mid_y),(F0[0],mid_y)]
        polys["banquettes"]+=[g_low,g_up]
    else:
        polys["banquettes"].append(ban_g)

    ban_b=[Fx,Bx,Bx2,Fx2,Fx]
    Lb=abs(Bx2[0]-Fx2[0])
    if Lb>SPLIT_THRESHOLD:
        split_bottom=True
        mid_x=_split_mid_int(Fx2[0],Bx2[0])
        b_left=[(Fx[0],Fx[1]),(mid_x,Fx[1]),(mid_x,Fx2[1]),(Fx2[0],Fx2[1]),(Fx[0],Fx[1])]
        b_right=[(mid_x,Fx[1]),(Bx[0],Bx[1]),(Bx2[0],Bx2[1]),(mid_x,Fx2[1]),(mid_x,Fx[1])]
        polys["banquettes"]+=[b_left,b_right]
    else:
        polys["banquettes"].append(ban_b)

    ban_r=[F02,By4,By3,Bx,F02]
    Lr=abs(By3[1]-F02[1])
    if Lr>SPLIT_THRESHOLD:
        split_right=True
        mid_y=_split_mid_int(F02[1],By3[1])
        r_low=[(Bx[0],mid_y),(Bx[0],F02[1]),(F02[0],F02[1]),(F02[0],mid_y),(Bx[0],mid_y)]
        r_up=[(Bx[0],mid_y),(By3[0],By3[1]),(By4[0],By4[1]),(F02[0],mid_y),(Bx[0],mid_y)]
        polys["banquettes"]+=[r_low,r_up]
    else:
        polys["banquettes"].append(ban_r)

    # dossiers
    groups = _dossiers_groups_U("v2", pts, tx, profondeur, draw)
    _append_groups_to_polys_U(polys, groups)

    # Accoudoirs U v2
    if acc_left:
        if draw["D1"]:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_"], pts["Ay2"], pts["By2"], pts["By"], pts["Ay_"]])
    if acc_right:
        if draw["D5"]:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], pts["Dy3"], pts["By3"]])
        else:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax_par"], pts["By4"], pts["By3"]])

    polys["split_flags"]={"left":split_left,"bottom":split_bottom,"right":split_right}
    return polys, draw

def compute_points_U_v3(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                        dossier_left=True, dossier_bas=True, dossier_right=True,
                        acc_left=True, acc_bas=True, acc_right=True):
    prof = profondeur; pts={}
    F0x = 10 if dossier_left else 0
    F0y = 10 if dossier_bas  else 0
    pts["D0"]=(0,0); pts["D0x"]=(F0x,0); pts["D0y"]=(0,F0y); pts["F0"]=(F0x,F0y)

    # gauche (comme v1)
    pts["Dy"]=(0, F0y+prof)
    top_y_L=ty_left-(ACCOUDOIR_THICK if acc_left else 0)
    pts["Dy2"]=(0, top_y_L)
    pts["Ay"]=(0, ty_left); pts["Ay2"]=(F0x+prof, ty_left); pts["Ay_"]=(F0x, ty_left)
    pts["Fy"]=(F0x, F0y+prof); pts["Fy2"]=(F0x+prof, F0y+prof)
    pts["By"]=(F0x, top_y_L); pts["By2"]=(F0x+prof, top_y_L)

    # bas jusqu'à Bx (= D02x - prof)
    D02x_x = tx - (10 if (dossier_right or dossier_bas) else 0)
    Bx_x   = D02x_x - prof
    pts["Dx"]=(F0x+prof,0)
    pts["Bx"]=(Bx_x, F0y); pts["Bx2"]=(Bx_x, F0y+prof)

    # droite (à DROITE du bas)
    top_y_R=tz_right-(ACCOUDOIR_THICK if acc_right else 0)
    pts["By3"]=(Bx_x,   top_y_R); pts["F02"]=(D02x_x, F0y); pts["By4"]=(D02x_x, top_y_R)
    pts["D02x"]=(D02x_x,0); pts["D02"]=(tx,0); pts["D02y"]=(tx,F0y); pts["Dy3"]=(tx, top_y_R)
    pts["Ax"]=(Bx_x, tz_right); pts["Ax2"]=(tx, tz_right); pts["Ax_par"]=(D02x_x, tz_right)

    pts["_ty_canvas"]=max(ty_left,tz_right)
    return pts

def build_polys_U_v3(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                     dossier_left=True, dossier_bas=True, dossier_right=True,
                     acc_left=True, acc_bas=True, acc_right=True):
    polys={"banquettes":[],"dossiers":[],"accoudoirs":[]}

    draw = {
        "D1": bool(dossier_left),
        "D2": bool(dossier_left or dossier_bas),
        "D3": bool(dossier_bas),
        "D4": bool(dossier_right or dossier_bas),
        "D5": bool(dossier_right),
    }

    F0=pts["F0"]; Fy=pts["Fy"]; Fy2=pts["Fy2"]; By=pts["By"]; By2=pts["By2"]
    Bx=pts["Bx"]; Bx2=pts["Bx2"]; By3=pts["By3"]; By4=pts["By4"]; F02=pts["F02"]

    split_left=split_bottom=split_right=False
    # banquettes
    ban_g=[Fy,By,By2,Fy2,Fy]
    Lg=abs(By[1]-Fy[1])
    if Lg>SPLIT_THRESHOLD:
        split_left=True
        mid_y=_split_mid_int(Fy[1],By[1])
        g_low=[(Fy[0],Fy[1]),(Fy2[0],Fy[1]),(Fy2[0],mid_y),(Fy[0],mid_y),(Fy[0],Fy[1])]
        g_up=[(Fy[0],mid_y),(By[0],By[1]),(By2[0],By2[1]),(Fy2[0],mid_y),(Fy[0],mid_y)]
        polys["banquettes"]+=[g_low,g_up]
    else:
        polys["banquettes"].append(ban_g)

    ban_b=[F0,Bx,Bx2,Fy,F0]
    Lb=abs(Bx[0]-F0[0])
    if Lb>SPLIT_THRESHOLD:
        split_bottom=True
        mid_x=_split_mid_int(F0[0],Bx[0])
        b_left=[(F0[0],F0[1]),(mid_x,F0[1]),(mid_x,Fy[1]),(Fy[0],Fy[1]),(F0[0],F0[1])]
        b_right=[(mid_x,F0[1]),(Bx[0],Bx[1]),(Bx2[0],Bx2[1]),(mid_x,Fy[1]),(mid_x,F0[1])]
        polys["banquettes"]+=[b_left,b_right]
    else:
        polys["banquettes"].append(ban_b)

    # droite : By3 - By4 - F02 - Bx - By3
    ban_r=[By3,By4,F02,Bx,By3]
    Lr=abs(By3[1]-F02[1])
    if Lr>SPLIT_THRESHOLD:
        split_right=True
        mid_y=_split_mid_int(F02[1],By3[1])
        r_low=[(Bx[0],F02[1]),(F02[0],F02[1]),(F02[0],mid_y),(Bx[0],mid_y),(Bx[0],F02[1])]
        r_up=[(Bx[0],mid_y),(By3[0],By3[1]),(By4[0],By4[1]),(F02[0],mid_y),(Bx[0],mid_y)]
        polys["banquettes"]+=[r_low,r_up]
    else:
        polys["banquettes"].append(ban_r)

    # dossiers
    groups = _dossiers_groups_U("v3", pts, tx, profondeur, draw)
    _append_groups_to_polys_U(polys, groups)

    # Accoudoirs U v3
    if acc_left:
        if draw["D1"]:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_"], pts["Ay2"], pts["By2"], pts["By"], pts["Ay_"]])
    if acc_right:
        if draw["D5"]:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], pts["Dy3"], pts["By3"]])
        else:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax_par"], pts["By4"], pts["By3"]])

    polys["split_flags"]={"left":split_left,"bottom":split_bottom,"right":split_right}
    return polys, draw

def compute_points_U_v4(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                        dossier_left=True, dossier_bas=True, dossier_right=True,
                        acc_left=True, acc_bas=True, acc_right=True):
    prof = profondeur; pts = {}
    F0x = 10 if dossier_left else 0
    F0y = 10 if dossier_bas  else 0
    pts["D0"]  = (0, 0); pts["D0x"] = (F0x, 0); pts["D0y"] = (0, F0y); pts["F0"]  = (F0x, F0y)

    # Montant gauche
    top_y_L = ty_left - (ACCOUDOIR_THICK if acc_left else 0)
    pts["By"]  = (F0x, top_y_L); pts["Fx"]=(F0x+profondeur, F0y); pts["Fx2"]=(F0x+profondeur, F0y+prof); pts["By2"]=(F0x+profondeur, top_y_L)
    pts["Dy2"] = (0, top_y_L);  pts["Ay"]=(0, ty_left); pts["Ay2"]=(F0x+profondeur, ty_left); pts["Ay_"]=(F0x, ty_left)

    # Limite droite
    D02x_x = tx - (10 if (dossier_right or dossier_bas) else 0)
    pts["Dx"]=(F0x+profondeur,0); pts["Bx"]=(D02x_x, F0y); pts["Bx2"]=(D02x_x, F0y+prof)

    # Branche droite (au-dessus)
    top_y_R   = tz_right - (ACCOUDOIR_THICK if acc_right else 0)
    x_left_R  = D02x_x - prof
    pts["Fy3"]=(x_left_R, F0y+prof); pts["By3"]=(x_left_R, top_y_R); pts["By4"]=(D02x_x, top_y_R)

    pts["D02x"]=(D02x_x, 0); pts["D02"]=(tx, 0); pts["D02y"]=(tx, F0y); pts["Dy3"]=(tx, top_y_R)
    pts["Ax"]=(x_left_R, tz_right); pts["Ax2"]=(tx, tz_right); pts["Ax_par"]=(D02x_x, tz_right)

    pts["_ty_canvas"]=max(ty_left, tz_right)
    return pts

def build_polys_U_v4(pts, tx, ty_left, tz_right, profondeur=DEPTH_STD,
                     dossier_left=True, dossier_bas=True, dossier_right=True,
                     acc_left=True, acc_bas=True, acc_right=True):
    polys = {"banquettes": [], "dossiers": [], "accoudoirs": []}

    draw = {
        "D1": bool(dossier_left),
        "D2": bool(dossier_left or dossier_bas),
        "D3": bool(dossier_bas),
        "D4": bool(dossier_right or dossier_bas),
        "D5": bool(dossier_right),
    }

    F0=pts["F0"]; Fx=pts["Fx"]; Fx2=pts["Fx2"]; By=pts["By"]; By2=pts["By2"]
    Bx=pts["Bx"]; Bx2=pts["Bx2"]; Fy3=pts["Fy3"]; By3=pts["By3"]; By4=pts["By4"]

    split_left=split_bottom=split_right=False

    # banquettes
    ban_g = [F0, By, By2, Fx, F0]
    Lg = abs(By[1] - F0[1])
    if Lg > SPLIT_THRESHOLD:
        split_left=True
        mid_y = _split_mid_int(F0[1], By[1])
        g_low  = [(F0[0],F0[1]), (Fx[0],F0[1]), (Fx[0],mid_y), (F0[0],mid_y), (F0[0],F0[1])]
        g_high = [(F0[0],mid_y), (By[0],By[1]), (By2[0],By2[1]), (Fx[0],mid_y), (F0[0],mid_y)]
        polys["banquettes"] += [g_low, g_high]
    else:
        polys["banquettes"].append(ban_g)

    ban_b = [Fx, Bx, Bx2, Fx2, Fx]
    Lb = abs(Bx2[0] - Fx2[0])
    if Lb > SPLIT_THRESHOLD:
        split_bottom=True
        mid_x = _split_mid_int(Fx2[0], Bx2[0])
        b_left  = [(Fx[0],Fx[1]), (mid_x,Fx[1]), (mid_x,Fx2[1]), (Fx2[0],Fx2[1]), (Fx[0],Fx[1])]
        b_right = [(mid_x,Fx[1]), (Bx[0],Bx[1]), (Bx2[0],Bx2[1]), (mid_x,Fx2[1]), (mid_x,Fx[1])]
        polys["banquettes"] += [b_left, b_right]
    else:
        polys["banquettes"].append(ban_b)

    ban_r = [Fy3, By3, By4, Bx2, Fy3]
    Lr = abs(By3[1] - Fy3[1])
    if Lr > SPLIT_THRESHOLD:
        split_right=True
        mid_y = _split_mid_int(Fy3[1], By3[1])
        r_low  = [(Fy3[0],Fy3[1]), (Bx2[0],Fy3[1]), (Bx2[0],mid_y), (Fy3[0],mid_y), (Fy3[0],Fy3[1])]
        r_high = [(Fy3[0],mid_y), (By3[0],By3[1]), (By4[0],By4[1]), (Bx2[0],mid_y), (Fy3[0],mid_y)]
        polys["banquettes"] += [r_low, r_high]
    else:
        polys["banquettes"].append(ban_r)

    # dossiers
    groups = _dossiers_groups_U("v4", pts, tx, profondeur, draw)
    _append_groups_to_polys_U(polys, groups)

    # Accoudoirs U v4
    if acc_left:
        if draw["D1"]:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By2"], pts["Dy2"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay_"], pts["Ay2"], pts["By2"], pts["By"], pts["Ay_"]])
    if acc_right:
        if draw["D5"]:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax2"], pts["Dy3"], pts["By3"]])
        else:
            polys["accoudoirs"].append([pts["By3"], pts["Ax"], pts["Ax_par"], pts["By4"], pts["By3"]])

    polys["split_flags"]={"left":split_left,"bottom":split_bottom,"right":split_right}
    return polys, draw

# ---------- Dossiers par côtés (U) ----------
def _dossiers_groups_U(variant, pts, tx, profondeur, draw):
    groups = {"left": {"D1":[], "D2":[]},
              "bottom":{"D3":[]},
              "right":{"D4":[], "D5":[]}}
    F0x, F0y = pts["F0"]

    if variant == "v1":
        if draw["D1"]:
            groups["left"]["D1"].append([pts["Dy2"], pts["By"], pts["Fy"], pts["Dy"], pts["Dy2"]])
        if draw["D2"]:
            groups["left"]["D2"].append([pts["D0x"], pts["D0"], pts["Dy"], pts["Fy"], pts["D0x"]])
        if draw["D3"]:
            groups["bottom"]["D3"].append([pts["D02x"], pts["D0x"], pts["F0"], pts["Bx"], pts["D02x"]])
        if draw["D4"]:
            groups["right"]["D4"].append([pts["D02x"], pts["D02"], pts["Dy3"], pts["Bx2"], pts["D02x"]])
        if draw["D5"]:
            x0 = pts["D02x"][0]; y1 = F0y + profondeur; y_top = pts["By4"][1]
            groups["right"]["D5"].append(_rectU(x0, y1, tx, y_top))

    elif variant == "v2":
        if draw["D1"]:
            groups["left"]["D1"].append([pts["D0x"], pts["By"], pts["Dy2"], pts["D0"], pts["D0x"]])
        if draw["D2"]:
            groups["left"]["D2"].append([pts["D0x"], pts["Dx"], pts["Fx"], pts["F0"], pts["D0x"]])
        if draw["D3"]:
            groups["bottom"]["D3"].append([pts["Dx"], pts["Dx2"], pts["Bx"], pts["Fx"], pts["Dx"]])
        if draw["D4"]:
            groups["right"]["D4"].append([pts["Dx2"], pts["D02x"], pts["F02"], pts["Bx"], pts["Dx2"]])
        if draw["D5"]:
            groups["right"]["D5"].append([pts["D02x"], pts["D02"], pts["Dy3"], pts["By4"], pts["D02x"]])

    elif variant == "v3":
        if draw["D1"]:
            groups["left"]["D1"].append([pts["Dy"], pts["Fy"], pts["By"], pts["Dy2"], pts["Dy"]])
        if draw["D2"]:
            groups["left"]["D2"].append([pts["D0x"], pts["D0"], pts["Dy"], pts["Fy"], pts["D0x"]])
        if draw["D3"]:
            xL = F0x; xR = pts["Bx"][0]; y0 = 0; y1 = F0y
            groups["bottom"]["D3"].append(_rectU(xL, y0, xR, y1))
        if draw["D4"]:
            bx0 = pts["Bx"][0]
            groups["right"]["D4"].append([
                pts["Dx"], pts["D02x"], pts["F02"], pts["Bx"], (bx0, 0), pts["Dx"]
            ])
        if draw["D5"]:
            groups["right"]["D5"].append([pts["Dy3"], pts["By4"], pts["D02x"], pts["D02"], pts["Dy3"]])

    else:  # v4
        if draw["D1"]:
            groups["left"]["D1"].append([pts["D0x"], pts["By"], pts["Dy2"], pts["D0"], pts["D0x"]])
        if draw["D2"]:
            groups["left"]["D2"].append([pts["D0x"], pts["Dx"], pts["Fx"], pts["F0"], pts["D0x"]])
        if draw["D3"]:
            groups["bottom"]["D3"].append([pts["Dx"], pts["D02x"], pts["Bx"], pts["Fx"], pts["Dx"]])
        F02x = pts["D02x"][0]; y0 = F0y; y1 = y0 + profondeur
        if draw["D4"]:
            groups["right"]["D4"] += [
                _rectU(F02x, 0,  tx, y0),
                _rectU(F02x, y0, tx, y1),
            ]
        if draw["D5"]:
            y_top = pts["By4"][1]
            groups["right"]["D5"].append(_rectU(F02x, y1, tx, y_top))
    return groups

def _append_groups_to_polys_U(polys, groups):
    order = {"left":["D1","D2"], "bottom":["D3"], "right":["D4","D5"]}
    for side in ("left","bottom","right"):
        for d in order[side]:
            for poly in groups[side].get(d, []):
                polys["dossiers"].append(poly)
    polys["dossiers_by_side"] = groups  # info

# === AUTO optimisé pour U (taille + orientation) ===
def _best_orientation_score_U(variant, pts, drawn, size, traversins=None):
    F0x, F0y = pts["F0"]
    x_end = _u_variant_x_end(variant, pts)

    def cnt_h(x0, x1): return int(max(0, x1-x0)//size)
    def cnt_v(y0, y1): return int(max(0, y1-y0)//size)

    y_end_L = pts["By"][1]
    y_end_R = pts["By4"][1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK

    def score(shiftL, shiftR):
        xs = F0x + (CUSHION_DEPTH if shiftL else 0)
        xe = x_end - (CUSHION_DEPTH if shiftR else 0)
        bas = cnt_h(xs, xe)
        yL0 = F0y + (0 if (not drawn.get("D1", False) or shiftL) else CUSHION_DEPTH)
        has_right = drawn.get("D4", False) or drawn.get("D5", False)
        yR0 = F0y + (0 if (not has_right or shiftR) else CUSHION_DEPTH)
        g = cnt_v(yL0, y_end_L); d = cnt_v(yR0, y_end_R)
        waste = (max(0, xe-xs)%size) + (max(0, y_end_L-yL0)%size) + (max(0, y_end_R-yR0)%size)
        return (bas+g+d, -waste, -size), xs, xe, yL0, yR0

    cands = [score(False,False), score(True,False), score(False,True), score(True,True)]
    return max(cands, key=lambda k: k[0])

def _choose_cushion_size_auto_U(variant, pts, drawn, traversins=None):
    best_s, best_tuple = 65, (-1, -1, -65)
    for s in (65, 80, 90):
        (score_tuple, *_rest) = _best_orientation_score_U(variant, pts, drawn, s, traversins=traversins)
        if score_tuple > best_tuple:
            best_tuple, best_s = score_tuple, s
    return best_s

def _draw_cushions_variant_U(t, tr, variant, pts, size, drawn, traversins=None):
    (score_tuple, xs, xe, yL0, yR0) = _best_orientation_score_U(variant, pts, drawn, size, traversins=traversins)
    F0x, F0y = pts["F0"]
    x_col = pts["Bx"][0] if variant in ("v1","v4") else pts["F02"][0]
    y_end_L = pts["By"][1]; y_end_R = pts["By4"][1]
    if traversins:
        if "g" in traversins: y_end_L -= TRAVERSIN_THK
        if "d" in traversins: y_end_R -= TRAVERSIN_THK

    count = 0
    # bas
    y = F0y; x = xs
    while x + size <= xe + 1e-6:
        poly = [(x, y), (x+size, y), (x+size, y+CUSHION_DEPTH), (x, y+CUSHION_DEPTH), (x, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{size}", font=FONT_CUSHION)
        x += size; count += 1

    # gauche
    x = F0x; y = yL0
    while y + size <= y_end_L + 1e-6:
        poly = [(x, y), (x+CUSHION_DEPTH, y), (x+CUSHION_DEPTH, y+size), (x, y+size), (x, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{size}", font=FONT_CUSHION)
        y += size; count += 1

    # droit
    x = x_col; y = yR0
    while y + size <= y_end_R + 1e-6:
        poly = [(x - CUSHION_DEPTH, y), (x, y), (x, y+size), (x - CUSHION_DEPTH, y+size), (x - CUSHION_DEPTH, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{size}", font=FONT_CUSHION)
        y += size; count += 1

    return count

def _render_common_U(variant, tx, ty_left, tz_right,
                     profondeur, dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_fn, build_fn, traversins=None, couleurs=None):
    pts = compute_fn(tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right)
    polys, drawn = build_fn(pts, tx, ty_left, tz_right, profondeur,
                            dossier_left, dossier_bas, dossier_right,
                            acc_left, acc_bas, acc_right)
    _assert_banquettes_max_250(polys)

    trv = _parse_traversins_spec(traversins, allowed={"g","d"})
    legend_items = _resolve_and_apply_colors(couleurs)

    ty_canvas = pts["_ty_canvas"]
    screen = turtle.Screen(); screen.setup(WIN_W, WIN_H)
    screen.title(f"{window_title} — {variant} — tx={tx} / ty(left)={ty_left} / tz(right)={tz_right} — prof={profondeur}")
    t = turtle.Turtle(visible=False); t.speed(0); screen.tracer(False)
    tr = WorldToScreen(tx, ty_canvas, WIN_W, WIN_H, PAD_PX, ZOOM)

    # (Quadrillage et repères supprimés)

    for p in polys["dossiers"]:
        if _poly_has_area(p): draw_polygon_cm(t, tr, p, fill=COLOR_DOSSIER)
    for p in polys["banquettes"]:
        draw_polygon_cm(t, tr, p, fill=COLOR_ASSISE)
    for p in polys["accoudoirs"]:
        draw_polygon_cm(t, tr, p, fill=COLOR_ACC)

    # Traversins + comptage
    n_traversins = _draw_traversins_U_common(t, tr, variant, pts, profondeur, trv)

    draw_double_arrow_vertical_cm(t, tr, -25, 0, ty_left,   f"{ty_left} cm")
    draw_double_arrow_vertical_cm(t, tr,  tx+25, 0, tz_right, f"{tz_right} cm")
    draw_double_arrow_horizontal_cm(t, tr, -25, 0, tx, f"{tx} cm")

    # Labels banquettes
    banquette_sizes=[]
    for poly in polys["banquettes"]:
        L,P = banquette_dims(poly); banquette_sizes.append((L,P))
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        bb_w=max(xs)-min(xs); bb_h=max(ys)-min(ys)
        text=f"{L}×{P} cm"
        if bb_h >= bb_w:
            cx = sum(xs)/len(xs); dx = (CUSHION_DEPTH+10) if cx < tx/2 else -(CUSHION_DEPTH+10)
            label_poly_offset_cm(t, tr, poly, text, dx_cm=dx, dy_cm=0.0)
        else:
            label_poly(t, tr, poly, text)

    # Labels dossiers / accoudoirs
    for p in polys["dossiers"]:
        if _poly_has_area(p): label_poly(t, tr, p, "10")
    for p in polys["accoudoirs"]:
        if _poly_has_area(p): label_poly(t, tr, p, "15")

    # ===== COUSSINS =====
    spec = _parse_coussins_spec(coussins)
    if spec["mode"] == "auto":
        size = _choose_cushion_size_auto_U(variant, pts, drawn, traversins=trv)
        cushions_count = _draw_cushions_variant_U(t, tr, variant, pts, size, drawn, traversins=trv)
        total_line = f"{coussins} → {cushions_count} × {size} cm"
    elif spec["mode"] == "fixed":
        size = int(spec["fixed"])
        cushions_count = _draw_cushions_variant_U(t, tr, variant, pts, size, drawn, traversins=trv)
        total_line = f"{coussins} → {coussins} × {size} cm"
    else:
        best = _optimize_valise_U(variant, pts, drawn, spec["range"], spec["same"], traversins=trv)
        if not best:
            raise ValueError("Aucune configuration valise valide pour U.")
        sizes = best["sizes"]; shiftL = best.get("shiftL", False); shiftR = best.get("shiftR", False)
        cushions_count = _draw_U_with_sizes(variant, t, tr, pts, sizes, drawn, shiftL, shiftR, traversins=trv)
        sb, sg, sd = sizes["bas"], sizes["gauche"], sizes["droite"]
        total_line = f"bas={sb} / gauche={sg} / droite={sd} (Δ={max(sb,sg,sd)-min(sb,sg,sd)}) — total: {cushions_count}"

    # Titre + légende (U → haut-centre)
    draw_title_center(t, tr, tx, ty_canvas, "Canapé en U sans angle")
    draw_legend(t, tr, tx, ty_canvas, items=legend_items, pos="top-center")

    screen.tracer(True); t.hideturtle()

    # Comptage dossiers + bonus scission
    split_flags = polys.get("split_flags", {})
    add_split = int(split_flags.get("left",False)  and (drawn.get("D1") or drawn.get("D2"))) \
              + int(split_flags.get("bottom",False) and drawn.get("D3")) \
              + int(split_flags.get("right",False) and drawn.get("D5"))
    print(f"=== Rapport canapé U (variant {variant}) ===")
    print(f"Dimensions : tx={tx} / ty(left)={ty_left} / tz(right)={tz_right} — prof={profondeur}")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers : {len(polys['dossiers'])} (+{add_split} via scission) | Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 0")
    print(f"Traversins : {n_traversins} × 70x30")
    print(f"Coussins : {total_line}")
    turtle.done()

def render_U_v1(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                dossier_left=True, dossier_bas=True, dossier_right=True,
                acc_left=True, acc_bas=True, acc_right=True,
                coussins="auto", window_title="U v1", traversins=None, couleurs=None):
    _render_common_U("v1", tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_points_U_v1, build_polys_U_v1, traversins=traversins, couleurs=couleurs)

def render_U_v2(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                dossier_left=True, dossier_bas=True, dossier_right=True,
                acc_left=True, acc_bas=True, acc_right=True,
                coussins="auto", window_title="U v2", traversins=None, couleurs=None):
    _render_common_U("v2", tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_points_U_v2, build_polys_U_v2, traversins=traversins, couleurs=couleurs)

def render_U_v3(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                dossier_left=True, dossier_bas=True, dossier_right=True,
                acc_left=True, acc_bas=True, acc_right=True,
                coussins="auto", window_title="U v3", traversins=None, couleurs=None):
    _render_common_U("v3", tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_points_U_v3, build_polys_U_v3, traversins=traversins, couleurs=couleurs)

def render_U_v4(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                dossier_left=True, dossier_bas=True, dossier_right=True,
                acc_left=True, acc_bas=True, acc_right=True,
                coussins="auto", window_title="U v4", traversins=None, couleurs=None):
    _render_common_U("v4", tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_points_U_v4, build_polys_U_v4, traversins=traversins, couleurs=couleurs)

# ---------- AUTO sélection U ----------
def _metrics_U(variant, tx, ty_left, tz_right, profondeur,
               dossier_left, dossier_bas, dossier_right,
               acc_left, acc_bas, acc_right):
    comp = {"v1":compute_points_U_v1, "v2":compute_points_U_v2,
            "v3":compute_points_U_v3, "v4":compute_points_U_v4}[variant]
    build= {"v1":build_polys_U_v1,   "v2":build_polys_U_v2,
            "v3":build_polys_U_v3,   "v4":build_polys_U_v4}[variant]
    pts = comp(tx, ty_left, tz_right, profondeur,
               dossier_left, dossier_bas, dossier_right,
               acc_left, acc_bas, acc_right)
    polys, _ = build(pts, tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right)
    nb_banquettes = len(polys["banquettes"])
    scissions = max(0, nb_banquettes - 3)  # U = 3 groupes (G,B,D)
    return nb_banquettes, scissions

def render_U(tx, ty_left, tz_right,
             profondeur=DEPTH_STD,
             dossier_left=True, dossier_bas=True, dossier_right=True,
             acc_left=True, acc_bas=True, acc_right=True,
             coussins="auto",
             variant="auto",
             traversins=None,
             couleurs=None,
             window_title="U — auto"):
    v = (variant or "auto").lower()
    if v in ("v1","v2","v3","v4"):
        return {"v1":render_U_v1, "v2":render_U_v2, "v3":render_U_v3, "v4":render_U_v4}[v](
            tx, ty_left, tz_right, profondeur,
            dossier_left, dossier_bas, dossier_right,
            acc_left, acc_bas, acc_right,
            coussins, window_title=f"{window_title} [{v}]", traversins=traversins, couleurs=couleurs
        )

    # auto
    variants = ["v1","v2","v3","v4"]
    metrics = {vv:_metrics_U(vv, tx, ty_left, tz_right, profondeur,
                             dossier_left, dossier_bas, dossier_right,
                             acc_left, acc_bas, acc_right)
               for vv in variants}
    # critère 1 : moins de banquettes
    min_b = min(m[0] for m in metrics.values())
    tied = [vv for vv,(b,s) in metrics.items() if b==min_b]
    if len(tied) > 1:
        # tie-break : moins de scissions
        min_s = min(metrics[vv][1] for vv in tied)
        tied = [vv for vv in tied if metrics[vv][1]==min_s]
    # tie-break final (stabilité)
    for pref in ["v2","v1","v3","v4"]:
        if pref in tied:
            choice=pref; break

    return render_U(tx, ty_left, tz_right,
                    profondeur, dossier_left, dossier_bas, dossier_right,
                    acc_left, acc_bas, acc_right,
                    coussins, variant=choice, traversins=traversins, couleurs=couleurs,
                    window_title=window_title)

# =====================================================================
# ===================  SIMPLE droit (S1)  =============================
# =====================================================================

def compute_points_simple_S1(tx,
                             profondeur=DEPTH_STD,
                             dossier=True,
                             acc_left=True, acc_right=True,
                             meridienne_side=None, meridienne_len=0):
    if meridienne_side == 'g' and acc_left:
        raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
    if meridienne_side == 'd' and acc_right:
        raise ValueError("Méridienne droite interdite avec accoudoir droit.")

    xL_in = ACCOUDOIR_THICK if acc_left  else 0
    xR_in = tx - (ACCOUDOIR_THICK if acc_right else 0)
    y_base = DOSSIER_THICK if dossier else 0

    pts = {}
    pts["Ay"]  = (0, 0);          pts["Ay2"] = (0, profondeur)
    pts["Ax"]  = (tx, 0);         pts["Ax2"] = (tx, profondeur)
    pts["B0"]  = (xL_in, y_base); pts["By"]  = (xL_in, profondeur)
    pts["Bx"]  = (xR_in, y_base); pts["Bx2"] = (xR_in, profondeur)
    pts["D0"]  = (xL_in, 0);      pts["Dx"]  = (xR_in, 0)

    if meridienne_side == 'g' and meridienne_len > 0:
        start_x = min(max(xL_in + meridienne_len, xL_in), xR_in)
        pts["D0_m"] = (start_x, 0); pts["B0_m"] = (start_x, y_base)
    if meridienne_side == 'd' and meridienne_len > 0:
        end_x = max(min(xR_in - meridienne_len, xR_in), xL_in)
        pts["Dx_m"] = (end_x, 0); pts["Bx_m"] = (end_x, y_base)

    pts["_tx"] = tx; pts["_prof"] = profondeur
    return pts

def build_polys_simple_S1(pts, dossier=True, acc_left=True, acc_right=True,
                          meridienne_side=None, meridienne_len=0):
    polys = {"banquettes": [], "dossiers": [], "accoudoirs": []}
    # --- Ajout pour scission de dossier si banquette scindée ---
    mid_x = None

    ban = [pts["By"], pts["B0"], pts["Bx"], pts["Bx2"], pts["By"]]
    L = abs(pts["Bx"][0] - pts["B0"][0])
    split = False
    if L > SPLIT_THRESHOLD:
        split = True
        mid_x = _split_mid_int(pts["B0"][0], pts["Bx"][0])
        left  = [pts["By"], pts["B0"], (mid_x, pts["B0"][1]), (mid_x, pts["By"][1]), pts["By"]]
        right = [(mid_x, pts["By"][1]), (mid_x, pts["B0"][1]), pts["Bx"], pts["Bx2"], (mid_x, pts["By"][1])]
        polys["banquettes"] += [left, right]
    else:
        polys["banquettes"].append(ban)

    if dossier:
        x0, x1 = pts["D0"][0], pts["Dx"][0]
        if meridienne_side == 'g' and meridienne_len > 0: x0 = pts["D0_m"][0]
        if meridienne_side == 'd' and meridienne_len > 0: x1 = pts["Dx_m"][0]
        if x1 > x0 + 1e-6:
            # Si banquette scindée et mid_x tombe dans le segment → scinder le dossier aussi
            if (mid_x is not None) and (x0 < mid_x < x1):
                left_dossier  = [(x0,0), (mid_x,0), (mid_x,DOSSIER_THICK), (x0,DOSSIER_THICK), (x0,0)]
                right_dossier = [(mid_x,0), (x1,0), (x1,DOSSIER_THICK), (mid_x,DOSSIER_THICK), (mid_x,0)]
                polys["dossiers"] += [left_dossier, right_dossier]
            else:
                # sinon, un seul dossier
                polys["dossiers"].append([(x0,0),(x1,0),(x1,DOSSIER_THICK),(x0,DOSSIER_THICK),(x0,0)])

    if acc_left:
        if dossier:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By"], pts["D0"], pts["Ay"]])
        else:
            polys["accoudoirs"].append([pts["Ay"], pts["Ay2"], pts["By"], pts["B0"], pts["Ay"]])
    if acc_right:
        if dossier:
            polys["accoudoirs"].append([pts["Bx2"], pts["Dx"], pts["Ax"], pts["Ax2"], pts["Bx2"]])
        else:
            polys["accoudoirs"].append([pts["Bx2"], pts["Ax2"], pts["Ax"], pts["Bx"], pts["Bx2"]])

    polys["split_flags"]={"center":split}
    return polys

def _choose_cushion_size_auto_simple_S1(x0, x1):
    usable = max(0, x1 - x0)
    best, best_score = 65, (1e9, -1)
    for s in (65, 80, 90):
        waste = usable % s if usable > 0 else 0
        score = (waste, -s)
        if score < best_score:
            best_score, best = score, s
    return best

def _draw_coussins_simple_S1(t, tr, pts, size,
                             meridienne_side=None, meridienne_len=0,
                             traversins=None):
    x0 = pts["B0"][0]; x1 = pts["Bx"][0]
    if meridienne_side == 'g' and meridienne_len > 0:
        x0 = max(x0, pts.get("B0_m", (x0, 0))[0])
    if meridienne_side == 'd' and meridienne_len > 0:
        x1 = min(x1, pts.get("Bx_m", pts["Bx"])[0])
    if traversins:
        if "g" in traversins: x0 += TRAVERSIN_THK
        if "d" in traversins: x1 -= TRAVERSIN_THK

    def count(off):
        xs = x0 + off; xe = x1
        return int(max(0, xe - xs) // size)
    off = CUSHION_DEPTH if count(CUSHION_DEPTH) > count(0) else 0

    y = pts["B0"][1]
    x = x0 + off; n = 0
    while x + size <= x1 + 1e-6:
        poly = [(x, y), (x+size, y), (x+size, y+CUSHION_DEPTH), (x, y+CUSHION_DEPTH), (x, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{size}", font=FONT_CUSHION)
        x += size; n += 1
    return n

def render_Simple1(tx,
                   profondeur=DEPTH_STD,
                   dossier=True,
                   acc_left=True, acc_right=True,
                   meridienne_side=None, meridienne_len=0,
                   coussins="auto",
                   traversins=None,
                   couleurs=None,
                   window_title="Canapé simple 1"):
    pts   = compute_points_simple_S1(tx, profondeur, dossier, acc_left, acc_right,
                                     meridienne_side, meridienne_len)
    polys = build_polys_simple_S1(pts, dossier, acc_left, acc_right,
                                  meridienne_side, meridienne_len)
    _assert_banquettes_max_250(polys)

    trv = _parse_traversins_spec(traversins, allowed={"g","d"})
    legend_items = _resolve_and_apply_colors(couleurs)

    screen = turtle.Screen(); screen.setup(WIN_W, WIN_H)
    screen.title(f"{window_title} — tx={tx} / prof={profondeur} — méridienne {meridienne_side or '-'}={meridienne_len} — coussins={coussins}")
    t = turtle.Turtle(visible=False); t.speed(0); screen.tracer(False)
    tr = WorldToScreen(tx, profondeur, WIN_W, WIN_H, PAD_PX, ZOOM)

    # (Quadrillage et repères supprimés)

    for p in polys["dossiers"]:
        if _poly_has_area(p):  draw_polygon_cm(t, tr, p, fill=COLOR_DOSSIER)
    for p in polys["banquettes"]:
        draw_polygon_cm(t, tr, p, fill=COLOR_ASSISE)
    for p in polys["accoudoirs"]:
        draw_polygon_cm(t, tr, p, fill=COLOR_ACC)

    # Traversins + comptage
    n_traversins = _draw_traversins_simple_S1(t, tr, pts, profondeur, dossier, trv)

    draw_double_arrow_vertical_cm(t, tr, -25, 0, profondeur, f"{profondeur} cm")
    draw_double_arrow_horizontal_cm(t, tr, -25, 0, tx, f"{tx} cm")

    banquette_sizes=[]
    for poly in polys["banquettes"]:
        L, P = banquette_dims(poly); banquette_sizes.append((L, P))
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        bb_w=max(xs)-min(xs); bb_h=max(ys)-min(ys)
        text=f"{L}×{P} cm"
        if bb_h>=bb_w:
            label_poly_offset_cm(t, tr, poly, text, dx_cm=CUSHION_DEPTH+10, dy_cm=0.0)
        else:
            label_poly(t, tr, poly, text)
    for p in polys["dossiers"]:
        if _poly_has_area(p): label_poly(t, tr, p, "10")
    for p in polys["accoudoirs"]:
        if _poly_has_area(p): label_poly(t, tr, p, "15")

    # ===== COUSSINS =====
    spec = _parse_coussins_spec(coussins)
    if spec["mode"] == "auto":
        x0 = pts.get("B0_m", pts["B0"])[0] if meridienne_side == 'g' else pts["B0"][0]
        x1 = pts.get("Bx_m", pts["Bx"])[0] if meridienne_side == 'd' else pts["Bx"][0]
        if trv:
            if "g" in trv: x0 += TRAVERSIN_THK
            if "d" in trv: x1 -= TRAVERSIN_THK
        size = _choose_cushion_size_auto_simple_S1(x0, x1)
        nb_coussins = _draw_coussins_simple_S1(t, tr, pts, size, meridienne_side, meridienne_len, traversins=trv)
        total_line = f"{coussins} → {nb_coussins} × {size} cm"
    elif spec["mode"] == "fixed":
        size = int(spec["fixed"])
        nb_coussins = _draw_coussins_simple_S1(t, tr, pts, size, meridienne_side, meridienne_len, traversins=trv)
        total_line = f"{coussins} → {nb_coussins} × {size} cm"
    else:
        best = _optimize_valise_simple(pts, spec["range"], meridienne_side, meridienne_len, traversins=trv)
        if not best:
            raise ValueError("Aucune configuration valise valide pour S1.")
        size = best["size"]
        nb_coussins = _draw_simple_with_size(t, tr, pts, size, meridienne_side, meridienne_len, traversins=trv)
        total_line = f"{nb_coussins} × {size} cm"

    # Légende
    draw_legend(t, tr, tx, profondeur, items=legend_items, pos="top-right")

    screen.tracer(True); t.hideturtle()
    add_split = int(polys.get("split_flags",{}).get("center",False) and dossier)
    print("=== Rapport Canapé simple 1 ===")
    print(f"Dimensions : {tx}×{profondeur} cm")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers   : {len(polys['dossiers'])} (+{add_split} via scission)  |  Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 0")
    print(f"Traversins : {n_traversins} × 70x30")
    print(f"Coussins   : {total_line}")
    if meridienne_side:
        print(f"Méridienne : côté {'gauche' if meridienne_side=='g' else 'droit'} — {meridienne_len} cm")
    turtle.done()

# =====================================================================
# ===========================  MAIN  ==================================
# =====================================================================
# =========================

# ======== TESTS ==========

# =========================

# Conseil : place ce bloc en bas de ton fichier (avant le __main__ si tu veux

# garder ton ancien MAIN). Chaque test illustre un aspect différent :

# variantes, dossiers, accoudoirs, méridienne, traversins, modes coussins, scissions…



def TEST_01_U_V2_base():

    render_U(

        tx=520, ty_left=300, tz_right=280, profondeur=80,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=True, acc_bas=True, acc_right=True,

        coussins="auto", variant="v3", traversins=None,

        window_title="T01 — U v2 | auto coussins | pas de TR"

    )



def TEST_02_U_V4_traversins_both_80():

    render_U(

        tx=440, ty_left=300, tz_right=270, profondeur=80,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=False, acc_bas=False, acc_right=False,

        coussins="80", variant="v4", traversins="g,d",

        window_title="T02 — U v4 | TR gauche+droite | coussins 80"

    )



def TEST_03_U_auto_variant_g():

    render_U(
        tx=525, ty_left=365, tz_right=360, profondeur=90,
        dossier_left=True, dossier_bas=True, dossier_right=True,
        acc_left=True, acc_bas=True, acc_right=True,
        coussins="80", variant="auto", traversins=None,
        window_title="T03 — U auto | valise g (76..100) | pas de TR"
    )




def TEST_04_U_V3_sans_dossier_droit_p():

    render_U(

        tx=600, ty_left=260, tz_right=260, profondeur=70,
        dossier_left=True, dossier_bas=True, dossier_right=True,  # pas de dossier droit
        acc_left=True, acc_bas=True, acc_right=True,
        meridienne_side='g', meridienne_len=50,
        coussins="p", variant="v3", traversins=None,
        window_title="T04 — U v3 | dossier droit OFF | valise p (60..74)"

    )



def TEST_05_S1_traversins_both_auto():

    render_Simple1(

        tx=400, profondeur=70, dossier=True,

        acc_left=True, acc_right=True,

        meridienne_side=None, meridienne_len=0,

        coussins="90", traversins="g,d",

        window_title="T05 — S1 | TR gauche+droite | coussins auto"

    )



def TEST_06_S1_mer_droite_120_no_accR_90_TRg():

    render_Simple1(

        tx=280, profondeur=70, dossier=True,

        acc_left=True, acc_right=False,              # méridienne droite -> pas d'accoudoir droit

        meridienne_side='d', meridienne_len=120,

        coussins="90", traversins="g",

        window_title="T06 — S1 | méridienne droite 120 | accR OFF | TR gauche | 90"

    )



def TEST_07_LNF_v1_mer_gauche_100_no_accL_p_TRg():

    render_LNF_v1(
        tx=350, ty=200, profondeur=70,
        dossier_left=True, dossier_bas=True,
        acc_left=True, acc_bas=False,                # méridienne gauche -> pas d'accoudoir gauche
        meridienne_side='b', meridienne_len=50,
        coussins="p", traversins=None,
        window_title="T07 — LNF v1 | méridienne G 100 | accL OFF | valise p | TR G"
    )



def TEST_08_LNF_v2_mer_bas_120_no_accB_gs_TRb():

    render_LF_variant(
        tx=380, ty=320, profondeur=70,
        dossier_left=True, dossier_bas=True,
        acc_left=False, acc_bas=False,               # méridienne bas -> pas d'accoudoir bas
        meridienne_side='g', meridienne_len=30,
        coussins="p", traversins=None,
        window_title="T08 — LNF v2 | méridienne bas 120 | accB OFF | g:s | TR bas"

    )



def TEST_09_LNF_v1_grand_split_valise_TRgb():

    render_LNF_v2(

        tx=520, ty=330, profondeur=70,

        dossier_left=True, dossier_bas=True,

        acc_left=True, acc_bas=True,

        meridienne_side=None, meridienne_len=0,

        coussins="valise", traversins="g,b",

        window_title="T09 — LNF v1 | grandes longueurs (scissions) | valise | TR G+B"

    )



def TEST_10_LNF_v2_compact_75():

    render_LNF_v2(

        tx=240, ty=240, profondeur=80,

        dossier_left=True, dossier_bas=True,

        acc_left=True, acc_bas=True,

        meridienne_side=None, meridienne_len=0,

        coussins="75", traversins=None,

        window_title="T10 — LNF v2 | compact | coussins 75 | pas de TR"

    )



def TEST_11_LF_mer_bas_100_no_accB_auto_TRgb():

    render_LF_variant(

        tx=420, ty=340, profondeur=70,

        dossier_left=True, dossier_bas=True,

        acc_left=True, acc_bas=False,               # méridienne bas -> pas d'accoudoir bas

        meridienne_side='b', meridienne_len=100,

        coussins="auto", traversins="g,b",

        window_title="T11 — LF | méridienne bas 100 | accB OFF | auto | TR G+B"

    )



def TEST_12_LF_p_same_TRg():

    render_LF_variant(

        tx=360, ty=300, profondeur=80,

        dossier_left=True, dossier_bas=True,

        acc_left=True, acc_bas=True,

        meridienne_side=None, meridienne_len=0,

        coussins="p:s", traversins="g",

        window_title="T12 — LF | p:s (même taille) | TR G"

    )



def TEST_13_U1F_v2_mer_g_120_no_accL_s_TRd():

    render_U1F_v2(

        tx=420, ty=300, tz=280, profondeur=80,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=False, acc_right=True,                  # méridienne gauche -> pas d'accoudoir gauche

        meridienne_side='g', meridienne_len=120,

        coussins="s", traversins="d",

        window_title="T13 — U1F v2 | méridienne G 120 | accL OFF | s | TR D"

    )



def TEST_14_U1F_v4_mer_d_90_no_accR_65_TRg():

    render_U1F_v4(

        tx=400, ty=280, tz=320, profondeur=70,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=True, acc_right=False,                 # méridienne droite -> pas d'accoudoir droit

        meridienne_side='d', meridienne_len=90,

        coussins="65", traversins="g",

        window_title="T14 — U1F v4 | méridienne D 90 | accR OFF | 65 | TR G"

    )



def TEST_15_U1F_v3_TR_both_g():

    render_U1F_v3(

        tx=360, ty=320, tz=300, profondeur=70,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=True, acc_right=True,

        meridienne_side=None, meridienne_len=0,

        coussins="g", traversins="g,d",

        window_title="T15 — U1F v3 | TR G+D | valise g"

    )



def TEST_16_U1F_v1_p_same():

    render_U1F_v1(

        tx=380, ty=300, tz=280, profondeur=70,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=True, acc_right=True,

        meridienne_side=None, meridienne_len=0,

        coussins="p:s", traversins=None,

        window_title="T16 — U1F v1 | p:s (même taille) | pas de TR"

    )



def TEST_17_U2F_valise_TR_both():

    render_U2f_variant(

        tx=560, ty_left=340, tz_right=320, profondeur=80,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=True, acc_bas=True, acc_right=True,

        meridienne_side=None, meridienne_len=0,

        coussins="valise", traversins="g,d",

        window_title="T17 — U2F | valise (60..100) | TR G+D"

    )



def TEST_18_U2F_mer_d_120_no_accR_80_TRg():

    render_U2f_variant(

        tx=520, ty_left=320, tz_right=330, profondeur=80,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=True, acc_bas=True, acc_right=False,          # méridienne droite -> pas d'accoudoir droit

        meridienne_side='d', meridienne_len=120,

        coussins="80", traversins="g",

        window_title="T18 — U2F | méridienne D 120 | accR OFF | 80 | TR G"

    )



def TEST_19_U_V2_grand_TRg_90():

    render_U(

        tx=600, ty_left=360, tz_right=300, profondeur=90,

        dossier_left=True, dossier_bas=True, dossier_right=True,

        acc_left=True, acc_bas=True, acc_right=True,

        coussins="90", variant="v2", traversins="g",

        window_title="T19 — U v2 | grande config (scissions) | TR G | 90"

    )



def TEST_20_U_V1_left_only_TRg_auto():

    render_U(

        tx=420, ty_left=300, tz_right=260, profondeur=70,

        dossier_left=True, dossier_bas=True, dossier_right=False,  # pas de dossier droit

        acc_left=True, acc_bas=True, acc_right=True,

        coussins="auto", variant="v1", traversins="g",

        window_title="T20 — U v1 | dossier droit OFF | TR G | auto"

    )



# =========================

# ===== EXÉCUTION =========

# =========================

if __name__ == "__main__":

    # Décommente EXACTEMENT UNE ligne à la fois :

    #TEST_01_U_V2_base()

    TEST_02_U_V4_traversins_both_80()

    #TEST_03_U_auto_variant_g()

    #TEST_04_U_V3_sans_dossier_droit_p()

    #TEST_05_S1_traversins_both_auto()

    #TEST_06_S1_mer_droite_120_no_accR_90_TRg()

    #TEST_07_LNF_v1_mer_gauche_100_no_accL_p_TRg()

    #TEST_08_LNF_v2_mer_bas_120_no_accB_gs_TRb()

    #TEST_09_LNF_v1_grand_split_valise_TRgb()

    #TEST_10_LNF_v2_compact_75()

    #TEST_11_LF_mer_bas_100_no_accB_auto_TRgb()

    #TEST_12_LF_p_same_TRg()

    #TEST_13_U1F_v2_mer_g_120_no_accL_s_TRd()

    #TEST_14_U1F_v4_mer_d_90_no_accR_65_TRg()

    #TEST_15_U1F_v3_TR_both_g()

    #TEST_16_U1F_v1_p_same()

    #TEST_17_U2F_valise_TR_both()

    # TEST_18_U2F_mer_d_120_no_accR_80_TRg()

    # TEST_19_U_V2_grand_TRg_90()

    # TEST_20_U_V1_left_only_TRg_auto()

    pass