# Poly Pizza'dan indirilen GLB modelleri oyuna uygun hale getirir:
# burun +Y (glTF'te -Z), merkezleme, hedef boyuta ölçekleme. Çıktı: models/<ad>.glb
# Kullanım: blender -b --factory-startup --python modelleri_normalle.py
import bpy, os, math
from mathutils import Vector, Matrix

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAYNAK = os.path.join(KOK, "models", "kaynak")
HEDEF = os.path.join(KOK, "models")

# ad: (burun yönü, hedef en büyük yatay boyut veya yükseklik, yerleşim)
AYAR = {
    "oyuncu_p40": ("-Y", 6.0, "merkez"), "oyuncu_f16": ("-Y", 6.4, "merkez"), "oyuncu_a10": ("-Y", 6.8, "merkez"),
    "oyuncu_f22": ("-Y", 6.6, "merkez"), "oyuncu_x99": ("-Y", 6.8, "merkez"),
    "dusman_avci": ("+X", 4.0, "merkez"), "dusman_jet": ("-Y", 4.2, "merkez"), "dusman_bombardiman": ("-Y", 9.5, "merkez"),
    "dusman_helikopter": ("-Y", 5.6, "merkez"), "dusman_tank": ("-X", 3.6, "taban"),
    "boss": ("-Y", 17.0, "merkez"), "fuze": ("+Z", 1.2, "merkez"), "bomba": ("-Y", 1.0, "merkez"),
    "pilot": ("-Y_ayakta", 3.0, "taban"),
}
DONDUR = {"-Y": Matrix.Rotation(math.pi, 4, 'Z'), "+X": Matrix.Rotation(math.pi / 2, 4, 'Z'),
          "-X": Matrix.Rotation(-math.pi / 2, 4, 'Z'), "+Z": Matrix.Rotation(-math.pi / 2, 4, 'X'),
          "-Y_ayakta": Matrix.Identity(4)}   # pilot: yüzü zaten kameraya (-Y) dönük kalsın


def temizle():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for grup in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.actions):
        for b in list(grup):
            if b.users == 0:
                grup.remove(b)


def isle(ad):
    yon, boyut, yer = AYAR[ad]
    temizle()
    bpy.ops.import_scene.gltf(filepath=os.path.join(KAYNAK, ad + ".glb"))
    ustler = [o for o in bpy.data.objects if o.parent is None]
    kok = bpy.data.objects.new(ad, None)
    bpy.context.scene.collection.objects.link(kok)
    for o in ustler:
        o.parent = kok
    kok.matrix_world = DONDUR[yon]
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in bpy.data.objects if o.type == 'MESH' for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    d = mx - mn
    olcek = boyut / (d.z if yer == "taban" and ad == "pilot" else max(d.x, d.y))
    merkez = (mn + mx) / 2
    z0 = mn.z if yer == "taban" else merkez.z
    kok.matrix_world = Matrix.Scale(olcek, 4) @ Matrix.Translation(Vector((-merkez.x, -merkez.y, -z0))) @ DONDUR[yon]
    bpy.context.view_layer.update()
    yol = os.path.join(HEDEF, ad + ".glb")
    bpy.ops.export_scene.gltf(filepath=yol, export_format='GLB', export_yup=True, export_apply=True, export_animations=False)
    print("NORMAL", ad, "olcek", round(olcek, 4), "boyut", tuple(round(v * olcek, 2) for v in d), "->", os.path.getsize(yol) // 1024, "KB")


for ad in AYAR:
    isle(ad)
print("TAMAM")
