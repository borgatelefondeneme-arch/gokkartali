# =====================================================================
#  GÖK KARTALI 3D — Blender Modelleme Adım 2
#  Motorlar (eğik "caret" hava girişleri, kompresör fanı, 2D vektörel kare
#  egzoz nozulları, türbin + art yakıcı) ve iniş takımları (amortisör,
#  makas bağlantıları, lastik/jant, iniş takımı kapakları).
#
#  Önce Adım 1'i çalıştırır (sahne temizliği dahil), sonra üstüne ekler.
#  01_govde_kanat_kuyruk.py bu dosyayla AYNI klasörde olmalıdır.
#  Uyumluluk: Blender 4.0+ / 5.x
# =====================================================================
import bpy
import bmesh
import math
import os
import runpy
from mathutils import Vector, Matrix


# ---------------------------------------------------------------------
# 0) Adım 1'i çalıştır: sahneyi temizler, gövde/kanat/kuyruk/kanopiyi kurar
# ---------------------------------------------------------------------
def adim1_yolu():
    adaylar = []
    try:
        adaylar.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass
    sp = getattr(bpy.context, "space_data", None)
    if sp is not None and getattr(sp, "text", None) is not None and sp.text.filepath:
        adaylar.append(os.path.dirname(bpy.path.abspath(sp.text.filepath)))
    for t in bpy.data.texts:
        if t.filepath:
            adaylar.append(os.path.dirname(bpy.path.abspath(t.filepath)))
    for d in adaylar:
        p = os.path.join(d, "01_govde_kanat_kuyruk.py")
        if os.path.exists(p):
            return p
    raise FileNotFoundError("01_govde_kanat_kuyruk.py bu betikle aynı klasörde bulunamadı.")


A1 = runpy.run_path(adim1_yolu(), run_name="adim1")
obje_olustur = A1["obje_olustur"]
subdiv_ekle = A1["subdiv_ekle"]
bevel_ekle = A1["bevel_ekle"]
mirror_ekle = A1["mirror_ekle"]
materyal_olustur = A1["materyal_olustur"]
materyal_ata = A1["materyal_ata"]
giris = A1["giris"]


# ---------------------------------------------------------------------
# 1) EK MATERYALLER
# ---------------------------------------------------------------------
def ek_materyaller():
    m = {}
    m["boya"] = bpy.data.materials["GK_Boya_Hayalet"]
    m["motor"] = bpy.data.materials["GK_Motor_Metal"]

    ic, _, b = materyal_olustur("GK_HavaGirisi_Ic")          # emiş kanalı içi: mat koyu
    giris(b, "Base Color", (0.012, 0.013, 0.015, 1))
    giris(b, "Roughness", 0.75)
    m["ic"] = ic

    lastik, _, b = materyal_olustur("GK_Lastik")
    giris(b, "Base Color", (0.018, 0.018, 0.018, 1))
    giris(b, "Roughness", 0.88)
    giris(b, ["Specular IOR Level", "Specular"], 0.3)
    m["lastik"] = lastik

    krom, _, b = materyal_olustur("GK_Krom_Amortisor")
    giris(b, "Base Color", (0.85, 0.86, 0.88, 1))
    giris(b, "Metallic", 1.0)
    giris(b, "Roughness", 0.08)
    m["krom"] = krom

    takim, _, b = materyal_olustur("GK_InisTakimi_Boya")    # açık gri iniş takımı boyası
    giris(b, "Base Color", (0.62, 0.63, 0.64, 1))
    giris(b, "Metallic", 0.15)
    giris(b, "Roughness", 0.42)
    giris(b, ["Coat Weight", "Coat"], 0.25)
    m["takim"] = takim

    yuva, _, b = materyal_olustur("GK_TakimYuvasi")           # iniş takımı yuvası iç rengi
    giris(b, "Base Color", (0.28, 0.29, 0.30, 1))
    giris(b, "Roughness", 0.6)
    m["yuva"] = yuva

    alev, _, b = materyal_olustur("GK_ArtYakici")             # art yakıcı halkası (emisyon)
    giris(b, "Base Color", (0.05, 0.02, 0.01, 1))
    giris(b, ["Emission Color", "Emission"], (1.0, 0.42, 0.12, 1))
    giris(b, "Emission Strength", 6.0)
    m["alev"] = alev
    return m


