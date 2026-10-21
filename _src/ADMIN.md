# Yönetim paneli

Panel: **https://epsilonpublishinggroup.com/admin/** ([Sveltia CMS](https://sveltiacms.app), arayüz Türkçe).

## Nasıl çalışır

1. Editör panelde bir kitabı, yazarı, ana sayfa vitrinini ya da site ayarlarını kaydeder.
2. Panel, değişikliği `_src/content/` altındaki JSON dosyasına yazar ve `main`'e commit eder.
3. **Build site from content** workflow'u (`.github/workflows/build-site.yml`) sayfaları
   yeniden üretir, commit eder ve GitHub Pages yayınını tetikler. Toplam 1–2 dakika sürer.

Pages kaynağı (`main` / root) ve `CNAME` değişmez. Derleme hata verirse (örneğin
eksik bir alan) workflow kırmızı olur ve yayındaki site olduğu gibi kalır.

Panelde yönetilenler: **Kitaplar** (ekle / düzenle / sil / sürükleyerek sırala, kapak
yükleme), **Yazarlar**, **Haberler**, **Fuarlar & Etkinlikler**, **Yayınevleri**, **Hizmetler**,
**Sayfa metinleri** (Ana sayfa, Hakkımızda, İletişim ve liste sayfalarının başlık/metin/görselleri),
**Ana sayfa vitrinleri**, **Site ayarları**, **Rakamlar** ("The group in numbers") ve
**İletişim bilgileri**, **Kataloglar** (PDF yükleme; okuyucu sayfaları ve kapak otomatik üretilir).

Yeni bir katalog PDF'i yüklendiğinde workflow, PDF'in her sayfasını okuyucu için görsele
çevirir (PyMuPDF). Büyük kataloglarda bu birkaç dakika sürebilir; o sırada sitede eski
hali görünmeye devam eder.

İletişim formu FormSubmit ile pelin@epsilonyayingrubu.com adresine gider; bu adres panelden
değişmez (değişirse FormSubmit'te yeniden doğrulama gerekir).

Kitap sayıları (yayınevi kartları, yazarlar listesi, Representations) her derlemede
kitaplardan hesaplanır; elle güncellenmez.

Fuarlar bitiş tarihlerine göre "Upcoming" ya da "Past" görünür; workflow her sabah da
çalıştığı için bir etkinlik bittiğinde ertesi sabah kendiliğinden "Past"a geçer.

## Blog

**Blog** bölümünden yazı eklenir: başlık, tarih, yazar, etiketler, özet, kapak, metin
(ara başlık, liste, link) ve **Yazıda geçen kitaplar**. Seçilen kitaplar yazının altında kart
olarak listelenir ve kitap sayfalarına iç link verir. "Vitrine sabitle" ile önemli yazılar
yeni yazıların önünde kalır. İlk yazı yayınlanınca menüde ve alt bilgide "Blog" linki,
`/blog/feed.xml` RSS beslemesi ve sitemap kayıtları kendiliğinden oluşur.

## SEO

Her kitap, yazar, haber, etkinlik, yayınevi, hizmet, katalog ve sayfa metninin sonunda
**SEO başlığı** ve **SEO açıklaması** alanları vardır. Boş bırakılırsa içerikten otomatik
üretilir (açıklama metnin ilk ~155 karakteri). Paylaşım görseli olarak kapak, haber/etkinlik
görseli ya da Site ayarlarındaki varsayılan görsel kullanılır.

Liste sayfalarının (Kitaplar, Yazarlar, Yayınevleri, Haberler, Fuarlar, Kataloglar,
Representations, Hizmetler, Blog) **Sayfa metinleri** girdisinde ayrıca **SEO metni** alanı
vardır: sayfanın altında görünen, ara başlık ve link içerebilen tanıtım metni. Yazarlara
**fotoğraf**, kitaplara **ISBN** eklenebilir; ikisi de Google'ın verisine de yansır. `sitemap.xml`, `robots.txt`
(yapay zeka tarayıcıları dahil herkese açık, `/admin/` hariç) ve `llms.txt` her derlemede
güncellenir.

## Kimler girebilir

Repoya **Write** yetkisi olan GitHub hesapları. Yeni bir editör için:
repo → Settings → Collaborators → Add people → rol: Write. Yetkisi olmayan biri
paneli açsa bile hiçbir şeyi okuyamaz ya da değiştiremez. Editörlerin GitHub
hesaplarında iki adımlı doğrulamanın açık olması önerilir.

## Panele giriş: erişim token'ı

Panele **"Erişim Token'ı Kullanarak Giriş Yap"** ile girilir. Token, GitHub'ın sizin adınıza
verdiği bir erişim anahtarıdır; her kullanıcı kendi token'ını bir kez oluşturur ve panele
yapıştırır. Ek bir sunucu ya da Cloudflare kurulumu gerekmez.

**Repo sahibi (Rıza) için: fine-grained token**
GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** →
Generate new token
- Repository access: **Only select repositories** → `epsilon_right`
- Permissions → Repository permissions → **Contents: Read and write** (Metadata: Read-only otomatik gelir)
- Expiration: örn. 90 gün

**Repoda collaborator olanlar için: classic token**
Fine-grained token'lar başkasının kişisel reposunu seçemediği için:
GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)** →
Generate new token (classic)
- Scope: **repo**
- Expiration: örn. 90 gün

