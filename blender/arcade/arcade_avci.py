# =====================================================================
#  GÖK KARTALI 3D — Arcade Low-Poly Avcı Uçağı (oyun motoruna hazır)
#
#  • Hiyerarşi: Arcade_Plane_Root (Empty) altında
#      Body (gövde + kanatlar + kuyruk sabit kısımları + kokpit çerçevesi)
#      Canopy (yarı saydam mavi kokpit camı), Pilot_Head (kask + gözlük)
#      Propeller (pervane + göbek)      -> pivot: göbek merkezi, dönme ekseni Y
#      Aileron_L / Aileron_R            -> pivot: menteşe çizgisi, dönme ekseni X
#      Rudder                           -> pivot: menteşe çizgisi, dönme ekseni Z
#  • Burun +Y yönünde, kanat açıklığı 4.5 m, düz gölgelendirme (Shade Flat)
#  • Tüm rotasyon/ölçek değerleri uygulanmış (0 ve 1). Hareketli parçaların
#    konumu (location) bilinçli olarak pivot noktasıdır.
#  Uyumluluk: Blender 4.0+ / 5.x
# =====================================================================
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

GLB_KAYDET = True    # True: betik klasörüne arcade_avci.glb dışa aktarır


# ---------------------------------------------------------------------
# 0) SAHNE TEMİZLİĞİ (varsayılan küp, kamera, ışık dahil her şey)
# ---------------------------------------------------------------------
def sahneyi_temizle():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for grup in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.images):
        for blok in list(grup):
            if blok.users == 0:
                grup.remove(blok)


# ---------------------------------------------------------------------
# 1) MATERYALLER — parlak arcade renkleri
# ---------------------------------------------------------------------
def mat(ad, renk, rough=0.35, metal=0.0, alfa=1.0, emis=None):
    m = bpy.data.materials.new(ad)
    if bpy.app.version < (5, 0, 0):
        m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*renk, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if alfa < 1.0:
        b.inputs["Alpha"].default_value = alfa
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = 'BLENDED'
        elif hasattr(m, "blend_method"):
            m.blend_method = 'BLEND'
    if emis:
        for ad_ in ("Emission Color", "Emission"):
            if ad_ in b.inputs:
                b.inputs[ad_].default_value = (*emis, 1.0)
                break
        b.inputs["Emission Strength"].default_value = 1.5
    m.diffuse_color = (*renk, alfa)     # viewport rengi
    return m


def materyaller():
    return {
        "kirmizi": mat("Arcade_Kirmizi", (0.80, 0.04, 0.03), 0.32),
        "beyaz": mat("Arcade_Beyaz", (0.92, 0.92, 0.90), 0.35),
        "koyu": mat("Arcade_KoyuGri", (0.07, 0.075, 0.085), 0.45, 0.6),
        "cam": mat("Arcade_Cam_Mavi", (0.15, 0.62, 1.0), 0.05, 0.1, alfa=0.45),
        "sari": mat("Arcade_Sari", (1.0, 0.72, 0.05), 0.35),
        "deri": mat("Arcade_Ten", (0.88, 0.62, 0.45), 0.6),
        "lens": mat("Arcade_Gozluk", (0.05, 0.35, 0.9), 0.05, 0.3, emis=(0.05, 0.35, 0.9)),
    }


