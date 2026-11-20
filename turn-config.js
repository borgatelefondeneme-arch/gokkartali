// =====================================================================
//  ÇOK OYUNCULU — FARKLI AĞLAR (farklı Wi-Fi / mobil veri) İÇİN TURN AYARI
//
//  Aynı Wi-Fi'deki cihazlar bu ayar olmadan da bağlanır. Farklı ağlardaki
//  cihazların bağlanabilmesi için bir TURN aktarma sunucusu gerekir.
//
//  Metered panelinde: TURN Server → Credentials → "gok-kartali-oyun"
//  kimliğinin USERNAME ve PASSWORD değerlerini aşağıdaki iki alana yapıştır.
//  (Panelde her birinin yanında kopyalama butonu var; şifre için önce REVEAL.)
//  Not: Bu bilgiler oyun sayfasında herkese görünür; ücretsiz kotanı
//  panelden takip edebilirsin, gerekirse kimliği silip yenisini oluştur.
// =====================================================================
window.GK_TURN = {
  turnKullanici: "66fd6f62f11843e114ae47ec",   // Metered → Credentials → USERNAME
  turnSifre: "T0Mh0arQVoj/Mq8C",       // Metered → Credentials → PASSWORD
  turnSunucu: "standard.relay.metered.ca",

  // İsteğe bağlı (gelişmiş): Metered TURN API anahtarı ile otomatik kimlik alma
  meteredUygulama: "",
  meteredApiKey: "",
  // Başka TURN sunucuların varsa: { urls: "turn:adres:3478", username: "...", credential: "..." }
  sunucular: []
};