Token yalnızca bir kez gösterilir; kopyalayıp panele yapıştırın. Panel token'ı yalnızca o
tarayıcıda saklar; ortak bilgisayarlarda çıkış yapın. Süresi dolunca yeni token oluşturup
tekrar girin. Token'ı kimseyle paylaşmayın; kaybolursa GitHub'dan iptal edin (Revoke).

Teknik olmayan editörler eklenirse tek tıkla "GitHub ile Giriş" kurulabilir: Sveltia CMS
Authenticator (ücretsiz Cloudflare Worker) + GitHub OAuth App; ardından `admin/config.yml`'de
`base_url` eklenir ve `auth_methods` `[oauth, token]` yapılır.

## Bilgisayarda önizleme (canlıya dokunmadan)

```bash
python3 _src/serve.py
```

- Site: http://127.0.0.1:8765/
- Panel: http://127.0.0.1:8765/admin/ → **Yerel Repo ile Çalış** → `epsilon_right` klasörünü seçin.

Bu modda panel dosyaları doğrudan bu klasöre yazar, sunucu sayfaları kendiliğinden
yeniden üretir; sayfayı yenilemek yeterlidir. Hiçbir şey commit edilmez ya da gönderilmez.
Chrome veya Edge gerekir. Yüklenen kapaklardan küçük boyutlar yalnızca Pillow kuruluysa
yerelde üretilir; değilse önizlemede orijinal görsel kullanılır (yayında her zaman üretilir).

## Panel sürümünü yükseltme

`admin/index.html` Sveltia CMS'i sabit bir sürümle ve bütünlük (SRI) karmasıyla yükler.
Yükseltirken ikisini birlikte değiştirin:

```bash
curl -sL https://unpkg.com/@sveltia/cms@<sürüm>/dist/sveltia-cms.js | openssl dgst -sha384 -binary | openssl base64 -A
```

## Dikkat: eski workflow'lar artık kullanılmamalı

`Optimize website assets`, `Publish catalogue readers` ve `Import verified YA catalogue`
workflow'larının işleri (kapak optimizasyonu, katalog okuyucuları) artık **Build site from
content** içinde yapılıyor. Eski üçü üretilmiş HTML'i doğrudan düzenlediği için çalıştırılırsa
bir sonraki derleme değişikliklerini geri alır; birleştirme sırasında kaldırılmaları önerilir.