# ---------------------------------------------------------------------
# Yardımcı: yuvarlatılmış dikdörtgen / paralelkenar kesit
# ---------------------------------------------------------------------
def kesit_noktalari(a, b, r, egim=0.0, n=40):
    """a: yarım genişlik, b: yarım yükseklik, r: köşe yarıçapı, egim: üst kenarın dışa kayması"""
    r = min(r, a * 0.95, b * 0.95)
    pts = []
    kose = [(a - r, b - r, 0.0), (-(a - r), b - r, math.pi / 2),
            (-(a - r), -(b - r), math.pi), (a - r, -(b - r), 1.5 * math.pi)]
    her = n // 4
    for cx, cy, a0 in kose:
        for k in range(her):
            ang = a0 + (math.pi / 2) * k / her
            u, v = cx + r * math.cos(ang), cy + r * math.sin(ang)
            pts.append((u + egim * v / b, v))
    return pts


def loft(ad, istasyonlar, kapat_on=False, kapat_arka=False):
    """istasyonlar: [dict(y, cx, cz, a, b, r, egim, lip=fn(u,v)->dy)] — kesitleri Y ekseni boyunca örer"""
    bm = bmesh.new()
    halkalar = []
    for s in istasyonlar:
        halka = []
        for (u, v) in kesit_noktalari(s["a"], s["b"], s["r"], s.get("egim", 0.0)):
            dy = s["lip"](u, v) if "lip" in s else 0.0
            halka.append(bm.verts.new((s["cx"] + u, s["y"] + dy, s["cz"] + v)))
        halkalar.append(halka)
    n = len(halkalar[0])
    for p, q in zip(halkalar, halkalar[1:]):
        for j in range(n):
            bm.faces.new((p[j], p[(j + 1) % n], q[(j + 1) % n], q[j]))
    if kapat_on:
        bm.faces.new(halkalar[0])
    if kapat_arka:
        bm.faces.new(halkalar[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return obje_olustur(ad, bm)


def kutu(bm, merkez, olcu, rot=Matrix.Identity(4)):
    M = Matrix.Translation(Vector(merkez)) @ rot @ Matrix.Diagonal(Vector((olcu[0], olcu[1], olcu[2], 1.0)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=M)


def silindir(bm, merkez, yaricap, uzunluk, eksen='Y', seg=32, r2=None):
    rot = {'X': Matrix.Rotation(math.pi / 2, 4, 'Y'), 'Y': Matrix.Rotation(math.pi / 2, 4, 'X'), 'Z': Matrix.Identity(4)}[eksen]
    M = Matrix.Translation(Vector(merkez)) @ rot
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=yaricap, radius2=yaricap if r2 is None else r2, depth=uzunluk, matrix=M)


def torus(bm, merkez, R, r, eksen='X', seg=48, yan=20):
    """eksen etrafında halka (lastik). bmesh'te hazır torus yok; elle örülür."""
    halkalar = []
    for i in range(seg):
        t = 2 * math.pi * i / seg
        halka = []
        for j in range(yan):
            p = 2 * math.pi * j / yan
            rr = R + r * math.cos(p)
            a, b_, c = rr * math.cos(t), rr * math.sin(t), r * math.sin(p)
            if eksen == 'X':
                co = (c, a, b_)
            elif eksen == 'Y':
                co = (a, c, b_)
            else:
                co = (a, b_, c)
            halka.append(bm.verts.new(Vector(merkez) + Vector(co)))
        halkalar.append(halka)
    for i in range(seg):
        p, q = halkalar[i], halkalar[(i + 1) % seg]
        for j in range(yan):
            bm.faces.new((p[j], p[(j + 1) % yan], q[(j + 1) % yan], q[j]))


# ---------------------------------------------------------------------
# 2) HAVA GİRİŞLERİ (Intake) — eğik/ok açılı "caret" ağız + iç kanal
# ---------------------------------------------------------------------
def hava_girisi_olustur(m):
    def dudak(u, v):          # ağız kenarı: alttan üste ve içten dışa ok açılı
        return 0.75 * (v / 0.6) - 0.45 * (u / 0.48)

    ist = [
        dict(y=3.45, cx=1.50, cz=-0.12, a=0.47, b=0.60, r=0.10, egim=0.30, lip=dudak),
        dict(y=2.80, cx=1.50, cz=-0.12, a=0.48, b=0.61, r=0.14, egim=0.24, lip=lambda u, v: 0.25 * dudak(u, v)),
        dict(y=1.50, cx=1.44, cz=-0.10, a=0.48, b=0.60, r=0.20, egim=0.12),
        dict(y=-0.60, cx=1.32, cz=-0.06, a=0.45, b=0.55, r=0.22, egim=0.06),
        dict(y=-3.20, cx=1.12, cz=0.00, a=0.38, b=0.48, r=0.22, egim=0.0),
    ]
    ob = loft("GK_HavaGirisi", ist)
    sol = ob.modifiers.new("DudakKalinligi", 'SOLIDIFY')
    sol.thickness = 0.045
    sol.offset = 1.0
    sol.material_offset = 1            # iç yüzey -> 2. materyal (koyu kanal)
    sol.use_even_offset = True
    mirror_ekle(ob)
    bevel_ekle(ob, 0.008, 2)
    subdiv_ekle(ob, 1, 2)
    materyal_ata(ob, m["boya"], m["ic"])
    return ob


def kompresor_fani_olustur(m, merkez=(1.44, 1.45, -0.10), yaricap=0.44, kanat=26):
    """Hava girişi içinde görünen ön fan: göbek konisi + burulmuş kanatçıklar"""
    bm = bmesh.new()
    cx, cy, cz = merkez
    gobek_r = yaricap * 0.32
    # göbek (spinner) — öne bakan koni
    M = Matrix.Translation(Vector((cx, cy + 0.08, cz))) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=gobek_r, radius2=0.01, depth=0.32, matrix=M)
    silindir(bm, (cx, cy - 0.12, cz), gobek_r, 0.25, 'Y', 32)
    # kanatçıklar
    L = yaricap - gobek_r
    for i in range(kanat):
        th = 2 * math.pi * i / kanat
        M = (Matrix.Translation(Vector((cx, cy - 0.05, cz)))
             @ Matrix.Rotation(th, 4, 'Y')
             @ Matrix.Translation(Vector((gobek_r + L / 2, 0, 0)))
             @ Matrix.Rotation(math.radians(38), 4, 'X')
             @ Matrix.Diagonal(Vector((L, 0.16, 0.012, 1.0))))
        bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    # dış gövde halkası (fan muhafazası)
    torus(bm, (cx, cy - 0.05, cz), yaricap + 0.01, 0.025, 'Y', 48, 10)
    ob = obje_olustur("GK_KompresorFani", bm)
    mirror_ekle(ob)
    bevel_ekle(ob, 0.004, 1)
    materyal_ata(ob, m["motor"])
    return ob


# ---------------------------------------------------------------------
# 3) EGZOZ NOZULLARI — 2D vektörel kare nozul + türbin yüzü + art yakıcı
# ---------------------------------------------------------------------
def nozul_olustur(m):
    cx, cz = 0.66, 0.02
    ist = [
        dict(y=-8.55, cx=cx, cz=cz, a=0.60, b=0.47, r=0.20),
        dict(y=-9.30, cx=cx, cz=cz, a=0.58, b=0.44, r=0.16),
        dict(y=-9.90, cx=cx, cz=cz, a=0.56, b=0.37, r=0.10),
        dict(y=-10.15, cx=cx, cz=cz, a=0.555, b=0.34, r=0.08),
    ]
    kabuk = loft("GK_Nozul", ist)
    sol = kabuk.modifiers.new("Kalinlik", 'SOLIDIFY')
    sol.thickness = 0.04
    sol.offset = -1.0
    sol.material_offset = 1
    mirror_ekle(kabuk)
    bevel_ekle(kabuk, 0.006, 2)
    subdiv_ekle(kabuk, 1, 2)
    materyal_ata(kabuk, m["boya"], m["motor"])

    # Üst/alt vektörel kanatçıklar (petal) — hafif içe kapalı
    bm = bmesh.new()
    for s in (1, -1):
        rot = Matrix.Rotation(math.radians(9) * s, 4, 'X')
        kutu(bm, (cx, -10.05, cz + s * 0.35), (1.06, 0.62, 0.035), rot)
    # yan duvar plakaları
    for s in (1, -1):
        kutu(bm, (cx + s * 0.57, -9.95, cz), (0.035, 0.5, 0.62))
    pet = obje_olustur("GK_NozulKanatcik", bm)
    mirror_ekle(pet)
    bevel_ekle(pet, 0.01, 2)
    materyal_ata(pet, m["motor"])

    # Türbin yüzü: arka disk + kanatçıklar + kuyruk konisi + alev tutucu halkalar
    bm = bmesh.new()
    ty = -9.25
    silindir(bm, (cx, ty, cz), 0.5, 0.04, 'Y', 48)
    for i in range(36):
        th = 2 * math.pi * i / 36
        M = (Matrix.Translation(Vector((cx, ty - 0.04, cz))) @ Matrix.Rotation(th, 4, 'Y')
             @ Matrix.Translation(Vector((0.29, 0, 0))) @ Matrix.Rotation(math.radians(-30), 4, 'X')
             @ Matrix.Diagonal(Vector((0.36, 0.08, 0.01, 1.0))))
        bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    M = Matrix.Translation(Vector((cx, ty - 0.3, cz))) @ Matrix.Rotation(math.pi / 2, 4, 'X')
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.15, radius2=0.02, depth=0.5, matrix=M)
    turb = obje_olustur("GK_Turbin", bm)
    mirror_ekle(turb)
    materyal_ata(turb, m["motor"])

    bm = bmesh.new()
    for rr in (0.22, 0.36):
        torus(bm, (cx, ty - 0.45, cz), rr, 0.018, 'Y', 48, 8)
    alev = obje_olustur("GK_ArtYakiciHalka", bm)
    mirror_ekle(alev)
    materyal_ata(alev, m["alev"])
    return kabuk


