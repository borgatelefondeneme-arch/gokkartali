# =====================================================================
#  GÖK KARTALI 3D — Blender Modelleme Adım 1
#  5. nesil hayalet savaş uçağı (F-22 sınıfı) — Gövde, Kanat, Kuyruk,
#  Kokpit camı, temel PBR materyaller, Nishita gökyüzü ve sinematik kamera.
#
#  Uyumluluk: Blender 4.0+ (4.2 LTS, 4.5 LTS ve 5.x dahil)
#  Birimler: metre. Burun +Y yönüne bakar (glTF dışa aktarımında oyunla uyumlu).
#  Ölçüler: Boy ~18.9 m, kanat açıklığı ~13.6 m, yükseklik ~5.1 m
# =====================================================================
import bpy
import bmesh
import math
from mathutils import Vector

KOLEKSIYON = "GK_Ucak"


# ---------------------------------------------------------------------
# 0) SAHNE TEMİZLİĞİ — her çalıştırmada eski objeleri ve artık verileri siler
# ---------------------------------------------------------------------
def sahneyi_temizle():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("GK_"):
            bpy.data.collections.remove(coll)
    veri_gruplari = (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                     bpy.data.lights, bpy.data.curves, bpy.data.node_groups,
                     bpy.data.images, bpy.data.textures)
    for grup in veri_gruplari:
        for blok in list(grup):
            if blok.users == 0:
                grup.remove(blok)


def koleksiyon():
    c = bpy.data.collections.get(KOLEKSIYON)
    if c is None:
        c = bpy.data.collections.new(KOLEKSIYON)
        bpy.context.scene.collection.children.link(c)
    return c


def obje_olustur(ad, bm):
    me = bpy.data.meshes.new(ad + "_Mesh")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(ad, me)
    koleksiyon().objects.link(ob)
    return ob


def subdiv_ekle(ob, seviye_viewport=1, seviye_render=2):
    m = ob.modifiers.new("Subdivision", 'SUBSURF')
    m.levels = seviye_viewport
    m.render_levels = seviye_render
    m.quality = 3
    return m


def bevel_ekle(ob, genislik=0.01, segment=2):
    m = ob.modifiers.new("Bevel", 'BEVEL')
    m.width = genislik
    m.segments = segment
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(40)
    m.harden_normals = False
    return m


def mirror_ekle(ob):
    m = ob.modifiers.new("Mirror", 'MIRROR')
    m.use_axis[0] = True
    m.use_clip = True
    m.use_mirror_merge = True
    m.merge_threshold = 0.002
    return m


