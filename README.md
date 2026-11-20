# Gök Kartalı 3D

Dikey ilerlemeli, 3D grafikli arcade uçak oyunu. Tek dosya: `index.html`. Kurulum yok, derleme yok.

## GitHub Pages ile yayınlama
1. Bu klasördeki dosyaları (`index.html`, `README.md`) bir GitHub deposuna yükleyin.
2. Depoda **Settings → Pages** bölümüne gidin.
3. **Source: Deploy from a branch**, Branch: `main`, klasör: `/ (root)` seçip kaydedin.
4. Birkaç dakika sonra oyun `https://KULLANICI-ADI.github.io/DEPO-ADI/` adresinde açılır.

## Kontroller
- **PC:** W A S D / Oklar ile uç · Space: Özel Bomba · E: Yardımcı Silah · F: Otomatik ateşi aç/kapa · J / Z / Fare: Ateş · P / Esc: Menü
- **Tablet:** Parmağınızı sürükleyerek uçun · Ekrandaki BOMBA ve YARDIMCI butonları

## Çok oyunculu (PC + Tablet)
İki cihazda oyunu açın. Biri **Çok Oyunculu → Oda Kur** der, diğeri **Odaya Katıl** deyip 4 haneli kodu girer.
Bağlantı PeerJS (WebRTC) ile doğrudan kurulur, iki cihazda da internet gerekir.

## Test modu
Ayarlar (⚙️) penceresinin en altındaki **"Gök Kartalı 3D · v1.0"** yazısına 5 kez dokunun.
**+10 Level & +5000 Altın/Elmas** butonu açılır.

İlerleme tarayıcının `localStorage` hafızasına otomatik kaydedilir.

## 3D model kredileri
Hazır modeller [Poly Pizza](https://poly.pizza) üzerinden alınmış, Blender ile yön/ölçek normalleştirilmiştir (`blender/modelleri_normalle.py`).

| Oyundaki rol | Model | Yazar | Lisans |
|---|---|---|---|
| P-40 Sparrow | Aeroplane | Gilang Romadhan | CC-BY |
| F-16 Falcon | Jet | Poly by Google | CC-BY |
| A-10 Warthog | Jet | Poly by Google | CC-BY |
| F-22 Raptor | Jet | jeremy | CC-BY |
| X-99 Valkyrie | Low poly Fighter | Stephen Graybill | CC0 |
| Düşman avcı | Airplane | Poly by Google | CC0 |
| Düşman jet | Spaceship | Liz Reddington | CC-BY |
| Bombardıman | Spaceship | Quaternius | CC0 |
| Helikopter | Helicopter | kazuma | CC0 |
| Tank | Tank | Quaternius | CC0 |
| Boss | Spaceship | Quaternius | CC0 |
| Pilot | Astronaut | PW Wu | CC-BY |
| Füze | Missile | Jarlan Perez | CC-BY |
| Bomba | Bomb | Quaternius | CC0 |