# ---------------------------------------------------------------------
# 4) İNİŞ TAKIMLARI — burun + 2 ana takım (açık konumda)
# ---------------------------------------------------------------------
ZEMIN_Z = -2.45


def tekerlek(bm_lastik, bm_jant, merkez, R, genislik):
    r_kesit = genislik * 0.5
    torus(bm_lastik, merkez, R - r_kesit, r_kesit, 'X', 48, 20)
    silindir(bm_jant, merkez, (R - r_kesit) * 0.92, genislik * 0.92, 'X', 40)
    # jant göbeği ve bijonlar
    silindir(bm_jant, merkez, R * 0.28, genislik * 1.05, 'X', 24)
    for i in range(6):
        a = 2 * math.pi * i / 6
        p = (merkez[0] + genislik * 0.48, merkez[1] + math.cos(a) * R * 0.38, merkez[2] + math.sin(a) * R * 0.38)
        silindir(bm_jant, p, 0.02, 0.04, 'X', 10)


def takim_ayagi(bm_boya, bm_krom, ust, alt, r_dis=0.075, r_ic=0.055):
    """Amortisör: üst boyalı silindir + alt krom piston + makas (torque link)"""
    ust, alt = Vector(ust), Vector(alt)
    yon = (alt - ust)
    L = yon.length
    rot = yon.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    orta1 = ust + yon * 0.3
    bmesh.ops.create_cone(bm_boya, cap_ends=True, segments=24, radius1=r_dis, radius2=r_dis, depth=L * 0.6,
                          matrix=Matrix.Translation(orta1) @ rot)
    orta2 = ust + yon * 0.75
    bmesh.ops.create_cone(bm_krom, cap_ends=True, segments=24, radius1=r_ic, radius2=r_ic, depth=L * 0.5,
                          matrix=Matrix.Translation(orta2) @ rot)
    # makas bağlantıları (iki parçalı, öne doğru kırık)
    m1 = ust + yon * 0.55 + Vector((0, 0.09, 0))
    m2 = ust + yon * 0.75 + Vector((0, 0.09, 0))
    kutu(bm_boya, m1, (0.03, 0.05, L * 0.22), Matrix.Rotation(math.radians(20), 4, 'X'))
    kutu(bm_boya, m2, (0.03, 0.05, L * 0.22), Matrix.Rotation(math.radians(-20), 4, 'X'))


