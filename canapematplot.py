# -*- coding: utf-8 -*-
# canape_complet_v6_valise.py
# Base validée (LF, U2f, U1F v1..v4, LNF v1/v2, U no-fromage v1..v4, Simple S1)
# + Correctifs antérieurs :
#   - Seuil scission strict = 250 (aucune tolérance)
#   - Vérif post-scission : si banquette > 250 -> erreur
#   - U no-fromage "auto" = moins de banquettes ; tie-break = moins de scissions
#   - L : coussins auto avec orientation H vs V (choix automatique)
#   - Comptage dossiers : +1 si scission sur un côté avec dossier
#   - Console enrichie (dimensions banquettes, nb banquettes d’angle)
#   - render_LNF(..., window_title=...) supporté
#   - PAS de "coussins valises" (ancienne version)
# + AJOUTS (version VALISE) — exigences 2025-10-02 :
#   - Modes coussins : auto / p / g / valise / s (same) / fixe (60..100)
#   - Contraintes globales :
#       * min = 60, max = 100
#       * auto = {65,80,90} (unique taille globale)
#       * p : tailles 60..74
#       * g : tailles 76..100
#       * valise : 60..100
#       * s : même taille partout (selon intervalle du mode)
#       * une seule taille par côté, et (hors s) dispersion globale ≤ 5 cm (max-min)
#   - Règles inchangées d’implantation (mêmes emplacements et orientations)
#   - Affichage console : récap par côté (nb × taille), total, mode + Δ global

import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# =========================
# Réglages / constantes
# =========================
WIN_W, WIN_H       = 900, 700
PAD_PX             = 60
ZOOM               = 0.85
LINE_WIDTH         = 2

COLOR_ASSISE       = "#f5f5dc"
COLOR_ACC          = "#d3d3d3"
COLOR_DOSSIER      = "#d3d3d3"
COLOR_CUSHION      = "#ece6d6"
COLOR_CONTOUR      = "black"

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

# =========================
# Helpers géométrie / écran
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
# pen_up_to removed: not needed with matplotlib

def draw_polygon_cm(ax, tr, pts, fill=None, outline=COLOR_CONTOUR, width=LINE_WIDTH):
    """Dessine un polygone (en cm) en utilisant matplotlib."""
    if not pts:
        return
    # Convertir les points du monde (cm) en pixels
    pts_px = [tr.pt(x, y) for (x, y) in pts]
    poly = Polygon(
        pts_px,
        closed=True,
        facecolor=(fill if fill is not None else "none"),
        edgecolor=outline,
        linewidth=width,
    )
    ax.add_patch(poly)

def draw_grid_cm(ax, tr, tx, ty, step, color, width):
    """Grille en coordonnées cm, dessinée en pixels sur ax."""
    for x in range(0, tx + 1, step):
        x0, y0 = tr.pt(x, 0)
        x1, y1 = tr.pt(x, ty)
        ax.plot([x0, x1], [y0, y1], linewidth=width, color=color)
    for y in range(0, ty + 1, step):
        x0, y0 = tr.pt(0, y)
        x1, y1 = tr.pt(tx, y)
        ax.plot([x0, x1], [y0, y1], linewidth=width, color=color)

def draw_axis_labels_cm(ax, tr, tx, ty,
                         step=AXIS_LABEL_STEP, max_mark=AXIS_LABEL_MAX):
    """Marques 50, 100, 150... en bord d’axes (toujours en cm)."""
    # Axe X
    for x in range(step, min(tx, max_mark) + 1, step):
        xp, yp = tr.pt(x, 0)
        # Décalage vertical vers le bas de 12 px
        ax.text(xp, yp - 12, str(x),
                ha="center", va="top", fontsize=10)

    # Axe Y
    for y in range(step, min(ty, max_mark) + 1, step):
        xp, yp = tr.pt(0, y)
        # Décalage horizontal vers la gauche
        ax.text(xp - 12, yp - 4, str(y),
                ha="right", va="center", fontsize=10)

def _unit(vx, vy):
    n = math.hypot(vx, vy)
    return (vx/n, vy/n) if n else (0, 0)

def draw_double_arrow_px(ax, p1, p2, text=None,
                         text_perp_offset_px=0, text_tang_shift_px=0):
    """Double flèche entre p1 et p2 (+ éventuelle étiquette)."""
    # Ligne avec flèches aux deux extrémités
    ax.annotate(
        "",
        xy=p2,
        xytext=p1,
        arrowprops=dict(arrowstyle="<->", lw=1.5, color="black")
    )

    vx, vy = (p2[0] - p1[0], p2[1] - p1[1])
    ux, uy = _unit(vx, vy)
    px, py = -uy, ux  # vecteur perpendiculaire

    if text:
        cx = (p1[0] + p2[0]) / 2.0
        cy = (p1[1] + p2[1]) / 2.0
        tx = cx + px * text_perp_offset_px + ux * text_tang_shift_px
        ty = cy + py * text_perp_offset_px + uy * text_tang_shift_px
        ax.text(tx, ty, text,
                ha="center", va="center", fontsize=12, fontweight="bold")

def draw_double_arrow_vertical_cm(ax, tr, x_cm, y0_cm, y1_cm, label):
    draw_double_arrow_px(
        ax,
        tr.pt(x_cm, y0_cm),
        tr.pt(x_cm, y1_cm),
        text=label,
        text_perp_offset_px=+12
    )

def draw_double_arrow_horizontal_cm(ax, tr, y_cm, x0_cm, x1_cm, label):
    draw_double_arrow_px(
        ax,
        tr.pt(x0_cm, y_cm),
        tr.pt(x1_cm, y_cm),
        text=label,
        text_perp_offset_px=-12,
        text_tang_shift_px=20
    )

def centroid(poly):
    return (sum(x for x,y in poly)/len(poly), sum(y for x,y in poly)/len(poly))

def label_poly(ax, tr, poly, text, font=("Arial", 11, "bold")):
    cx, cy = centroid(poly)
    x, y = tr.pt(cx, cy)
    # On n’utilise que la taille de police du tuple font
    fontsize = font[1] if len(font) > 1 else 11
    ax.text(x, y, text,
            ha="center", va="center",
            fontsize=fontsize, fontweight="bold")

def label_poly_offset_cm(ax, tr, poly, text,
                         dx_cm=0.0, dy_cm=0.0,
                         font=("Arial", 11, "bold")):
    cx, cy = centroid(poly)
    x, y = tr.pt(cx + dx_cm, cy + dy_cm)
    fontsize = font[1] if len(font) > 1 else 11
    ax.text(x, y, text,
            ha="center", va="center",
            fontsize=fontsize, fontweight="bold")

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

# ============================================================
# ===============  PLANIFICATEUR DE COUSSINS  =================
# ============================================================

def _norm_coussins_spec(c):
    """
    Normalise l'argument `coussins` en (mode, same, size_fixed, tag),
    où :
      - mode in {"auto", "p", "g", "valise", "fixed", "s"}
      - same: bool (force même taille partout)
      - size_fixed: int | None (si taille unique imposée)
      - tag: str pour affichage console ("valise" / "std" / None)
    Règles de parsing :
      - int ou str-int : -> ("fixed", True, value, None)
      - "auto" -> ("auto", True, None, None)
      - "p", "g", "valise", "s" -> mode correspondant
      - "valise:p", "valise:g", "valise:s" etc. -> mode = p/g/s, tag="valise"
      - "std:*" -> équivalent mais tag="std"
    """
    tag=None
    if isinstance(c, (int, float)):
        v=int(c); return ("fixed", True, v, tag)
    if c is None:
        return ("auto", True, None, tag)
    s=str(c).strip().lower()
    if s.isdigit():
        return ("fixed", True, int(s), tag)

    # labels + options
    parts=[p for p in s.replace(" ", "").split(":") if p]
    # labels ignorés dans la logique, gardés pour console
    labels=[p for p in parts if p in ("valise","std")]
    if labels: tag=labels[0]  # premier label conservé
    opts=[p for p in parts if p in ("auto","p","g","s")]
    if not opts:
        # "valise" seul => valise libre
        return ("valise", False, None, tag or "valise")
    # si plusieurs opts, on prend la dernière (ex: "valise:p:s" -> s prime)
    opt=opts[-1]
    if opt=="auto":  return ("auto", True, None, tag)
    if opt=="p":     return ("p", False, None, tag)
    if opt=="g":     return ("g", False, None, tag)
    if opt=="s":     return ("s", True, None, tag or "valise")  # same partout
    # fallback
    return ("valise", False, None, tag)

