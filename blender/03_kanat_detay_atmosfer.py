# =====================================================================
#  GÖK KARTALI 3D — Blender Modelleme Adım 3
#  Kanat detayları: flaperon/kanatçık/stabilatör kontrol yüzeyleri (sapmalı),
#  LERX (kanat kökü uzantısı), silah yuvası kapakları, prosedürel panel çizgileri.
#  Atmosfer: uçağın altında hacimli (volumetrik) bulut denizi, gün batımı kamerası.
#
#  Önce Adım 2'yi (o da Adım 1'i) çalıştırır — sahne temizliği dahildir.
#  01, 02 ve 03 betikleri AYNI klasörde olmalıdır.
#  Uyumluluk: Blender 4.0+ / 5.x
# =====================================================================
import bpy
import bmesh
import math
import os
import runpy
from mathutils import Vector, Matrix

INIS_TAKIMI_ACIK = False      # uçuş sahnesi: iniş takımları kapalı (True yaparsan görünür)


def betik_yolu(dosya):
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
        p = os.path.join(d, dosya)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(dosya + " bu betikle aynı klasörde bulunamadı.")


A2 = runpy.run_path(betik_yolu("02_motor_inis.py"), run_name="adim2")
A1 = A2["A1"]
obje_olustur, subdiv_ekle, bevel_ekle = A1["obje_olustur"], A1["subdiv_ekle"], A1["bevel_ekle"]
mirror_ekle, materyal_olustur, materyal_ata, giris = A1["mirror_ekle"], A1["materyal_olustur"], A1["materyal_ata"], A1["giris"]
naca_kesit, kanat_lofts, koleksiyon = A1["naca_kesit"], A1["kanat_lofts"], A1["koleksiyon"]
kutu = A2["kutu"]


# ---------------------------------------------------------------------
# 1) KANAT PLANFORMU — Adım 1'deki ana kanatla birebir aynı ölçüler
# ---------------------------------------------------------------------
K_KOK_X, K_UC_X = 1.3, 6.78
K_KOK_LE, K_KOK_CHORD = 2.0, 7.6
K_HUCUM, K_FIRAR = math.radians(42), math.radians(17)
K_ANHEDRAL = math.radians(-3.25)


def kanat_istasyon(x):
    dx = x - K_KOK_X
    y_le = K_KOK_LE - dx * math.tan(K_HUCUM)
    y_te = (K_KOK_LE - K_KOK_CHORD) + dx * math.tan(K_FIRAR)
    f = (x - K_KOK_X) / (K_UC_X - K_KOK_X)
    return y_le, max(1.2, y_le - y_te), 0.05 + dx * math.tan(K_ANHEDRAL), -1.5 * f


def kesit_parcasi(kalinlik, b0, b1, olcek=1.06, nokta=14):
    """Airfoil'in b0..b1 (veter oranı) arasındaki arka parçası — kapalı kesit"""
    ust, alt = [], []
    for i in range(nokta + 1):
        b = b0 + (b1 - b0) * i / nokta
        yt = 5 * kalinlik * (0.2969 * math.sqrt(b) - 0.1260 * b - 0.3516 * b ** 2
                             + 0.2843 * b ** 3 - 0.1036 * b ** 4) * olcek
        ust.append((b, yt))
        alt.append((b, -yt))
    return ust + list(reversed(alt))