# ---------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------
def obje(ad, bm, malzemeler, pivot=(0, 0, 0), kok=None):
    """bmesh'i pivot noktasına göre ötelenmiş obje yapar (origin = pivot)."""
    bmesh.ops.translate(bm, vec=-Vector(pivot), verts=bm.verts[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(ad)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False                 # Shade Flat
    for m in malzemeler:
        me.materials.append(m)
    ob = bpy.data.objects.new(ad, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pivot
    if kok:
        ob.parent = kok
    return ob


def halka_loft(bm, istasyonlar, sekil, mat_fn=None):
    """istasyonlar: [(y, yarı_gen, yarı_yuk, z)]; sekil: birim kesit noktaları [(x,z)]"""
    halkalar = []
    for (y, w, h, z) in istasyonlar:
        halkalar.append([bm.verts.new((px * w, y, z + pz * h)) for (px, pz) in sekil])
    n = len(sekil)
    for i, (p, q) in enumerate(zip(halkalar, halkalar[1:])):
        for j in range(n):
            f = bm.faces.new((p[j], p[(j + 1) % n], q[(j + 1) % n], q[j]))
            if mat_fn:
                f.material_index = mat_fn(i, j)
    return halkalar


SEKIZGEN = [(math.cos(math.radians(22.5 + 45 * k)), math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]


def kanat_kesiti(x, y_le, chord, z, kal):
    """Altıgen low-poly kanat kesiti (hücum kenarı -> firar kenarı)"""
    t = chord * kal
    return [(x, y_le, z), (x, y_le - chord * 0.22, z + t * 0.55), (x, y_le - chord * 0.65, z + t * 0.35),
            (x, y_le - chord, z), (x, y_le - chord * 0.65, z - t * 0.25), (x, y_le - chord * 0.22, z - t * 0.4)]


def kesit_loft(bm, kesitler, mat_fn=None, kapak_bas=True, kapak_son=True):
    halkalar = [[bm.verts.new(p) for p in k] for k in kesitler]
    n = len(halkalar[0])
    for i, (p, q) in enumerate(zip(halkalar, halkalar[1:])):
        for j in range(n):
            f = bm.faces.new((p[j], p[(j + 1) % n], q[(j + 1) % n], q[j]))
            if mat_fn:
                f.material_index = mat_fn(i, j)
    if kapak_bas:
        bm.faces.new(halkalar[0])
    if kapak_son:
        f = bm.faces.new(halkalar[-1])
        if mat_fn:
            f.material_index = mat_fn(len(halkalar) - 1, 0)
    return halkalar


# ---------------------------------------------------------------------
# 2) GÖVDE (Body) — sekizgen kesitli gövde + kanatlar + kuyruk + şeritler
# ---------------------------------------------------------------------
KANAT_Z = -0.14
TE_Y = -0.55                 # düz firar kenarı -> kanatçık menteşesi X eksenine paralel
MENTESE_Y = TE_Y + 0.30
KANATCIK_X0, KANATCIK_X1 = 1.12, 2.22
DUMEN_Y = -1.72


def govde_olustur(M, kok):
    bm = bmesh.new()
    # malzeme indeksleri: 0 kırmızı, 1 beyaz, 2 koyu, 3 sarı
    ist = [(1.95, 0.30, 0.30, 0.00), (1.62, 0.37, 0.37, 0.02), (0.95, 0.42, 0.43, 0.05),
           (0.25, 0.40, 0.42, 0.07), (-0.55, 0.32, 0.34, 0.09), (-0.85, 0.29, 0.31, 0.10),
           (-1.05, 0.27, 0.29, 0.11), (-1.55, 0.17, 0.20, 0.14), (-2.0, 0.07, 0.09, 0.18)]

    def gmat(i, j):
        if i == 0:
            return 3                         # motor kaportası ön bandı: sarı
        if i == 5:
            return 1                         # gövde beyaz şeridi
        return 0
    halkalar = halka_loft(bm, ist, SEKIZGEN, gmat)
    on = bm.faces.new(list(reversed(halkalar[0])))
    on.material_index = 2                    # motor ön yüzü koyu
    bm.faces.new(halkalar[-1])
    # egzoz boruları
    for s in (1, -1):
        for k in range(3):
            r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.045, radius2=0.045, depth=0.16,
                                      matrix=Matrix.Translation((s * 0.42, 1.35 - k * 0.17, 0.08)) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
            for f in {f for v in r['verts'] for f in v.link_faces}:
                f.material_index = 2

    # Ana kanat (iki yan). Dış bölümde firar kenarı kanatçık için kesik.
    for s in (1, -1):
        def k(x, kesik=False):
            y_le = 0.78 - (x / 2.25) * 0.55
            chord = (y_le - (MENTESE_Y if kesik else TE_Y))
            kal = 0.13 - 0.05 * (x / 2.25)
            return [(s * px, py, pz) for (px, py, pz) in kanat_kesiti(x, y_le, chord, KANAT_Z, kal)]
        kesitler = [k(0.0), k(KANATCIK_X0 - 0.02), k(KANATCIK_X0 - 0.02, True), k(1.95, True), k(2.25, True)]
        kesit_loft(bm, kesitler, lambda i, j: 1 if i >= 3 else 0)       # kanat ucu beyaz şerit
    # Yatay stabilizatör
    for s in (1, -1):
        def ks(x):
            y_le = -1.32 - (x / 0.95) * 0.18
            return [(s * px, py, pz) for (px, py, pz) in kanat_kesiti(x, y_le, (y_le + 1.98) * 0.95, 0.12, 0.10)]
        kesit_loft(bm, [ks(0.0), ks(0.8), ks(0.95)], lambda i, j: 1 if i == 1 else 0)
    # Dikey kuyruk (sabit kısım, dümen menteşesine kadar)
    def kd(z):
        f = (z - 0.15) / 0.8
        y_le = -1.25 - f * 0.32
        ch = y_le - DUMEN_Y
        t = ch * 0.12
        return [(0, y_le, z), (t * 0.5, y_le - ch * 0.3, z), (t * 0.4, DUMEN_Y, z), (-t * 0.4, DUMEN_Y, z), (-t * 0.5, y_le - ch * 0.3, z)]
    kesit_loft(bm, [kd(0.15), kd(0.95)], lambda i, j: 0)
    # Kokpit çerçevesi (koyu)
    bmesh.ops.create_cone(bm, cap_ends=False, segments=8, radius1=0.33, radius2=0.33, depth=0.05,
                          matrix=Matrix.Translation((0, 0.42, 0.42)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Diagonal((1, 0.75, 1, 1)))
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(c.y - 0.42) < 0.04 and c.z > 0.3 and len(f.verts) == 4 and abs(c.x) < 0.36:
            f.material_index = 2
    return obje("Body", bm, [M["kirmizi"], M["beyaz"], M["koyu"], M["sari"]], (0, 0, 0), kok)


# ---------------------------------------------------------------------
# 3) KOKPİT CAMI + PİLOT KAFASI
# ---------------------------------------------------------------------
def kanopi_olustur(M, kok):
    bm = bmesh.new()
    # yarım sekizgen kubbe, öne-arkaya uzatılmış
    ist = [(0.42, 0.26, 0.05, 0.36), (0.25, 0.27, 0.22, 0.36), (-0.15, 0.26, 0.26, 0.36), (-0.55, 0.18, 0.12, 0.38), (-0.75, 0.10, 0.03, 0.40)]
    yarim = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in (0, 30, 60, 90, 120, 150, 180)]
    h = [[bm.verts.new((px * w, y, z + pz * hh)) for (px, pz) in yarim] for (y, w, hh, z) in ist]
    for p, q in zip(h, h[1:]):
        for j in range(len(yarim) - 1):
            bm.faces.new((p[j], p[j + 1], q[j + 1], q[j]))
    bm.faces.new(h[0])
    bm.faces.new(list(reversed(h[-1])))
    return obje("Canopy", bm, [M["cam"]], (0, 0, 0), kok)


def pilot_kafasi_olustur(M, kok):
    bm = bmesh.new()
    merkez = Vector((0, 0.02, 0.50))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.15, matrix=Matrix.Translation(merkez))          # kask
    for f in bm.faces:
        if f.calc_center_median().z < merkez.z - 0.06:
            f.material_index = 3                                           # alt kısım: ten (yüz/boyun)
        elif abs(f.calc_center_median().x) < 0.045:
            f.material_index = 1                                           # kask ortası kırmızı şerit
    for s in (1, -1):                                                      # gözlükler
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.05, radius2=0.05, depth=0.05,
                              matrix=Matrix.Translation(merkez + Vector((s * 0.06, 0.13, 0.01))) @ Matrix.Rotation(math.radians(90), 4, 'X'))
    for f in bm.faces:
        c = f.calc_center_median()
        if c.y > merkez.y + 0.125:
            f.material_index = 2                                           # gözlük camı
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(merkez + Vector((0, 0.07, 0.02))) @ Matrix.Diagonal((0.3, 0.12, 0.025, 1)))
    return obje("Pilot_Head", bm, [M["beyaz"], M["kirmizi"], M["lens"], M["deri"]], (0, 0, 0), kok)


# ---------------------------------------------------------------------
# 4) HAREKETLİ PARÇALAR — pivotları dönme eksenlerinde
# ---------------------------------------------------------------------
def pervane_olustur(M, kok):
    pivot = (0.0, 2.05, 0.0)                  # göbek merkezi; dönme ekseni = Y (burun yönü)
    bm = bmesh.new()
    # göbek konisi (beyaz)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.17, radius2=0.0, depth=0.36,
                          matrix=Matrix.Translation((0, 2.13, 0)) @ Matrix.Rotation(math.radians(-90), 4, 'X'))
    for f in bm.faces:
        f.material_index = 1
    # 3 pala (koyu gri, uçları sarı), hafif burulmuş
    for k in range(3):
        a = math.radians(90 + 120 * k)
        yon = Vector((math.cos(a), 0, math.sin(a)))
        dik = Vector((-math.sin(a), 0, math.cos(a)))
        kes = []
        for (r, gen, burul) in ((0.08, 0.09, 30), (0.45, 0.13, 18), (0.78, 0.07, 10)):
            b = math.radians(burul)
            on = Vector((0, 1, 0)) * (gen * math.sin(b)) + dik * (gen * math.cos(b))
            kes.append([Vector(pivot) + yon * r + on, Vector(pivot) + yon * r + on * -1 + Vector((0, 0.02, 0)),
                        Vector(pivot) + yon * r - on, Vector(pivot) + yon * r + on * 0 - Vector((0, 0.02, 0))])
        halk = [[bm.verts.new(p) for p in s] for s in kes]
        for i, (p, q) in enumerate(zip(halk, halk[1:])):
            for j in range(4):
                f = bm.faces.new((p[j], p[(j + 1) % 4], q[(j + 1) % 4], q[j]))
                f.material_index = 2 if i == 1 else 0
        bm.faces.new(halk[-1]).material_index = 2
    return obje("Propeller", bm, [M["koyu"], M["beyaz"], M["sari"]], pivot, kok)