def inis_takimlari_olustur(m):
    bm_boya, bm_krom, bm_lastik, bm_jant, bm_kapak, bm_yuva = (bmesh.new() for _ in range(6))

    # --- Burun takımı (tek teker, kokpit altında)
    nR, nG = 0.33, 0.20
    n_merkez = (0.0, 5.55, ZEMIN_Z + nR)
    takim_ayagi(bm_boya, bm_krom, (0.0, 5.75, -0.55), (0.0, 5.55, n_merkez[2] + 0.12))
    kutu(bm_boya, (0.0, 5.55, n_merkez[2] + 0.06), (0.30, 0.12, 0.1))            # çatal
    tekerlek(bm_lastik, bm_jant, (n_merkez[0] - 0.0, n_merkez[1], n_merkez[2]), nR, nG)
    # burun takımı yuvası ve kapakları
    kutu(bm_yuva, (0.0, 5.6, -0.66), (0.42, 1.5, 0.06))
    for s in (1, -1):
        kutu(bm_kapak, (s * 0.24, 5.6, -0.9), (0.02, 1.3, 0.42), Matrix.Rotation(math.radians(8) * s, 4, 'Y'))

    # --- Ana takımlar (gövde altından, gövdeye doğru içe eğik)
    mR, mG = 0.43, 0.26
    for s in (1, -1):
        mx = s * 1.72
        m_merkez = (mx, -1.05, ZEMIN_Z + mR)
        takim_ayagi(bm_boya, bm_krom, (s * 1.45, -0.85, -0.62), (mx, -1.05, m_merkez[2] + 0.14), 0.095, 0.07)
        kutu(bm_boya, (mx - s * 0.12, -1.05, m_merkez[2]), (0.1, 0.14, 0.14))  # aks yatağı
        tekerlek(bm_lastik, bm_jant, (mx + s * 0.06, -1.05, m_merkez[2]), mR, mG)
        # yan destek çubuğu (drag brace)
        takim_ayagi(bm_boya, bm_krom, (s * 1.25, -2.0, -0.6), (mx - s * 0.05, -1.2, m_merkez[2] + 0.55), 0.035, 0.03)
        # yuva ve büyük ana kapak
        kutu(bm_yuva, (s * 1.45, -1.2, -0.72), (0.75, 2.0, 0.05))
        kutu(bm_kapak, (s * 2.0, -1.2, -1.15), (0.03, 1.9, 0.85), Matrix.Rotation(math.radians(-14) * s, 4, 'Y'))

    obs = []
    for ad, bm, mat in (("GK_TakimBoya", bm_boya, m["takim"]), ("GK_TakimKrom", bm_krom, m["krom"]),
                        ("GK_Lastikler", bm_lastik, m["lastik"]), ("GK_Jantlar", bm_jant, m["takim"]),
                        ("GK_TakimKapaklari", bm_kapak, m["boya"]), ("GK_TakimYuvalari", bm_yuva, m["yuva"])):
        ob = obje_olustur(ad, bm)
        materyal_ata(ob, mat)
        if ad in ("GK_TakimBoya", "GK_Jantlar", "GK_TakimKapaklari", "GK_TakimYuvalari"):
            bevel_ekle(ob, 0.008, 2)
        if ad == "GK_Lastikler":
            subdiv_ekle(ob, 1, 1)
        obs.append(ob)
    # İniş takımlarını tek bir boş obje altında topla (ileride açıp kapatmak için)
    kok = bpy.data.objects.new("GK_InisTakimi", None)
    A1["koleksiyon"]().objects.link(kok)
    for ob in obs:
        ob.parent = kok
    return kok


# ---------------------------------------------------------------------
# ÇALIŞTIR
# ---------------------------------------------------------------------
def main():
    m = ek_materyaller()
    hava_girisi_olustur(m)
    kompresor_fani_olustur(m)
    nozul_olustur(m)
    inis_takimlari_olustur(m)
    print("GÖK KARTALI — Adım 2 tamam: hava girişleri, fanlar, nozullar, türbin, iniş takımları.")


main()