def _allowed_interval_for_mode(mode):
    """Retourne (lo, hi) inclus selon le mode."""
    if mode=="p":        return 60, 74
    if mode=="g":        return 76, 100    # 'plus de 75' -> 76..100
    if mode in ("valise","s","fixed","auto"):
        return 60, 100
    return 60, 100

def _score_pref_key(mode, total_waste, total_count, sizes, is_uniform_choice):
    """
    Clé de tri : minimise la chute, puis selon la préférence :
      - p : plus de coussins => MAX total_count
      - g : moins de coussins => MIN total_count
      - valise/s/auto/fixed : neutre → on préfère Δ min puis taille médiane plus grande
    """
    delta = max(sizes)-min(sizes) if sizes else 0
    med = sorted(sizes)[len(sizes)//2] if sizes else 0
    if mode=="p":
        return (total_waste, -total_count, delta, -med, not is_uniform_choice)
    if mode=="g":
        return (total_waste, total_count, delta, -med, not is_uniform_choice)
    # valise/s/auto/fixed
    return (total_waste, delta, -med, not is_uniform_choice)

def _choose_uniform_size_from_set(lengths, candidate_set):
    """Choisit s unique dans candidate_set minimisant la chute totale (puis s plus grand)."""
    best=None; best_score=(1e18, -1)
    for s in sorted(candidate_set):
        waste = sum(L % s if L>0 else 0 for L in lengths)
        score = (waste, -s)
        if score < best_score:
            best_score=score; best=s
    return best

def _plan_sizes_for_branches(lengths_by_side, mode, same=False):
    """
    lengths_by_side : dict {"bas":L_b, "gauche":L_g, "droite":L_d} (certaines clés peuvent manquer)
    mode : "auto" | "p" | "g" | "valise" | "fixed"
    same : True => impose même taille sur toutes les branches

    Retourne : dict sizes_by_side (mêmes clés que lengths_by_side)
               et meta (delta_global, mode_used, uniform, chosen_set_info)
    """
    sides = list(lengths_by_side.keys())
    Ls = [max(0, int(round(lengths_by_side[s])) ) for s in sides]

    if not sides:
        return {}, {"delta":0, "mode":mode, "uniform":True, "set":"-"}

    # AUTO = set standard (65,80,90), uniforme
    if mode=="auto":
        s = _choose_uniform_size_from_set(Ls, {65,80,90})
        return {k:s for k in sides}, {"delta":0, "mode":"auto", "uniform":True, "set":"{65,80,90}"}

    # FIXED = uniforme
    if mode=="fixed":
        # 'fixed' ici veut dire qu'on a déjà filtré la taille; la vérif min/max se fait ailleurs
        # On s'attend à ce que same=True aussi ; on garde uniforme
        s = _plan_sizes_for_branches._fixed_value  # injecté par l'appelant
        return {k:s for k in sides}, {"delta":0, "mode":"fixed", "uniform":True, "set":str(s)}

    lo, hi = _allowed_interval_for_mode(mode)

    # SAME = uniforme mais plages selon mode (valise:s -> 60..100 ; p:s -> 60..74 ; g:s -> 76..100)
    if same:
        candidate_set = range(lo, hi+1)
        s = _choose_uniform_size_from_set(Ls, candidate_set)
        return {k:s for k in sides}, {"delta":0, "mode":(mode+":s" if mode!="s" else "s"), "uniform":True, "set":f"[{lo}..{hi}]"}

    # valise/p/g : une seule taille par côté, écart global <= 5
    # stratégie : on balaie un "ancrage" a ∈ [lo..hi], puis on choisit pour chaque côté s_i ∈ [a-2..a+2]∩[lo..hi]
    # qui minimise la chute sur ce côté ; on garde la meilleure combinaison globale (chute totale min),
    # tie-break selon _score_pref_key(mode, ...)
    best_sizes=None; best_key=None; best_meta=None
    for a in range(lo, hi+1):
        # plage commune autorisée
        a_lo = max(lo, a-2); a_hi = min(hi, a+2)
        if a_lo > a_hi: continue
        sizes=[]
        for L in Ls:
            # meilleur s local dans [a_lo..a_hi] (min chute)
            best_s=None; best_w=(1e18, -1)
            for s in range(a_lo, a_hi+1):
                w = (L % s if L>0 else 0, -s)  # min chute, puis s plus grand
                if w < best_w:
                    best_w=w; best_s=s
            sizes.append(best_s)
        if not sizes: continue
        delta = max(sizes)-min(sizes)
        if delta > 5:  # respect écart global
            continue
        # score global
        waste = sum(L % s if L>0 else 0 for L,s in zip(Ls, sizes))
        count = sum((L // s) for L,s in zip(Ls, sizes))
        key = _score_pref_key(mode, waste, count, sizes, is_uniform_choice=False)
        if (best_key is None) or (key < best_key):
            best_key=key
            best_sizes={side:s for side,s in zip(sides, sizes)}
            best_meta={"delta":delta, "mode":mode, "uniform":False, "set":f"[{lo}..{hi}] anchor={a}"}

    # si rien trouvé (cas pathologique minuscule), fallback : uniforme lo..hi
    if best_sizes is None:
        s = _choose_uniform_size_from_set(Ls, range(lo,hi+1))
        best_sizes = {k:s for k in sides}
        best_meta  = {"delta":0, "mode":mode+" (fallback uniform)", "uniform":True, "set":f"[{lo}..{hi}]"}
    return best_sizes, best_meta

# ============================================================
# ==================  LF (L avec angle fromage)  =============
# ============================================================
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

def _choose_cushion_size_auto_LF_lengths(pts, tx, ty, meridienne_side=None, meridienne_len=0):
    """Longueurs utiles nominales (sans décider des décalages) pour LF."""
    xF, yF = pts["F0"]
    x_end = pts.get("Bx_", pts.get("Bx", (tx, yF)))[0]
    if meridienne_side == 'b' and meridienne_len > 0:
        x_end = min(x_end, tx - meridienne_len)
    usable_h = max(0.0, x_end - xF)

    y_end = pts.get("By_", pts.get("By", (xF, ty)))[1]
    usable_v = max(0.0, y_end - yF)
    return {"bas": usable_h, "gauche": usable_v}

def _lf_draw_cushions_per_side(t, tr, pts, sizes, orientation="A"):
    """
    Dessine coussins LF par côté.
    orientation = "A" → bas collé + gauche décalé
                 "B" → bas décalé + gauche collé
    """
    F0x, F0y = pts["F0"]
    x_end = pts.get("Bx_", pts["Bx"])[0]
    y_end = pts.get("By_", pts["By"])[1]
    s_b = sizes["bas"]; s_g = sizes["gauche"]

    total=0
    # BAS
    y = F0y
    x_cur = F0x + (0 if orientation=="A" else CUSHION_DEPTH)
    while x_cur + s_b <= x_end + 1e-6:
        poly = [(x_cur, y),(x_cur+s_b, y),(x_cur+s_b, y+CUSHION_DEPTH),(x_cur, y+CUSHION_DEPTH),(x_cur, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{s_b}", font=("Arial",9,"bold"))
        x_cur += s_b; total += 1
    # GAUCHE
    x = F0x
    y_cur = F0y + (CUSHION_DEPTH if orientation=="A" else 0)
    while y_cur + s_g <= y_end + 1e-6:
        poly = [(x, y_cur),(x+CUSHION_DEPTH, y_cur),(x+CUSHION_DEPTH, y_cur+s_g),(x, y_cur+s_g),(x, y_cur)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{s_g}", font=("Arial",9,"bold"))
        y_cur += s_g; total += 1
    return total

def _lf_best_orientation_counts(pts, sizes):
    """Choisit A vs B pour maximiser le nb total de coussins avec tailles par côté."""
    F0x, F0y = pts["F0"]
    x_end = pts.get("Bx_", pts["Bx"])[0]
    y_end = pts.get("By_", pts["By"])[1]
    s_b = sizes["bas"]; s_g = sizes["gauche"]

    def cnt_A():
        # bas (off=0), gauche (off=+15)
        nb = int(max(0, (x_end - F0x)) // s_b)
        ng = int(max(0, (y_end - (F0y + CUSHION_DEPTH))) // s_g)
        waste = (x_end - F0x) % s_b + (y_end - (F0y + CUSHION_DEPTH)) % s_g
        return (nb+ng, -waste, "A")
    def cnt_B():
        nb = int(max(0, (x_end - (F0x + CUSHION_DEPTH))) // s_b)
        ng = int(max(0, (y_end - F0y)) // s_g)
        waste = (x_end - (F0x + CUSHION_DEPTH)) % s_b + (y_end - F0y) % s_g
        return (nb+ng, -waste, "B")
    return max([cnt_A(), cnt_B()], key=lambda k:(k[0], k[1]))

def draw_cousins_and_return_count(t, tr, pts, tx, ty, coussins, meridienne_side, meridienne_len):
    """
    *** LF ***
    Ancienne signature conservée ; désormais accepte modes valise/p/g/s/auto/fixed,
    planifie des tailles par côté (bas/gauche) en respectant l'écart global ≤ 5 (sauf same),
    puis choisit l'orientation A/B optimale et dessine.
    """
    # 1) normalisation
    mode, same, size_fixed, tag = _norm_coussins_spec(coussins)
    lengths = _choose_cushion_size_auto_LF_lengths(pts, tx, ty, meridienne_side, meridienne_len)

    # 2) contrôles borne + fixed injection
    if mode=="fixed":
        v=int(size_fixed)
        if not (60 <= v <= 100):
            raise ValueError("Taille coussins fixe hors bornes [60..100].")
        _plan_sizes_for_branches._fixed_value = v

    # 3) planification tailles
    sizes, meta = _plan_sizes_for_branches(lengths, mode, same=same)

    # 4) orientation optimale + dessin
    _, _, orient = _lf_best_orientation_counts(pts, sizes)
    count = _lf_draw_cushions_per_side(t, tr, pts, sizes, orientation=orient)
    # Renvoie total + info choisie (ancienne API : count, "size")
    # Ici, pour compat, on renvoie la taille bas si uniforme, sinon la moyenne arrondie
    chosen_size = sizes["bas"] if sizes.get("bas")==sizes.get("gauche") else int(round(sum(sizes.values())/len(sizes)))
    # Impression console détaillée assurée par render (plus bas)
    return count, chosen_size, sizes, meta

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
                      window_title="LF — variantes"):
    if meridienne_side == 'g' and acc_left:
        raise ValueError("Erreur: une méridienne gauche ne peut pas coexister avec un accoudoir gauche.")
    if meridienne_side == 'b' and acc_bas:
        raise ValueError("Erreur: une méridienne bas ne peut pas coexister avec un accoudoir bas.")

    pts=compute_points_LF_variant(tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    polys=build_polys_LF_variant(pts,tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    _assert_banquettes_max_250(polys)

    full_title = f"{window_title} — {tx}x{ty} cm — prof={profondeur} — méridienne {meridienne_side or '-'}={meridienne_len} — coussins={coussins}"
    fig_w = WIN_W / 100.0
    fig_h = WIN_H / 100.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.suptitle(full_title)
    try:
        fig.canvas.manager.set_window_title(full_title)
    except Exception:
        pass
    ax.set_aspect("equal")
    ax.axis("off")
    tr = WorldToScreen(tx, ty, WIN_W, WIN_H, PAD_PX, ZOOM)
    x_min = tr.left_px - PAD_PX / 2
    x_max = tr.left_px + tx * tr.scale + PAD_PX / 2
    y_min = tr.bottom_px - PAD_PX / 2
    y_max = tr.bottom_px + ty * tr.scale + PAD_PX / 2
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    t = ax

    draw_grid_cm(t,tr,tx,ty,GRID_MINOR_STEP,COLOR_GRID_MINOR,1)
    draw_grid_cm(t,tr,tx,ty,GRID_MAJOR_STEP,COLOR_GRID_MAJOR,1)
    draw_axis_labels_cm(t,tr,tx,ty,AXIS_LABEL_STEP,AXIS_LABEL_MAX)

    for poly in polys["dossiers"]:   draw_polygon_cm(t,tr,poly,fill=COLOR_DOSSIER)
    for poly in polys["banquettes"]: draw_polygon_cm(t,tr,poly,fill=COLOR_ASSISE)
    for poly in polys["accoudoirs"]: draw_polygon_cm(t,tr,poly,fill=COLOR_ACC)
    for poly in polys["angle"]:      draw_polygon_cm(t,tr,poly,fill=COLOR_ASSISE)

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

    count, chosen_size, sizes_by_side, meta = draw_cousins_and_return_count(
        t,tr,pts,tx,ty,coussins,meridienne_side,meridienne_len
    )

    # No tracer/hideturtle needed for matplotlib
    # Dossiers + scissions
    add_split = int(polys["split_flags"]["left"] and dossier_left) + int(polys["split_flags"]["bottom"] and dossier_bas)
    print("=== Rapport canapé (LF) ===")
    print(f"Dimensions : {tx}×{ty} cm — profondeur : {profondeur} cm")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers : {len(polys['dossiers'])} (+{add_split} via scission) | Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 1")
    # détail coussins
    s_b = sizes_by_side.get("bas"); s_g = sizes_by_side.get("gauche")
    print(f"Coussins (mode={meta['mode']}, Δ={meta['delta']}, uniform={meta['uniform']}, set={meta['set']})")
    print(f"  - Bas    : taille {s_b} cm")
    print(f"  - Gauche : taille {s_g} cm")
    print(f"  -> Total : {count} coussins   (taille affichée : {chosen_size} cm)")
    plt.show()

# ============================================================
# ==================  U2f (2 angles fromage)  =================
# ============================================================
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

def _u2f_nominal_lengths(pts):
    F0x, F0y = pts["F0"]
    F02x = pts["F02"][0]
    y_end_L = pts.get("By_", pts["By"])[1]
    y_end_R = pts.get("By4_", pts["By4"])[1]
    Lb = max(0, F02x - F0x)
    Lg = max(0, y_end_L - F0y)
    Ld = max(0, y_end_R - F0y)
    return {"bas":Lb, "gauche":Lg, "droite":Ld}

def _draw_cushions_U2f_with_sizes(t, tr, pts, sizes):
    """Dessine U2F avec tailles par côté et décalages optimisés (comme avant mais par-côté)."""
    F0x, F0y = pts["F0"]
    F02x = pts["F02"][0]
    y_end_L = pts.get("By_", pts["By"])[1]
    y_end_R = pts.get("By4_", pts["By4"])[1]
    s_b = sizes["bas"]; s_l = sizes["gauche"]; s_r = sizes["droite"]

    def cnt(shift_left, shift_right):
        xs = F0x + (CUSHION_DEPTH if shift_left else 0)
        xe = F02x - (CUSHION_DEPTH if shift_right else 0)
        bas = int(max(0, xe - xs) // s_b)
        yL0 = F0y + (0 if shift_left else CUSHION_DEPTH)
        yR0 = F0y + (0 if shift_right else CUSHION_DEPTH)
        g = int(max(0, y_end_L - yL0) // s_l)
        d = int(max(0, y_end_R - yR0) // s_r)
        waste = (max(0, xe - xs) % s_b if xe>xs else 1e9) \
              + (max(0, y_end_L - yL0) % s_l if y_end_L>yL0 else 1e9) \
              + (max(0, y_end_R - yR0) % s_r if y_end_R>yR0 else 1e9)
        return (bas+g+d, -waste, shift_left, shift_right)

    best = max([cnt(False,False), cnt(True,False), cnt(False,True), cnt(True,True)], key=lambda s:(s[0], s[1]))
    _, _, shL, shR = best

    total=0
    # Bas
    y, x = F0y, F0x + (CUSHION_DEPTH if shL else 0)
    xe = F02x - (CUSHION_DEPTH if shR else 0)
    while x + s_b <= xe + 1e-6:
        poly=[(x,y),(x+s_b,y),(x+s_b,y+CUSHION_DEPTH),(x,y+CUSHION_DEPTH),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{s_b}",font=("Arial",9,"bold"))
        x += s_b; total += 1
    # Gauche
    x, y = F0x, F0y + (0 if shL else CUSHION_DEPTH)
    while y + s_l <= y_end_L + 1e-6:
        poly=[(x,y),(x+CUSHION_DEPTH,y),(x+CUSHION_DEPTH,y+s_l),(x,y+s_l),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{s_l}",font=("Arial",9,"bold"))
        y += s_l; total += 1
    # Droite
    x, y = F02x, F0y + (0 if shR else CUSHION_DEPTH)
    while y + s_r <= y_end_R + 1e-6:
        poly=[(x-CUSHION_DEPTH,y),(x,y),(x,y+s_r),(x-CUSHION_DEPTH,y+s_r),(x-CUSHION_DEPTH,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{s_r}",font=("Arial",9,"bold"))
        y += s_r; total += 1
    return total, {"shift_left":shL, "shift_right":shR}

def _choose_cushions_U2f_plan(pts, coussins):
    mode, same, size_fixed, tag = _norm_coussins_spec(coussins)
    lengths = _u2f_nominal_lengths(pts)

    if mode=="fixed":
        v=int(size_fixed)
        if not (60 <= v <= 100): raise ValueError("Taille coussins fixe hors bornes [60..100].")
        _plan_sizes_for_branches._fixed_value = v
    sizes, meta = _plan_sizes_for_branches(lengths, mode, same=same)
    return sizes, meta

def render_U2f_variant(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                       dossier_left=True, dossier_bas=True, dossier_right=True,
                       acc_left=True, acc_bas=True, acc_right=True,
                       meridienne_side=None, meridienne_len=0,
                       coussins="auto",
                       window_title="U2f — variantes"):
    if meridienne_side == 'g' and acc_left:
        raise ValueError("Erreur: une méridienne gauche ne peut pas coexister avec un accoudoir gauche.")
    if meridienne_side == 'd' and acc_right:
        raise ValueError("Erreur: une méridienne droite ne peut pas coexister avec un accoudoir droit.")

    pts = compute_points_U2f(tx, ty_left, tz_right, profondeur,
                             dossier_left, dossier_bas, dossier_right,
                             acc_left, acc_bas, acc_right,
                             meridienne_side, meridienne_len)
    polys = build_polys_U2f(pts, tx, ty_left, tz_right, profondeur,
                            dossier_left, dossier_bas, dossier_right,
                            acc_left, acc_bas, acc_right)
    _assert_banquettes_max_250(polys)

    ty_canvas = pts["_ty_canvas"]
    # Titre de la figure
    full_title = f"{window_title} — tx={tx} / ty(left)={ty_left} / tz(right)={tz_right} — prof={profondeur}"
    fig_w = WIN_W / 100.0
    fig_h = WIN_H / 100.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.suptitle(full_title)
    try:
        fig.canvas.manager.set_window_title(full_title)
    except Exception:
        pass
    ax.set_aspect("equal")
    ax.axis("off")
    tr = WorldToScreen(tx, ty_canvas, WIN_W, WIN_H, PAD_PX, ZOOM)
    x_min = tr.left_px - PAD_PX / 2
    x_max = tr.left_px + tx * tr.scale + PAD_PX / 2
    y_min = tr.bottom_px - PAD_PX / 2
    y_max = tr.bottom_px + ty_canvas * tr.scale + PAD_PX / 2
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    t = ax

    draw_grid_cm(t, tr, tx, ty_canvas, GRID_MINOR_STEP, COLOR_GRID_MINOR, 1)
    draw_grid_cm(t, tr, tx, ty_canvas, GRID_MAJOR_STEP, COLOR_GRID_MAJOR, 1)
    draw_axis_labels_cm(t, tr, tx, ty_canvas, AXIS_LABEL_STEP, AXIS_LABEL_MAX)

    for poly in polys["dossiers"]:   draw_polygon_cm(t, tr, poly, fill=COLOR_DOSSIER)
    for poly in polys["banquettes"]: draw_polygon_cm(t, tr, poly, fill=COLOR_ASSISE)
    for poly in polys["accoudoirs"]: draw_polygon_cm(t, tr, poly, fill=COLOR_ACC)
    for poly in polys["angles"]:     draw_polygon_cm(t, tr, poly, fill=COLOR_ASSISE)

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

    # === COUSSINS (VALISE) ===
    sizes_by_side, meta = _choose_cushions_U2f_plan(pts, coussins)
    cushions_count, shifts = _draw_cushions_U2f_with_sizes(t, tr, pts, sizes_by_side)

    # No tracer/hideturtle needed for matplotlib
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
    print(f"Coussins (mode={meta['mode']}, Δ={meta['delta']}, uniform={meta['uniform']}, set={meta['set']})")
    print(f"  - Gauche : taille {sizes_by_side.get('gauche')} cm")
    print(f"  - Bas    : taille {sizes_by_side.get('bas')} cm")
    print(f"  - Droite : taille {sizes_by_side.get('droite')} cm")
    print(f"  -> Total : {cushions_count} coussins  |  shifts: L={shifts['shift_left']} R={shifts['shift_right']}")
    plt.show()

# ============================================================
# ===================  U1F (1 angle fromage)  =================
# ============================================================
# ... (SECTION U1F INCHANGÉE SAUF COUSSINS) ...

# --- utilitaires spécifiques U1F ---
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

# --- NOUVELLES FONCTIONS : longueurs et dessin U1F (valise) ---
def _u1f_nominal_lengths(pts):
    F0x, F0y = pts["F0"]; F02x = pts["F02"][0]
    x_len = max(0, F02x - F0x)
    y_end_L = pts["By_cush"][1]
    y_end_R = pts["By4_cush"][1]
    yL = max(0, y_end_L - F0y)
    yR = max(0, y_end_R - F0y)
    return {"bas":x_len, "gauche":yL, "droite":yR}

def _draw_coussins_U1F_sizes(t, tr, pts, sizes):
    F0x, F0y = pts["F0"]; F02x = pts["F02"][0]
    y_end_L = pts["By_cush"][1]; y_end_R = pts["By4_cush"][1]
    sb=sizes["bas"]; sl=sizes["gauche"]; sr=sizes["droite"]

    def cnt(shift_left, shift_right):
        xs = F0x + (CUSHION_DEPTH if shift_left else 0)
        xe = F02x - (CUSHION_DEPTH if shift_right else 0)
        nb = int(max(0, xe - xs) // sb)
        yL0 = F0y + (0 if shift_left else CUSHION_DEPTH)
        yR0 = F0y + (0 if shift_right else CUSHION_DEPTH)
        ng = int(max(0, y_end_L - yL0) // sl)
        nd = int(max(0, y_end_R - yR0) // sr)
        waste = (max(0, xe - xs) % sb) + (max(0, y_end_L - yL0) % sl) + (max(0, y_end_R - yR0) % sr)
        return (nb+ng+nd, -waste, shift_left, shift_right)
    best = max([cnt(False,False), cnt(True,False), cnt(False,True), cnt(True,True)], key=lambda k:(k[0],k[1]))
    _, _, shL, shR = best

    total=0
    # BAS
    y=F0y; x=F0x + (CUSHION_DEPTH if shL else 0); xe = F02x - (CUSHION_DEPTH if shR else 0)
    while x + sb <= xe + 1e-6:
        poly=[(x,y),(x+sb,y),(x+sb,y+CUSHION_DEPTH),(x,y+CUSHION_DEPTH),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sb}",font=("Arial",9,"bold"))
        x += sb; total += 1
    # GAUCHE
    x=F0x; y=F0y + (0 if shL else CUSHION_DEPTH)
    while y + sl <= y_end_L + 1e-6:
        poly=[(x,y),(x+CUSHION_DEPTH,y),(x+CUSHION_DEPTH,y+sl),(x,y+sl),(x,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sl}",font=("Arial",9,"bold"))
        y += sl; total += 1
    # DROITE
    x=F02x; y=F0y + (0 if shR else CUSHION_DEPTH)
    while y + sr <= y_end_R + 1e-6:
        poly=[(x-CUSHION_DEPTH,y),(x,y),(x,y+sr),(x-CUSHION_DEPTH,y+sr),(x-CUSHION_DEPTH,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sr}",font=("Arial",9,"bold"))
        y += sr; total += 1
    return total, {"shift_left":shL, "shift_right":shR}

# ---------------- v1 ----------------
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

# ---------------- v2 ----------------
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

# ---------------- v3 ----------------
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

    # Colonne droite et hauteurs
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
    pts["_acc"]={"L":bool(acc_left), "R":bool(acc_right)}
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

# ---------------- v4 ----------------
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
        polys["dossiers"].append([pts["F0"], pts["Bx"], pts["Dx"], pts["D0x"], pts["F0"]])  # rectangle confirmé
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
                       coussins, window_title):
    comp = {"v1":compute_points_U1F_v1, "v2":compute_points_U1F_v2,
            "v3":compute_points_U1F_v3, "v4":compute_points_U1F_v4}[variant]
    build= {"v1":build_polys_U1F_v1,   "v2":build_polys_U1F_v2,
            "v3":build_polys_U1F_v3,   "v4":build_polys_U1F_v4}[variant]

    pts = comp(tx, ty, tz, profondeur,
               dossier_left, dossier_bas, dossier_right,
               acc_left, acc_right,
               meridienne_side, meridienne_len)
    polys = build(pts, tx, ty, tz, profondeur,
                  dossier_left, dossier_bas, dossier_right,
                  acc_left, acc_right)
    _assert_banquettes_max_250(polys)

    ty_canvas = max(ty, tz)
    full_title = f"U1F {variant} — {window_title} — tx={tx} / ty={ty} / tz={tz} — prof={profondeur}"
    fig_w = WIN_W / 100.0
    fig_h = WIN_H / 100.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.suptitle(full_title)
    try:
        fig.canvas.manager.set_window_title(full_title)
    except Exception:
        pass
    ax.set_aspect("equal")
    ax.axis("off")
    tr = WorldToScreen(tx, ty_canvas, WIN_W, WIN_H, PAD_PX, ZOOM)
    x_min = tr.left_px - PAD_PX / 2
    x_max = tr.left_px + tx * tr.scale + PAD_PX / 2
    y_min = tr.bottom_px - PAD_PX / 2
    y_max = tr.bottom_px + ty_canvas * tr.scale + PAD_PX / 2
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    t = ax

    draw_grid_cm(t, tr, tx, ty_canvas, GRID_MINOR_STEP, COLOR_GRID_MINOR, 1)
    draw_grid_cm(t, tr, tx, ty_canvas, GRID_MAJOR_STEP, COLOR_GRID_MAJOR, 1)
    draw_axis_labels_cm(t, tr, tx, ty_canvas, AXIS_LABEL_STEP, AXIS_LABEL_MAX)

    for p in polys["dossiers"]:
        xs=[pp[0] for pp in p]; ys=[pp[1] for pp in p]
        if (max(xs)-min(xs) > 1e-9) and (max(ys)-min(ys) > 1e-9):
            draw_polygon_cm(t, tr, p, fill=COLOR_DOSSIER)
    for p in polys["banquettes"]: draw_polygon_cm(t, tr, p, fill=COLOR_ASSISE)
    for p in polys["accoudoirs"]: draw_polygon_cm(t, tr, p, fill=COLOR_ACC)
    for p in polys["angle"]:      draw_polygon_cm(t, tr, p, fill=COLOR_ASSISE)

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

    # === COUSSINS (VALISE) ===
    mode, same, size_fixed, tag = _norm_coussins_spec(coussins)
    lengths = _u1f_nominal_lengths(pts)
    if mode=="fixed":
        v=int(size_fixed)
        if not (60 <= v <= 100): raise ValueError("Taille coussins fixe hors bornes [60..100].")
        _plan_sizes_for_branches._fixed_value = v
    sizes_by_side, meta = _plan_sizes_for_branches(lengths, mode, same=same)
    nb_coussins, shifts = _draw_coussins_U1F_sizes(t, tr, pts, sizes_by_side)

    # No tracer/hideturtle needed for matplotlib

    add_split = int(polys.get("split_flags",{}).get("any",False))
    print(f"=== Rapport U1F {variant} ===")
    print(f"Dimensions : tx={tx} / ty={ty} / tz={tz} — profondeur={profondeur} (A={A})")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers : {len(polys['dossiers'])} (+{add_split} via scission) | Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 1")
    print(f"Coussins (mode={meta['mode']}, Δ={meta['delta']}, uniform={meta['uniform']}, set={meta['set']})")
    print(f"  - Gauche : taille {sizes_by_side.get('gauche')} cm")
    print(f"  - Bas    : taille {sizes_by_side.get('bas')} cm")
    print(f"  - Droite : taille {sizes_by_side.get('droite')} cm")
    print(f"  -> Total : {nb_coussins} coussins  |  shifts: L={shifts['shift_left']} R={shifts['shift_right']}")
    plt.show()

def render_U1F_v1(*args, **kwargs): _render_common_U1F("v1", *args, **kwargs)
def render_U1F_v2(*args, **kwargs): _render_common_U1F("v2", *args, **kwargs)
def render_U1F_v3(*args, **kwargs): _render_common_U1F("v3", *args, **kwargs)
def render_U1F_v4(*args, **kwargs): _render_common_U1F("v4", *args, **kwargs)

# ============================================================
# ==================  L (no fromage) v1 + v2  =================
# ============================================================
# ---- v2 (pivot bas) ----
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

# ---- v1 (pivot gauche) ----
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

# ---- L : coussins (valise) ----
def _lengths_L(pts, tx, ty):
    F0x,F0y = pts["F0"]
    x_end = pts.get("Bx_mer", pts.get("Bx", (F0x,0)))[0]
    y_end = pts.get("By_mer", pts.get("By", (F0x,F0y)))[1]
    return {"bas": max(0, x_end - F0x), "gauche": max(0, y_end - F0y)}

def draw_coussins_L_optimized(t, tr, pts, coussins):
    mode, same, size_fixed, tag = _norm_coussins_spec(coussins)
    lengths = _lengths_L(pts, pts.get("_tx", 0), pts.get("_ty", 0))
    if mode=="fixed":
        v=int(size_fixed)
        if not (60 <= v <= 100):
            raise ValueError("Taille coussins fixe hors bornes [60..100].")
        _plan_sizes_for_branches._fixed_value = v
    sizes, meta = _plan_sizes_for_branches(lengths, mode, same=same)

    # Choix orientation A/B (comme avant)
    F0x, F0y = pts["F0"]
    x_end = pts.get("Bx_mer", pts["Bx"])[0]
    y_end = pts.get("By_mer", pts["By"])[1]
    sb, sg = sizes["bas"], sizes["gauche"]

    def cntA():
        cb = int(max(0, (x_end - F0x)) // sb)
        cg = int(max(0, (y_end - (F0y + CUSHION_DEPTH))) // sg)
        waste = (x_end - F0x) % sb + (y_end - (F0y + CUSHION_DEPTH)) % sg
        return (cb+cg, -waste, "A")
    def cntB():
        cb = int(max(0, (x_end - (F0x + CUSHION_DEPTH))) // sb)
        cg = int(max(0, (y_end - F0y)) // sg)
        waste = (x_end - (F0x + CUSHION_DEPTH)) % sb + (y_end - F0y) % sg
        return (cb+cg, -waste, "B")
    _, _, orient = max([cntA(), cntB()], key=lambda k:(k[0],k[1]))

    total=0
    # bas
    y = F0y
    x_cur = F0x + (0 if orient=="A" else CUSHION_DEPTH)
    while x_cur + sb <= x_end + 1e-6:
        poly=[(x_cur,y),(x_cur+sb,y),(x_cur+sb,y+CUSHION_DEPTH),(x_cur,y+CUSHION_DEPTH),(x_cur,y)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sb}",font=("Arial",9,"bold"))
        x_cur += sb; total += 1
    # gauche
    x = F0x
    y_cur = F0y + (CUSHION_DEPTH if orient=="A" else 0)
    while y_cur + sg <= y_end + 1e-6:
        poly=[(x,y_cur),(x+CUSHION_DEPTH,y_cur),(x+CUSHION_DEPTH,y_cur+sg),(x,y_cur+sg),(x,y_cur)]
        draw_polygon_cm(t,tr,poly,fill=COLOR_CUSHION,outline=COLOR_CONTOUR,width=1)
        label_poly(t,tr,poly,f"{sg}",font=("Arial",9,"bold"))
        y_cur += sg; total += 1

    chosen_size = sb if sb==sg else int(round((sb+sg)/2))
    return total, chosen_size, sizes, meta

def _render_common_L(tx, ty, pts, polys, coussins, window_title,
                     profondeur, dossier_left, dossier_bas, meridienne_side, meridienne_len):
    _assert_banquettes_max_250(polys)

    full_title = f"{window_title} — {tx}×{ty} — prof={profondeur} — méridienne {meridienne_side or '-'}={meridienne_len} — coussins={coussins}"
    fig_w = WIN_W / 100.0
    fig_h = WIN_H / 100.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.suptitle(full_title)
    try:
        fig.canvas.manager.set_window_title(full_title)
    except Exception:
        pass
    ax.set_aspect("equal")
    ax.axis("off")
    tr = WorldToScreen(tx, ty, WIN_W, WIN_H, PAD_PX, ZOOM)
    x_min = tr.left_px - PAD_PX / 2
    x_max = tr.left_px + tx * tr.scale + PAD_PX / 2
    y_min = tr.bottom_px - PAD_PX / 2
    y_max = tr.bottom_px + ty * tr.scale + PAD_PX / 2
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    t = ax

    draw_grid_cm(t,tr,tx,ty,GRID_MINOR_STEP,"#f0f0f0",1)
    draw_grid_cm(t,tr,tx,ty,GRID_MAJOR_STEP,"#dcdcdc",1)
    draw_axis_labels_cm(t,tr,tx,ty,AXIS_LABEL_STEP,AXIS_LABEL_MAX)

    for p in polys["dossiers"]:   draw_polygon_cm(t,tr,p,fill=COLOR_DOSSIER)
    for p in polys["banquettes"]: draw_polygon_cm(t,tr,p,fill=COLOR_ASSISE)
    for p in polys["accoudoirs"]: draw_polygon_cm(t,tr,p,fill=COLOR_ACC)

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

    cushions_count, chosen_size, sizes_by_side, meta = draw_coussins_L_optimized(t,tr,pts,coussins)

    # No tracer/hideturtle needed for matplotlib

    add_split = int(polys.get("split_flags",{}).get("left",False) and dossier_left) \
              + int(polys.get("split_flags",{}).get("bottom",False) and dossier_bas)

    print("=== Rapport LNF ===")
    print(f"Dimensions : {tx}×{ty} — prof={profondeur} — méridienne {meridienne_side or '-'}={meridienne_len}")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers : {len(polys['dossiers'])} (+{add_split} via scission) | Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 0")
    print(f"Coussins (mode={meta['mode']}, Δ={meta['delta']}, uniform={meta['uniform']}, set={meta['set']})")
    print(f"  - Bas    : taille {sizes_by_side.get('bas')} cm")
    print(f"  - Gauche : taille {sizes_by_side.get('gauche')} cm")
    print(f"  -> Total : {cushions_count} coussins   (affiché : {chosen_size} cm)")
    plt.show()

def render_LNF_v1(tx, ty, profondeur=DEPTH_STD,
                  dossier_left=True, dossier_bas=True,
                  acc_left=True, acc_bas=True,
                  meridienne_side=None, meridienne_len=0,
                  coussins="auto",
                  window_title="LNF v1 — pivot gauche"):
    if meridienne_side=='g':
        if acc_left: raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
        if not dossier_left: raise ValueError("Méridienne gauche impossible sans dossier gauche.")
    if meridienne_side=='b':
        if acc_bas: raise ValueError("Méridienne bas interdite avec accoudoir bas.")
        if not dossier_bas: raise ValueError("Méridienne bas impossible sans dossier bas.")
    pts = compute_points_LNF_v1(tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    polys = build_polys_LNF_v1(pts,tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    _render_common_L(tx,ty,pts,polys,coussins,window_title,profondeur,dossier_left,dossier_bas,meridienne_side,meridienne_len)

def render_LNF_v2(tx, ty, profondeur=DEPTH_STD,
                  dossier_left=True, dossier_bas=True,
                  acc_left=True, acc_bas=True,
                  meridienne_side=None, meridienne_len=0,
                  coussins="auto",
                  window_title="LNF v2 — pivot bas"):
    if meridienne_side=='g':
        if acc_left: raise ValueError("Méridienne gauche interdite avec accoudoir gauche.")
        if not dossier_left: raise ValueError("Méridienne gauche impossible sans dossier gauche.")
    if meridienne_side=='b':
        if acc_bas: raise ValueError("Méridienne bas interdite avec accoudoir bas.")
        if not dossier_bas: raise ValueError("Méridienne bas impossible sans dossier bas.")
    pts = compute_points_LNF_v2(tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    polys = build_polys_LNF_v2(pts,tx,ty,profondeur,dossier_left,dossier_bas,acc_left,acc_bas,meridienne_side,meridienne_len)
    _render_common_L(tx,ty,pts,polys,coussins,window_title,profondeur,dossier_left,dossier_bas,meridienne_side,meridienne_len)

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
               window_title="LNF — auto"):
    if variant and variant.lower() in ("v1", "v2"):
        chosen = variant.lower()
        if chosen == "v2":
            render_LNF_v2(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas,
                          meridienne_side, meridienne_len, coussins,
                          window_title=window_title)
        else:
            render_LNF_v1(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas,
                          meridienne_side, meridienne_len, coussins,
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
                      meridienne_side, meridienne_len, coussins,
                      window_title=window_title)
    else:
        render_LNF_v1(tx, ty, profondeur, dossier_left, dossier_bas, acc_left, acc_bas,
                      meridienne_side, meridienne_len, coussins,
                      window_title=window_title)

# ============================================================
# =================  U (no fromage) — v1..v4  =================
# ============================================================

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

# --- NOUVEAU : longueurs nominales et dessin par tailles (U no-fromage) ---
def _u_nominal_lengths(variant, pts):
    F0x, F0y = pts["F0"]
    if variant in ("v1","v3","v4"):
        x_end = pts["Bx"][0]
    else: # v2
        x_end = pts["F02"][0]
    y_end_L = pts["By"][1]
    y_end_R = pts["By4"][1]
    return {"bas": max(0, x_end - F0x), "gauche": max(0, y_end_L - F0y), "droite": max(0, y_end_R - F0y)}

def _draw_cushions_variant_U_sizes(t, tr, variant, pts, sizes, drawn):
    F0x, F0y = pts["F0"]
    if variant in ("v1","v4"):
        x_end = pts["Bx"][0]; x_col = pts["Bx"][0]
    else:
        x_end = pts["F02"][0]; x_col = pts["F02"][0]
    y_end_L = pts["By"][1]; y_end_R = pts["By4"][1]
    sb=sizes["bas"]; sl=sizes["gauche"]; sr=sizes["droite"]

    def cnt(shift_left, shift_right):
        xs = F0x + (CUSHION_DEPTH if shift_left else 0)
        xe = x_end - (CUSHION_DEPTH if shift_right else 0)
        bas = int(max(0, xe - xs) // sb)
        yL0 = F0y + (0 if (not drawn.get("D1", False) or shift_left) else CUSHION_DEPTH)
        has_right = drawn.get("D4", False) or drawn.get("D5", False)
        yR0 = F0y + (0 if (not has_right or shift_right) else CUSHION_DEPTH)
        g = int(max(0, y_end_L - yL0) // sl)
        d = int(max(0, y_end_R - yR0) // sr)
        waste = (max(0, xe - xs) % sb) + (max(0, y_end_L - yL0) % sl) + (max(0, y_end_R - yR0) % sr)
        return (bas+g+d, -waste, shift_left, shift_right)

    best = max([cnt(False,False), cnt(True,False), cnt(False,True), cnt(True,True)], key=lambda s:(s[0], s[1]))
    _, _, shL, shR = best

    total=0
    # bas
    y = F0y; x = F0x + (CUSHION_DEPTH if shL else 0)
    xe = x_end - (CUSHION_DEPTH if shR else 0)
    while x + sb <= xe + 1e-6:
        poly = [(x, y), (x+sb, y), (x+sb, y+CUSHION_DEPTH), (x, y+CUSHION_DEPTH), (x, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{sb}", font=("Arial", 9, "bold"))
        x += sb; total += 1

    # gauche
    x = F0x; y = F0y + (0 if shL else CUSHION_DEPTH)
    while y + sl <= y_end_L + 1e-6:
        poly = [(x, y), (x+CUSHION_DEPTH, y), (x+CUSHION_DEPTH, y+sl), (x, y+sl), (x, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{sl}", font=("Arial", 9, "bold"))
        y += sl; total += 1

    # droite
    x = x_col; y = F0y + (0 if shR else CUSHION_DEPTH)
    while y + sr <= y_end_R + 1e-6:
        poly = [(x - CUSHION_DEPTH, y), (x, y), (x, y+sr), (x - CUSHION_DEPTH, y+sr), (x - CUSHION_DEPTH, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{sr}", font=("Arial", 9, "bold"))
        y += sr; total += 1

    return total, {"shift_left":shL, "shift_right":shR}

def _choose_cushion_size_auto_U(variant, pts, drawn):
    # conservé pour compat (utilisé si coussins="auto")
    F0x, F0y = pts["F0"]
    x_end = pts["Bx"][0] if variant in ("v1","v4") else pts["F02"][0]
    y_end_L = pts["By"][1]; y_end_R = pts["By4"][1]
    best, best_score = 65, (1e9, -1)
    for s in (65, 80, 90):
        Lb = max(0, x_end - F0x)
        yL0 = F0y + (CUSHION_DEPTH if drawn.get("D1", False) else 0)
        yR0 = F0y + (CUSHION_DEPTH if (drawn.get("D4", False) or drawn.get("D5", False)) else 0)
        Lg = max(0, y_end_L - yL0); Ld = max(0, y_end_R - yR0)
        waste = max(Lb % s if Lb>0 else 0, Lg % s if Lg>0 else 0, Ld % s if Ld>0 else 0)
        score = (waste, -s)
        if score < best_score: best_score, best = score, s
    return best

def _render_common_U(variant, tx, ty_left, tz_right,
                     profondeur, dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_fn, build_fn):
    pts = compute_fn(tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right)
    polys, drawn = build_fn(pts, tx, ty_left, tz_right, profondeur,
                            dossier_left, dossier_bas, dossier_right,
                            acc_left, acc_bas, acc_right)
    _assert_banquettes_max_250(polys)

    ty_canvas = pts["_ty_canvas"]
    full_title = f"{window_title} — {variant} — tx={tx} / ty(left)={ty_left} / tz(right)={tz_right} — prof={profondeur}"
    fig_w = WIN_W / 100.0
    fig_h = WIN_H / 100.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.suptitle(full_title)
    try:
        fig.canvas.manager.set_window_title(full_title)
    except Exception:
        pass
    ax.set_aspect("equal")
    ax.axis("off")
    tr = WorldToScreen(tx, ty_canvas, WIN_W, WIN_H, PAD_PX, ZOOM)
    x_min = tr.left_px - PAD_PX / 2
    x_max = tr.left_px + tx * tr.scale + PAD_PX / 2
    y_min = tr.bottom_px - PAD_PX / 2
    y_max = tr.bottom_px + ty_canvas * tr.scale + PAD_PX / 2
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    t = ax

    draw_grid_cm(t, tr, tx, ty_canvas, GRID_MINOR_STEP, COLOR_GRID_MINOR, 1)
    draw_grid_cm(t, tr, tx, ty_canvas, GRID_MAJOR_STEP, COLOR_GRID_MAJOR, 1)
    draw_axis_labels_cm(t, tr, tx, ty_canvas, AXIS_LABEL_STEP, AXIS_LABEL_MAX)

    for p in polys["dossiers"]:
        if _poly_has_area(p): draw_polygon_cm(t, tr, p, fill=COLOR_DOSSIER)
    for p in polys["banquettes"]:
        draw_polygon_cm(t, tr, p, fill=COLOR_ASSISE)
    for p in polys["accoudoirs"]:
        draw_polygon_cm(t, tr, p, fill=COLOR_ACC)

    draw_double_arrow_vertical_cm(t, tr, -25, 0, ty_left,   f"{ty_left} cm")
    draw_double_arrow_vertical_cm(t, tr, tx+25, 0, tz_right, f"{tz_right} cm")
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

    # === COUSSINS (VALISE) ===
    mode, same, size_fixed, tag = _norm_coussins_spec(coussins)
    lengths = _u_nominal_lengths(variant, pts)
    if mode=="fixed":
        v=int(size_fixed)
        if not (60 <= v <= 100): raise ValueError("Taille coussins fixe hors bornes [60..100].")
        _plan_sizes_for_branches._fixed_value = v

    # Spécifique : si "auto" on garde l'algorithme existant (s unique 65/80/90)
    if mode=="auto":
        size = _choose_cushion_size_auto_U(variant, pts, drawn)
        sizes_by_side = {k:size for k in lengths.keys()}
        cushions_count, shifts = _draw_cushions_variant_U_sizes(t, tr, variant, pts, sizes_by_side, drawn)
        meta={"mode":"auto", "delta":0, "uniform":True, "set":"{65,80,90}"}
    else:
        sizes_by_side, meta = _plan_sizes_for_branches(lengths, mode, same=same)
        cushions_count, shifts = _draw_cushions_variant_U_sizes(t, tr, variant, pts, sizes_by_side, drawn)

    # No tracer/hideturtle needed for matplotlib

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
    print(f"Coussins (mode={meta['mode']}, Δ={meta['delta']}, uniform={meta['uniform']}, set={meta['set']})")
    print(f"  - Gauche : taille {sizes_by_side.get('gauche')} cm")
    print(f"  - Bas    : taille {sizes_by_side.get('bas')} cm")
    print(f"  - Droite : taille {sizes_by_side.get('droite')} cm")
    print(f"  -> Total : {cushions_count} coussins  |  shifts: L={shifts['shift_left']} R={shifts['shift_right']}")
    plt.show()

def render_U_v1(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                dossier_left=True, dossier_bas=True, dossier_right=True,
                acc_left=True, acc_bas=True, acc_right=True,
                coussins="auto", window_title="U v1"):
    _render_common_U("v1", tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_points_U_v1, build_polys_U_v1)

def render_U_v2(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                dossier_left=True, dossier_bas=True, dossier_right=True,
                acc_left=True, acc_bas=True, acc_right=True,
                coussins="auto", window_title="U v2"):
    _render_common_U("v2", tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_points_U_v2, build_polys_U_v2)

def render_U_v3(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                dossier_left=True, dossier_bas=True, dossier_right=True,
                acc_left=True, acc_bas=True, acc_right=True,
                coussins="auto", window_title="U v3"):
    _render_common_U("v3", tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_points_U_v3, build_polys_U_v3)

def render_U_v4(tx, ty_left, tz_right, profondeur=DEPTH_STD,
                dossier_left=True, dossier_bas=True, dossier_right=True,
                acc_left=True, acc_bas=True, acc_right=True,
                coussins="auto", window_title="U v4"):
    _render_common_U("v4", tx, ty_left, tz_right, profondeur,
                     dossier_left, dossier_bas, dossier_right,
                     acc_left, acc_bas, acc_right, coussins, window_title,
                     compute_points_U_v4, build_polys_U_v4)

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
             window_title="U — auto"):
    v = (variant or "auto").lower()
    if v in ("v1","v2","v3","v4"):
        return {"v1":render_U_v1, "v2":render_U_v2, "v3":render_U_v3, "v4":render_U_v4}[v](
            tx, ty_left, tz_right, profondeur,
            dossier_left, dossier_bas, dossier_right,
            acc_left, acc_bas, acc_right,
            coussins, window_title=f"{window_title} [{v}]"
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
                    coussins, variant=choice,
                    window_title=window_title)

# ============================================================
# ===================  SIMPLE droit (S1)  ====================
# ============================================================

def compute_points_simple_S1(tx, profondeur=DEPTH_STD,
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
                             meridienne_side=None, meridienne_len=0):
    x0 = pts["B0"][0]; x1 = pts["Bx"][0]
    if meridienne_side == 'g' and meridienne_len > 0:
        x0 = max(x0, pts.get("B0_m", (x0, 0))[0])
    if meridienne_side == 'd' and meridienne_len > 0:
        x1 = min(x1, pts.get("Bx_m", pts["Bx"])[0])

    def count(off):
        xs = x0 + off; xe = x1
        return int(max(0, xe - xs) // size)
    off = CUSHION_DEPTH if count(CUSHION_DEPTH) > count(0) else 0

    y = pts["B0"][1]
    x = x0 + off; n = 0
    while x + size <= x1 + 1e-6:
        poly = [(x, y), (x+size, y), (x+size, y+CUSHION_DEPTH), (x, y+CUSHION_DEPTH), (x, y)]
        draw_polygon_cm(t, tr, poly, fill=COLOR_CUSHION, outline=COLOR_CONTOUR, width=1)
        label_poly(t, tr, poly, f"{size}", font=("Arial", 9, "bold"))
        x += size; n += 1
    return n

def render_Simple1(tx,
                   profondeur=DEPTH_STD,
                   dossier=True,
                   acc_left=True, acc_right=True,
                   meridienne_side=None, meridienne_len=0,
                   coussins="auto",
                   window_title="Canapé simple 1"):
    pts   = compute_points_simple_S1(tx, profondeur, dossier, acc_left, acc_right,
                                     meridienne_side, meridienne_len)
    polys = build_polys_simple_S1(pts, dossier, acc_left, acc_right,
                                  meridienne_side, meridienne_len)
    _assert_banquettes_max_250(polys)

    full_title = f"{window_title} — tx={tx} / prof={profondeur} — méridienne {meridienne_side or '-'}={meridienne_len} — coussins={coussins}"
    fig_w = WIN_W / 100.0
    fig_h = WIN_H / 100.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.suptitle(full_title)
    try:
        fig.canvas.manager.set_window_title(full_title)
    except Exception:
        pass
    ax.set_aspect("equal")
    ax.axis("off")
    tr = WorldToScreen(tx, profondeur, WIN_W, WIN_H, PAD_PX, ZOOM)
    x_min = tr.left_px - PAD_PX / 2
    x_max = tr.left_px + tx * tr.scale + PAD_PX / 2
    y_min = tr.bottom_px - PAD_PX / 2
    y_max = tr.bottom_px + profondeur * tr.scale + PAD_PX / 2
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    t = ax

    draw_grid_cm(t, tr, tx, profondeur, GRID_MINOR_STEP, COLOR_GRID_MINOR, 1)
    draw_grid_cm(t, tr, tx, profondeur, GRID_MAJOR_STEP, COLOR_GRID_MAJOR, 1)
    draw_axis_labels_cm(t, tr, tx, profondeur, AXIS_LABEL_STEP, AXIS_LABEL_MAX)

    for p in polys["dossiers"]:
        if _poly_has_area(p):  draw_polygon_cm(t, tr, p, fill=COLOR_DOSSIER)
    for p in polys["banquettes"]:
        draw_polygon_cm(t, tr, p, fill=COLOR_ASSISE)
    for p in polys["accoudoirs"]:
        draw_polygon_cm(t, tr, p, fill=COLOR_ACC)

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

    # COUSSINS (valise)
    mode, same, size_fixed, tag = _norm_coussins_spec(coussins)
    x0 = pts.get("B0_m", pts["B0"])[0] if meridienne_side == 'g' else pts["B0"][0]
    x1 = pts.get("Bx_m", pts["Bx"])[0] if meridienne_side == 'd' else pts["Bx"][0]
    L = max(0, x1 - x0)

    if mode=="fixed":
        v=int(size_fixed)
        if not (60 <= v <= 100): raise ValueError("Taille coussins fixe hors bornes [60..100].")
        size = v
    elif mode=="auto":
        size = _choose_cushion_size_auto_simple_S1(x0, x1)
    else:
        lo, hi = _allowed_interval_for_mode(mode)
        if same:
            size = _choose_uniform_size_from_set([L], range(lo,hi+1))
        else:
            # une seule branche ⇒ l'écart global ≤ 5 est trivial ; choisir le meilleur s dans [lo..hi]
            size = _choose_uniform_size_from_set([L], range(lo,hi+1))

    nb_coussins = _draw_coussins_simple_S1(t, tr, pts, size, meridienne_side, meridienne_len)

    # No tracer/hideturtle needed for matplotlib
    add_split = int(polys.get("split_flags",{}).get("center",False) and dossier)
    print("=== Rapport Canapé simple 1 ===")
    print(f"Dimensions : {tx}×{profondeur} cm")
    print(f"Banquettes : {len(polys['banquettes'])} → {banquette_sizes}")
    print(f"Dossiers   : {len(polys['dossiers'])} (+{add_split} via scission)  |  Accoudoirs : {len(polys['accoudoirs'])}")
    print(f"Banquettes d’angle : 0")
    print(f"Coussins (mode={mode}{' same' if same else ''}) : {nb_coussins} × {size} cm")
    if meridienne_side:
        print(f"Méridienne : côté {'gauche' if meridienne_side=='g' else 'droit'} — {meridienne_len} cm")
    plt.show()

# ============================================================

# ---------- L (no-fromage) ----------
def TV_L_valise():
    # Valise libre 60..100, Δ≤5, orientation H/V auto
    render_LNF(
        tx=310, ty=330, profondeur=70,
        dossier_left=True, dossier_bas=True,
        acc_left=True, acc_bas=True,
        meridienne_side=None, meridienne_len=0,
        coussins="valise",
        variant="auto",
        window_title="L — valise (Δ≤5, 60..100)"
    )

def TV_L_p_same():
    # Petites tailles (60..74), même taille partout
    render_LNF(
        tx=300, ty=360, profondeur=70,
        dossier_left=True, dossier_bas=True,
        acc_left=True, acc_bas=True,
        meridienne_side=None, meridienne_len=0,
        coussins="p:s",
        variant="v2",
        window_title="L — p:s (same 60..74)"
    )

# ---------- U2f (U à 2 angles fromage) ----------
def TV_U2f_valise():
    render_U2f_variant(
        tx=560, ty_left=320, tz_right=300, profondeur=80,
        dossier_left=True, dossier_bas=True, dossier_right=True,
        acc_left=True, acc_bas=True, acc_right=True,
        meridienne_side=None, meridienne_len=0,
        coussins="valise",
        window_title="U2f — valise (Δ≤5, 60..100)"
    )

def TV_U2f_g_same_merD():
    # Grandes tailles (76..100), même taille, méridienne droite (acc_right OFF)
    render_U2f_variant(
        tx=400, ty_left=320, tz_right=360, profondeur=80,
        dossier_left=True, dossier_bas=True, dossier_right=True,
        acc_left=True, acc_bas=True, acc_right=False,   # requis pour meridienne droite
        meridienne_side='d', meridienne_len=130,
        coussins="g:s",
        window_title="U2f — g:s + méridienne droite"
    )

# ---------- U (no-fromage) ----------
def TV_U_valise_v3():
    render_U(
        tx=420, ty_left=340, tz_right=320, profondeur=90,
        dossier_left=True, dossier_bas=True, dossier_right=True,
        acc_left=True, acc_bas=False, acc_right=True,
        coussins="valise",
        variant="v3",
        window_title="U — valise (v3)"
    )

# ---------- U1F (1 angle fromage) ----------
def TV_U1F_p_same_v3():
    render_U1F_v3(
        tx=360, ty=360, tz=200, profondeur=70,
        dossier_left=True, dossier_bas=True, dossier_right=True,
        acc_left=True, acc_right=True,
        meridienne_side=None, meridienne_len=0,
        coussins="p:s",
        window_title="U1F v3 — p:s"
    )

# ---------- LF (L avec angle fromage) ----------
def TV_LF_valise():
    render_LF_variant(
        tx=480, ty=360, profondeur=70,
        dossier_left=True, dossier_bas=True,
        acc_left=True, acc_bas=True,
        meridienne_side=None, meridienne_len=0,
        coussins="valise",
        window_title="LF — valise"
    )

# ---------- Simple (droit S1) ----------
def TV_Simple_valise():
    render_Simple1(
        tx=360, profondeur=70,
        dossier=True, acc_left=True, acc_right=True,
        meridienne_side=None, meridienne_len=0,
        coussins="valise",
        window_title="Simple — valise"
    )


# ======== MAIN : décommentez exactement UNE ligne =========
if __name__ == "__main__":
    TV_L_valise()
    #TV_L_p_same()
    #TV_U2f_valise()
    #TV_U2f_g_same_merD()
    #TV_U_valise_v3()
    #TV_U1F_p_same_v3()
    #TV_LF_valise()
    # TV_Simple_valise()
    pass