def kanatcik_olustur(M, kok, s):
    ad = "Aileron_R" if s > 0 else "Aileron_L"
    x_orta = s * (KANATCIK_X0 + KANATCIK_X1) / 2
    pivot = (x_orta, MENTESE_Y, KANAT_Z)     # menteşe çizgisi X eksenine paralel -> yerel X ile döndür
    bm = bmesh.new()
    kes = []
    for x in (KANATCIK_X0, KANATCIK_X1):
        kal = 0.13 - 0.05 * (x / 2.25)
        y_le = 0.78 - (x / 2.25) * 0.55
        t = (y_le - TE_Y) * kal * 0.42
        kes.append([(s * x, MENTESE_Y, KANAT_Z + t * 0.55), (s * x, TE_Y, KANAT_Z), (s * x, MENTESE_Y, KANAT_Z - t * 0.4)])
    kesit_loft(bm, kes, lambda i, j: 0)
    return obje(ad, bm, [M["beyaz"]], pivot, kok)


def dumen_olustur(M, kok):
    pivot = (0.0, DUMEN_Y, 0.55)             # menteşe dikey -> yerel Z ile döndür
    bm = bmesh.new()
    kes = []
    for z in (0.17, 0.93):
        t = 0.035
        kes.append([(t, DUMEN_Y, z), (0.0, DUMEN_Y - 0.32, z), (-t, DUMEN_Y, z)])
    kesit_loft(bm, kes, lambda i, j: 0)
    return obje("Rudder", bm, [M["beyaz"]], pivot, kok)