# ---------------------------------------------------------------------
# Yardımcı: profil tablosundan yumuşak (smoothstep) ara değer
# ---------------------------------------------------------------------
def tablo(t, noktalar):
    if t <= noktalar[0][0]:
        return noktalar[0][1]
    for (t0, v0), (t1, v1) in zip(noktalar, noktalar[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return noktalar[-1][1]


# ---------------------------------------------------------------------
# 1) GÖVDE (Fuselage) — kesit kesit örülmüş süper-elips gövde
#    Burun bölümünde elmas kesitli "chine" (keskin yan sırt) — hayalet tasarım
# ---------------------------------------------------------------------
GOVDE_BOY = 18.9
BURUN_Y = GOVDE_BOY / 2          # +9.45
KUYRUK_Y = -GOVDE_BOY / 2        # -9.45

GENISLIK = [(0.0, 0.03), (0.06, 0.38), (0.16, 0.70), (0.28, 0.95), (0.38, 1.45),
            (0.48, 2.05), (0.62, 2.25), (0.80, 2.05), (0.93, 1.65), (1.0, 1.35)]
YUKSEKLIK = [(0.0, 0.03), (0.06, 0.30), (0.16, 0.52), (0.28, 0.72), (0.40, 0.80),
             (0.60, 0.74), (0.80, 0.62), (0.93, 0.50), (1.0, 0.42)]
DIKEY_KAYMA = [(0.0, -0.30), (0.12, -0.18), (0.28, 0.0), (1.0, 0.05)]
# süper-elips üssü: <2 elmas/keskin, 2 elips, >2 kutumsu
KESKINLIK = [(0.0, 1.35), (0.30, 1.6), (0.55, 2.6), (1.0, 3.0)]


def govde_olustur(istasyon=72, cevre=48):
    bm = bmesh.new()
    halkalar = []
    for i in range(istasyon):
        u = i / (istasyon - 1)
        t = u ** 1.35   # burun bölgesinde daha sık kesit
        y = BURUN_Y - t * GOVDE_BOY
        w, h = tablo(t, GENISLIK), tablo(t, YUKSEKLIK)
        zoff, n = tablo(t, DIKEY_KAYMA), tablo(t, KESKINLIK)
        halka = []
        for j in range(cevre):
            a = 2 * math.pi * j / cevre
            ca, sa = math.cos(a), math.sin(a)
            x = w * math.copysign(abs(ca) ** (2 / n), ca)
            z = h * math.copysign(abs(sa) ** (2 / n), sa) + zoff
            # sırt hafif yassı, karın daha düz (gerçek uçak kesiti)
            if z < zoff:
                z = zoff + (z - zoff) * 0.82
            halka.append(bm.verts.new((x, y, z)))
        halkalar.append(halka)
    bm.verts.ensure_lookup_table()

    for a, b in zip(halkalar, halkalar[1:]):
        for j in range(cevre):
            bm.faces.new((a[j], a[(j + 1) % cevre], b[(j + 1) % cevre], b[j]))
    # burun ucu: tek noktaya kapat
    uc = bm.verts.new((0, BURUN_Y + 0.05, tablo(0, DIKEY_KAYMA)))
    for j in range(cevre):
        bm.faces.new((uc, halkalar[0][(j + 1) % cevre], halkalar[0][j]))
    # kuyruk: motor egzoz yüzü (motor materyali atanacak)
    arka = bm.faces.new(halkalar[-1])
    arka.material_index = 1

    # Chine (yan sırt) kenarlarına crease — Subdivision sonrası keskin kalsın
    crease = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
    yan_indeksler = (0, cevre // 2)
    for k in range(istasyon - 1):
        tk = k / (istasyon - 1)
        if tk > 0.62:
            break
        for j in yan_indeksler:
            e = bm.edges.get((halkalar[k][j], halkalar[k + 1][j]))
            if e:
                e[crease] = 0.85 * (1 - tk / 0.62) + 0.15
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = obje_olustur("GK_Govde", bm)
    subdiv_ekle(ob, 1, 2)
    return ob


# ---------------------------------------------------------------------
# 2) KANAT PROFİLİ — NACA 4 haneli simetrik airfoil (kapalı firar kenarı)
# ---------------------------------------------------------------------
def naca_kesit(kalinlik, nokta=36):
    ust = []
    for i in range(nokta + 1):
        b = 0.5 - 0.5 * math.cos(math.pi * i / nokta)   # kosinüs dağılımı
        yt = 5 * kalinlik * (0.2969 * math.sqrt(b) - 0.1260 * b - 0.3516 * b ** 2
                             + 0.2843 * b ** 3 - 0.1036 * b ** 4)
        ust.append((b, yt))
    # firar kenarından hücum kenarına üst yüzey, sonra alt yüzey (tekrar yok)
    dongu = [(x, y) for x, y in reversed(ust)] + [(x, -y) for x, y in ust[1:-1]]
    return dongu


def kanat_lofts(ad, istasyonlar, kalinlik_kok, kalinlik_uc, kapat_kok=True, donustur=None):
    """istasyonlar: [(x_aciklik, y_hucum, chord, z, burulma_derece), ...] kökten uca"""
    bm = bmesh.new()
    halkalar = []
    for s, (x, y_le, chord, z, twist) in enumerate(istasyonlar):
        f = s / (len(istasyonlar) - 1)
        kesit = naca_kesit(kalinlik_kok + (kalinlik_uc - kalinlik_kok) * f)
        tw = math.radians(twist)
        halka = []
        for (b, yt) in kesit:
            dy = -b * chord
            dz = yt * chord
            # hücum kenarı etrafında burulma (washout)
            ry = dy * math.cos(tw) - dz * math.sin(tw)
            rz = dy * math.sin(tw) + dz * math.cos(tw)
            co = Vector((x, y_le + ry, z + rz))
            halka.append(bm.verts.new(donustur(co) if donustur else co))
        halkalar.append(halka)
    n = len(halkalar[0])
    for a, b in zip(halkalar, halkalar[1:]):
        for j in range(n):
            bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
    bm.faces.new(list(reversed(halkalar[-1])))   # kanat ucu kapağı
    if kapat_kok:
        bm.faces.new(halkalar[0])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = obje_olustur(ad, bm)
    return ob


def ana_kanat_olustur():
    # Elmas planform: hücum kenarı 42° geri, firar kenarı 17° ileri ok açısı
    kok_x, uc_x = 1.3, 6.78
    kok_le, kok_chord = 2.0, 7.6
    hucum_ok, firar_ok = math.radians(42), math.radians(17)
    anhedral = math.radians(-3.25)
    ist = []
    adim = 14
    for i in range(adim):
        f = i / (adim - 1)
        x = kok_x + (uc_x - kok_x) * f
        dx = x - kok_x
        y_le = kok_le - dx * math.tan(hucum_ok)
        y_te = (kok_le - kok_chord) + dx * math.tan(firar_ok)
        chord = max(1.2, y_le - y_te)
        z = 0.05 + dx * math.tan(anhedral)
        ist.append((x, y_le, chord, z, -1.5 * f))
    ob = kanat_lofts("GK_AnaKanat", ist, 0.055, 0.04)
    mirror_ekle(ob)
    bevel_ekle(ob, 0.004, 2)
    subdiv_ekle(ob, 1, 2)
    return ob


# ---------------------------------------------------------------------
# 3) KUYRUK TAKIMI (Empennage) — yatay stabilatörler + 28° yatık çift dikey kuyruk
# ---------------------------------------------------------------------
def yatay_stabilator_olustur():
    kok_x, uc_x = 1.9, 4.45
    kok_le, kok_chord = -5.7, 3.4
    ist = []
    for i in range(8):
        f = i / 7
        x = kok_x + (uc_x - kok_x) * f
        dx = x - kok_x
        y_le = kok_le - dx * math.tan(math.radians(42))
        y_te = (kok_le - kok_chord) + dx * math.tan(math.radians(14))
        ist.append((x, y_le, max(0.9, y_le - y_te), 0.0, 0))
    ob = kanat_lofts("GK_YatayStabilator", ist, 0.045, 0.035)
    mirror_ekle(ob)
    bevel_ekle(ob, 0.004, 2)
    subdiv_ekle(ob, 1, 2)
    return ob


def dikey_kuyruk_olustur():
    # Kanat lofts fonksiyonu x ekseninde açıklık kurar; dikey kuyruk için
    # önce yatay kurup sonra X ekseni etrafında 90° çevirip 28° dışa yatırıyoruz.
    yuk = 2.75
    kok_le, kok_chord = -3.9, 3.7
    ist = []
    for i in range(9):
        f = i / 8
        h = yuk * f
        y_le = kok_le - h * math.tan(math.radians(23))
        y_te = (kok_le - kok_chord) - h * math.tan(math.radians(-8))
        ist.append((h, y_le, max(0.85, y_le - y_te), 0.0, 0))
    yatik = math.radians(28)

    def dikey(co):
        # açıklık (x) -> yükseklik; kalınlık (z) -> yan; ardından 28° dışa yatırma
        yan, dik = co.z, co.x
        return Vector((1.55 + yan * math.cos(yatik) + dik * math.sin(yatik),
                       co.y,
                       0.55 - yan * math.sin(yatik) + dik * math.cos(yatik)))

    ob = kanat_lofts("GK_DikeyKuyruk", ist, 0.05, 0.035, donustur=dikey)
    mirror_ekle(ob)
    bevel_ekle(ob, 0.004, 2)
    subdiv_ekle(ob, 1, 2)
    return ob


# ---------------------------------------------------------------------
# 4) KOKPİT CAMI — tek parça damla (bubble) kanopi
# ---------------------------------------------------------------------
def kokpit_cami_olustur():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0)
    alt = [v for v in bm.verts if v.co.z < -0.02]
    bmesh.ops.delete(bm, geom=alt, context='VERTS')
    for v in bm.verts:
        x, y, z = v.co
        # arkaya doğru incelen damla şekli
        incelme = 1.0 - 0.35 * max(0.0, -y)
        v.co = Vector((x * 0.56 * incelme, y * 2.5, z * 0.58 * (0.75 + 0.25 * incelme)))
    ob = obje_olustur("GK_KokpitCami", bm)
    ob.location = (0, 4.15, 0.55)
    sol = ob.modifiers.new("Kalinlik", 'SOLIDIFY')
    sol.thickness = 0.02
    subdiv_ekle(ob, 1, 2)
    return ob


# ---------------------------------------------------------------------
# 5) MATERYALLER — Principled BSDF (Blender 4.x/5.x giriş adlarıyla)
# ---------------------------------------------------------------------
def giris(bsdf, adlar, deger):
    for ad in adlar if isinstance(adlar, (list, tuple)) else [adlar]:
        if ad in bsdf.inputs:
            bsdf.inputs[ad].default_value = deger
            return


def materyal_olustur(ad):
    mat = bpy.data.materials.new(ad)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    return mat, nt, bsdf


def materyaller_olustur():
    # 5.1 Hayalet boyası: koyu grafit, hafif metalik, ince vernik, pürüzlülük varyasyonu
    boya, nt, bsdf = materyal_olustur("GK_Boya_Hayalet")
    giris(bsdf, "Base Color", (0.055, 0.060, 0.068, 1))
    giris(bsdf, "Metallic", 0.55)
    giris(bsdf, ["Coat Weight", "Coat"], 0.35)
    giris(bsdf, "Coat Roughness", 0.18)
    giris(bsdf, ["Specular IOR Level", "Specular"], 0.5)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gurultu = nt.nodes.new("ShaderNodeTexNoise")
    gurultu.inputs["Scale"].default_value = 38.0
    gurultu.inputs["Detail"].default_value = 6.0
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].position = 0.35
    rampa.color_ramp.elements[0].color = (0.30, 0.30, 0.30, 1)
    rampa.color_ramp.elements[1].position = 0.70
    rampa.color_ramp.elements[1].color = (0.48, 0.48, 0.48, 1)
    nt.links.new(tc.outputs["Object"], gurultu.inputs["Vector"])
    nt.links.new(gurultu.outputs["Fac"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], bsdf.inputs["Roughness"])
    tc.location, gurultu.location, rampa.location = (-900, 0), (-700, 0), (-450, 0)

    # 5.2 Kokpit camı: altın kaplamalı, çok yansıtıcı koyu cam
    cam, nt2, b2 = materyal_olustur("GK_Cam_Kokpit")
    giris(b2, "Base Color", (0.42, 0.30, 0.10, 1))
    giris(b2, "Metallic", 0.85)
    giris(b2, "Roughness", 0.03)
    giris(b2, ["Coat Weight", "Coat"], 1.0)
    giris(b2, "Coat Roughness", 0.0)
    giris(b2, ["Transmission Weight", "Transmission"], 0.25)
    giris(b2, "IOR", 1.52)

    # 5.3 Motor içi metal: anizotropik fırçalanmış titanyum + ısı renklenmesi
    motor, nt3, b3 = materyal_olustur("GK_Motor_Metal")
    giris(b3, "Base Color", (0.33, 0.31, 0.29, 1))
    giris(b3, "Metallic", 1.0)
    giris(b3, "Roughness", 0.28)
    giris(b3, "Anisotropic", 0.6)
    lw = nt3.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    mix = nt3.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (0.33, 0.31, 0.29, 1)   # A: çelik
    mix.inputs[7].default_value = (0.28, 0.18, 0.35, 1)   # B: ısıdan mavimsi-mor ton
    nt3.links.new(lw.outputs["Facing"], mix.inputs[0])
    nt3.links.new(mix.outputs[2], b3.inputs["Base Color"])
    lw.location, mix.location = (-600, 0), (-350, 0)
    return boya, cam, motor


def materyal_ata(ob, *mats):
    ob.data.materials.clear()
    for m in mats:
        ob.data.materials.append(m)


# ---------------------------------------------------------------------
# 6) NISHITA GÖKYÜZÜ + GÜNEŞ — bulutların üzerinde gün batımı
# ---------------------------------------------------------------------
GUNES_YUKSEKLIK = math.radians(6.0)
GUNES_YON = math.radians(205.0)


def gokyuzu_kur():
    sc = bpy.context.scene
    dunya = bpy.data.worlds.get("GK_Dunya") or bpy.data.worlds.new("GK_Dunya")
    sc.world = dunya
    dunya.use_nodes = True
    nt = dunya.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    # Blender 4.x: 'NISHITA' / Blender 5.x: 'MULTIPLE_SCATTERING' (Nishita'nın devamı)
    for tip in ('NISHITA', 'MULTIPLE_SCATTERING'):
        try:
            sky.sky_type = tip
            break
        except TypeError:
            continue
    for ozellik, deger in (("sun_elevation", GUNES_YUKSEKLIK), ("sun_rotation", GUNES_YON),
                           ("altitude", 3200.0), ("air_density", 1.0), ("dust_density", 2.2),
                           ("ozone_density", 1.0), ("sun_size", math.radians(0.6)),
                           ("sun_intensity", 1.0), ("sun_disc", True)):
        if hasattr(sky, ozellik):
            setattr(sky, ozellik, deger)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.6
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    sky.location, bg.location, out.location = (-400, 0), (-150, 0), (100, 0)

    # EEVEE'de de net gölge için gökyüzündeki güneşle hizalı bir Güneş lambası
    isik = bpy.data.lights.new("GK_Gunes", 'SUN')
    isik.energy = 3.5
    isik.color = (1.0, 0.72, 0.48)
    isik.angle = math.radians(0.6)
    ob = bpy.data.objects.new("GK_Gunes", isik)
    koleksiyon().objects.link(ob)
    ob.rotation_euler = (math.pi / 2 - GUNES_YUKSEKLIK, 0.0, GUNES_YON + math.pi / 2)


# ---------------------------------------------------------------------
# 7) SİNEMATİK KAMERA + RENDER AYARLARI
# ---------------------------------------------------------------------
def kamera_kur():
    hedef = bpy.data.objects.new("GK_KameraHedef", None)
    koleksiyon().objects.link(hedef)
    hedef.location = (0.0, 0.8, 0.2)

    cam = bpy.data.cameras.new("GK_Kamera")
    cam.lens = 70
    cam.sensor_width = 36
    cam.dof.use_dof = True
    cam.dof.focus_object = hedef
    cam.dof.aperture_fstop = 5.6
    ob = bpy.data.objects.new("GK_Kamera", cam)
    koleksiyon().objects.link(ob)
    ob.location = (-15.5, 17.0, 3.2)      # sol-ön, hafif alçak 3/4 açı
    kisit = ob.constraints.new('TRACK_TO')
    kisit.target = hedef
    kisit.track_axis = 'TRACK_NEGATIVE_Z'
    kisit.up_axis = 'UP_Y'
    bpy.context.scene.camera = ob


def render_ayarla():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 256
    if hasattr(sc.cycles, "use_denoising"):
        sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.unit_settings.system = 'METRIC'
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Punchy'
    except TypeError:
        pass


# ---------------------------------------------------------------------
# ÇALIŞTIR
# ---------------------------------------------------------------------
def main():
    sahneyi_temizle()
    boya, cam, motor = materyaller_olustur()

    govde = govde_olustur()
    materyal_ata(govde, boya, motor)          # 0: boya, 1: egzoz yüzü

    kanat = ana_kanat_olustur()
    materyal_ata(kanat, boya)
    stab = yatay_stabilator_olustur()
    materyal_ata(stab, boya)
    kuyruk = dikey_kuyruk_olustur()
    materyal_ata(kuyruk, boya)
    kanopi = kokpit_cami_olustur()
    materyal_ata(kanopi, cam)

    gokyuzu_kur()
    kamera_kur()
    render_ayarla()
    print("GÖK KARTALI — Adım 1 tamam: gövde, kanat, kuyruk, kanopi, materyaller, Nishita gökyüzü.")


main()
