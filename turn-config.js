// =====================================================================
//  ÇOK OYUNCULU — FARKLI AĞLAR (farklı Wi-Fi / mobil veri) İÇİN TURN AYARI
//
//  Aynı Wi-Fi'deki cihazlar bu ayar olmadan da bağlanır. Farklı ağlardaki
//  cihazların (ör. biri evde Wi-Fi, diğeri mobil veride) bağlanabilmesi için
//  bir TURN aktarma sunucusu gerekir.
//
//  Ücretsiz kurulum (ayda 20 GB, bu oyun için fazlasıyla yeter):
//    1) https://www.metered.ca/tools/openrelay/ adresinden ücretsiz hesap aç.
//    2) Panelde uygulama adını (ör. "gokkartali" -> gokkartali.metered.live)
//       ve "TURN Server" bölümündeki API Key'i al.
//    3) Bu dosyada aşağıdaki iki alanı doldurup GitHub'a kaydet.
//  Not: Bu anahtar oyun sayfasında herkese görünür; Metered bu anahtarı
//  tarayıcıda kullanılmak üzere verir. Kotanı panelden takip edebilirsin.
// =====================================================================
window.GK_TURN = {
  meteredUygulama: "gokkartali",   // örnek: "gokkartali"
  meteredApiKey: "4RowkkgvA8njt4xTyeMSMf_TNXF0m8sKjIFv4FN_0btcJRof",     // Metered panelindeki API Key
  // Kendi TURN sunucun varsa buraya da ekleyebilirsin:
  // { urls: "turn:sunucu.adresi:3478", username: "kullanici", credential: "sifre" }
  sunucular: []
};