# ---------------------------------------------------------------------
# 5) DÖNÜŞÜMLERİ UYGULA + DIŞA AKTAR
# ---------------------------------------------------------------------
def donusumleri_uygula(obs):
    """Rotasyon ve ölçeği uygula (0 / 1). Konum = pivot olarak kalır."""
    for ob in obs:
        if ob.type != 'MESH':
            continue
        M_rs = ob.matrix_basis.to_3x3().to_4x4()
        ob.data.transform(M_rs)
        ob.rotation_euler = (0, 0, 0)
        ob.scale = (1, 1, 1)


def glb_kaydet():
    try:
        klasor = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        klasor = bpy.path.abspath("//") or os.path.expanduser("~")
    yol = os.path.join(klasor, "arcade_avci.glb")
    try:
        bpy.ops.export_scene.gltf(filepath=yol, export_format='GLB', export_yup=True, export_apply=True)
        print("GLB kaydedildi:", yol)
    except Exception as e:      # eklenti kapalıysa betik yine de tamamlanır
        print("GLB dışa aktarılamadı:", e)


def main():
    sahneyi_temizle()
    M = materyaller()
    kok = bpy.data.objects.new("Arcade_Plane_Root", None)
    kok.empty_display_type = 'ARROWS'
    kok.empty_display_size = 1.0
    bpy.context.scene.collection.objects.link(kok)

    obs = [govde_olustur(M, kok), kanopi_olustur(M, kok), pilot_kafasi_olustur(M, kok),
           pervane_olustur(M, kok), kanatcik_olustur(M, kok, -1), kanatcik_olustur(M, kok, 1), dumen_olustur(M, kok)]
    donusumleri_uygula(obs)
    tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs)
    print("Arcade avcı hazır — üçgen sayısı:", tri)
    if GLB_KAYDET:
        glb_kaydet()


main()