def kontrol_yuzeyi(ad, x0, x1, mentese=0.78, sapma=0.0, kalinlik=0.05, adim=8):
    """Kanat firar kenarında ayrı, menteşe çizgisi etrafında saptırılmış kontrol yüzeyi"""
    bm = bmesh.new()
    halkalar = []
    for i in range(adim):
        x = x0 + (x1 - x0) * i / (adim - 1)
        y_le, chord, z, tw = kanat_istasyon(x)
        kes = kesit_parcasi(kalinlik, mentese, 1.0)
        h_y = y_le - mentese * chord                   # menteşe noktası
        s = math.radians(sapma)
        halka = []
        for (b, yt) in kes:
            dy = -(b - mentese) * chord                # menteşeden geriye
            dz = yt * chord
            ry = dy * math.cos(s) + dz * math.sin(s)
            rz = -dy * math.sin(s) + dz * math.cos(s)
            halka.append(bm.verts.new((x, h_y + ry, z + rz)))
        halkalar.append(halka)
    n = len(halkalar[0])
    for p, q in zip(halkalar, halkalar[1:]):
        for j in range(n):
            bm.faces.new((p[j], p[(j + 1) % n], q[(j + 1) % n], q[j]))
    bm.faces.new(halkalar[0])
    bm.faces.new(list(reversed(halkalar[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = obje_olustur(ad, bm)
    mirror_ekle(ob)
    bevel_ekle(ob, 0.003, 2)
    subdiv_ekle(ob, 1, 2)
    return ob


def kanat_detaylari(m):
    obs = []
    # Flaperon (iç, hafif aşağı sapmış) ve kanatçık (dış, hafif yukarı)
    obs.append(kontrol_yuzeyi("GK_Flaperon", 1.75, 4.05, 0.76, sapma=6.0))
    obs.append(kontrol_yuzeyi("GK_Kanatcik", 4.15, 6.1, 0.74, sapma=-4.0, kalinlik=0.045))
    # Hücum kenarı flapı: kanadın ön %12'sini kaplayan ince şerit (kalınca, gömülü)
    bm = bmesh.new()
    halkalar = []
    for i in range(10):
        x = 1.9 + (6.4 - 1.9) * i / 9
        y_le, chord, z, tw = kanat_istasyon(x)
        halka = []
        for (b, yt) in naca_kesit(0.058, 18):
            if b > 0.14:
                continue
            halka.append(bm.verts.new((x, y_le - b * chord - 0.003, z + yt * chord * 1.04)))
        halkalar.append(halka)
    n = len(halkalar[0])
    for p, q in zip(halkalar, halkalar[1:]):
        for j in range(n - 1):
            bm.faces.new((p[j], p[j + 1], q[j + 1], q[j]))
    ob = obje_olustur("GK_HucumKenariFlapi", bm)
    sol = ob.modifiers.new("Kalinlik", 'SOLIDIFY')
    sol.thickness = 0.01
    mirror_ekle(ob)
    subdiv_ekle(ob, 1, 2)
    obs.append(ob)
    for o in obs:
        materyal_ata(o, m["boya"])

    # LERX — hava girişi üstünden kanat hücum kenarına yumuşak geçiş
    ist = []
    for i in range(6):
        f = i / 5
        x = 0.95 + 0.85 * f
        y_le = 4.6 - 2.4 * f
        ist.append((x, y_le, 2.6 + 1.3 * f, 0.30 - 0.22 * f, 0))
    lerx = kanat_lofts("GK_LERX", ist, 0.07, 0.06)
    mirror_ekle(lerx)
    subdiv_ekle(lerx, 1, 2)
    materyal_ata(lerx, m["boya"])

    # Silah yuvası kapakları (gövde altı, testere dişli kenarlı stealth paneller)
    bm = bmesh.new()
    for s in (1, -1):
        kutu(bm, (s * 0.38, 0.4, -0.86), (0.7, 4.2, 0.03))
        for k in range(7):     # testere dişleri (ön/arka kenar)
            kutu(bm, (s * (0.1 + k * 0.095), 2.55 - (k % 2) * 0.08, -0.86), (0.08, 0.16, 0.031), Matrix.Rotation(math.radians(45), 4, 'Z'))
    for s in (1, -1):        # yan silah yuvaları
        kutu(bm, (s * 1.95, 1.0, -0.42), (0.04, 2.2, 0.38), Matrix.Rotation(math.radians(-55) * s, 4, 'Y'))
    kap = obje_olustur("GK_SilahYuvasiKapaklari", bm)
    bevel_ekle(kap, 0.006, 2)
    materyal_ata(kap, m["boya"])


# ---------------------------------------------------------------------
# 2) PANEL ÇİZGİLERİ — boyaya prosedürel panel ayrım çizgileri + bump
# ---------------------------------------------------------------------
def panel_cizgileri_ekle():
    mat = bpy.data.materials["GK_Boya_Hayalet"]
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = next(n for n in nt.nodes if n.type == 'TEX_COORD')
    renk = bsdf.inputs["Base Color"].default_value[:]

    def tugla(olcek, konum, harc):
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (olcek, olcek * 0.55, olcek)
        b = nt.nodes.new("ShaderNodeTexBrick")
        b.inputs["Mortar Size"].default_value = harc
        b.inputs["Scale"].default_value = 1.0
        b.offset = 0.5
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], b.inputs["Vector"])
        mp.location, b.location = (konum[0] - 200, konum[1]), konum
        return b

    b1 = tugla(0.3, (-700, -350), 0.006)
    b2 = tugla(0.85, (-700, -600), 0.01)
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = 'MAXIMUM'
    nt.links.new(b1.outputs["Fac"], mx.inputs[0])
    nt.links.new(b2.outputs["Fac"], mx.inputs[1])
    mx.location = (-450, -450)

    # renk: çizgilerde hafif koyulaşma
    karis = nt.nodes.new("ShaderNodeMix")
    karis.data_type = 'RGBA'
    karis.inputs[6].default_value = renk
    karis.inputs[7].default_value = (renk[0] * 0.72, renk[1] * 0.72, renk[2] * 0.72, 1)
    nt.links.new(mx.outputs["Value"], karis.inputs[0])
    nt.links.new(karis.outputs[2], bsdf.inputs["Base Color"])
    karis.location = (-250, -250)

    # bump: çizgiler hafif çukur
    ters = nt.nodes.new("ShaderNodeMath")
    ters.operation = 'SUBTRACT'
    ters.inputs[0].default_value = 1.0
    nt.links.new(mx.outputs["Value"], ters.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.004
    nt.links.new(ters.outputs["Value"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    ters.location, bump.location = (-250, -500), (-80, -500)


# ---------------------------------------------------------------------
# 3) ATMOSFER — uçağın altında hacimli bulut denizi
# ---------------------------------------------------------------------
def bulut_denizi_olustur():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    ob = obje_olustur("GK_BulutDenizi", bm)
    ob.scale = (30000.0, 30000.0, 60.0)   # ufka kadar uzanan bulut denizi
    ob.location = (0.0, -12000.0, -160.0)

    mat = bpy.data.materials.new("GK_Bulut_Hacim")
    if bpy.app.version < (5, 0, 0):
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (1.0, 0.97, 0.94, 1)
    vol.inputs["Anisotropy"].default_value = 0.65
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.0028, 0.0028, 0.016)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 10.0
    noise.inputs["Roughness"].default_value = 0.58
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 0.35
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].position = 0.22
    rampa.color_ramp.elements[1].position = 0.30
    # yükseklik: bulut tabanı yoğun, tepesi kabarık-yumuşak
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ayir = nt.nodes.new("ShaderNodeSeparateXYZ")
    yuk = nt.nodes.new("ShaderNodeMapRange")
    yuk.inputs["From Min"].default_value = -1.0
    yuk.inputs["From Max"].default_value = 1.0
    yuk.inputs["To Min"].default_value = 0.0      # 0 = taban, 1 = tepe
    yuk.inputs["To Max"].default_value = 1.0
    carp = nt.nodes.new("ShaderNodeMath")
    carp.operation = 'MULTIPLY'
    carp.inputs[1].default_value = 0.55
    # kabarık bulut tepeleri: yükseldikçe gürültü eşiği artar -> kubbe şekilli kümeler
    fark = nt.nodes.new("ShaderNodeMath")
    fark.operation = 'SUBTRACT'
    yog = nt.nodes.new("ShaderNodeMath")
    yog.operation = 'MULTIPLY'
    yog.inputs[1].default_value = 0.12
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], fark.inputs[0])
    nt.links.new(carp.outputs["Value"], fark.inputs[1])
    nt.links.new(fark.outputs["Value"], rampa.inputs["Fac"])
    nt.links.new(tc.outputs["Object"], ayir.inputs["Vector"])
    nt.links.new(ayir.outputs["Z"], yuk.inputs["Value"])
    nt.links.new(yuk.outputs["Result"], carp.inputs[0])
    nt.links.new(rampa.outputs["Color"], yog.inputs[0])
    # mesafeyle sönümleme: hacmin kenarı ufukta keskin çizgi oluşturmasın
    duz = nt.nodes.new("ShaderNodeVectorMath")
    duz.operation = 'MULTIPLY'
    duz.inputs[1].default_value = (1.0, 1.0, 0.0)
    uzun = nt.nodes.new("ShaderNodeVectorMath")
    uzun.operation = 'LENGTH'
    son = nt.nodes.new("ShaderNodeMapRange")
    son.inputs["From Min"].default_value = 9000.0
    son.inputs["From Max"].default_value = 30000.0
    son.inputs["To Min"].default_value = 1.0
    son.inputs["To Max"].default_value = 0.0
    sonc = nt.nodes.new("ShaderNodeMath")
    sonc.operation = 'MULTIPLY'
    nt.links.new(geo.outputs["Position"], duz.inputs[0])
    nt.links.new(duz.outputs["Vector"], uzun.inputs[0])
    nt.links.new(uzun.outputs["Value"], son.inputs["Value"])
    nt.links.new(yog.outputs["Value"], sonc.inputs[0])
    nt.links.new(son.outputs["Result"], sonc.inputs[1])
    nt.links.new(sonc.outputs["Value"], vol.inputs["Density"])
    for i, n in enumerate((duz, uzun, son, sonc)):
        n.location = (-700 + i * 160, -420)
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    for i, n in enumerate((geo, mp, noise, rampa, tc, ayir, yuk, carp, yog, vol, out)):
        n.location = (-1400 + i * 140, (i % 2) * 180)
    ob.data.materials.append(mat)
    return ob


def sahne_ayarlari():
    sc = bpy.context.scene
    sc.cycles.volume_step_rate = 3.0
    sc.cycles.volume_max_steps = 256
    sc.cycles.volume_bounces = 1
    # Kamera: biraz yukarıdan, ufuktaki gün batımını ve bulut denizini görecek şekilde
    cam = bpy.data.objects.get("GK_Kamera")
    if cam:
        cam.location = (-27.0, 29.0, 6.5)
        cam.data.lens = 55
        cam.data.dof.aperture_fstop = 16.0     # bulutlar da net kalsın
    # Uçuş halinde iniş takımı kapalı
    for ob in bpy.data.objects:
        if ob.name.startswith(("GK_Takim", "GK_Lastik", "GK_Jant")):
            ob.hide_render = not INIS_TAKIMI_ACIK
            ob.hide_viewport = not INIS_TAKIMI_ACIK


# ---------------------------------------------------------------------
# ÇALIŞTIR
# ---------------------------------------------------------------------
def main():
    m = {"boya": bpy.data.materials["GK_Boya_Hayalet"]}
    kanat_detaylari(m)
    panel_cizgileri_ekle()
    bulut_denizi_olustur()
    sahne_ayarlari()
    print("GÖK KARTALI — Adım 3 tamam: kontrol yüzeyleri, LERX, silah kapakları, panel çizgileri, bulut denizi.")


main()
