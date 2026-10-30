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

Ana sayfanın üstündeki kart sırayla şunu gösterir: "Ana sayfada sabitle" açık bir etkinlik;
yoksa haberler sırasındaki ilk haber (küçük görseliyle), ama sabitli değilse ve ondan sonra
biten bir fuar varsa o fuar. Sabitli bir haber, yeni haberler girilse de kartta kalır.

Fuarlar bitiş tarihlerine göre "Upcoming" ya da "Past" görünür; workflow her sabah da
çalıştığı için bir etkinlik bittiğinde ertesi sabah kendiliğinden "Past"a geçer.

## İngilizce örnekler

Kitabın düzenleme ekranındaki **İngilizce örnek** alanına bir önizleme PDF'i yüklenince
kitap sayfasında **Read an English Sample** düğmesi çıkar; örnek, katalog gibi sayfa
çevirmeli okuyucuda açılır. PDF'in kendisi sitede yayınlanmaz (`_src/samples/` altında
durur), ziyaretçi yalnızca sayfa görsellerini görür ve indirme düğmesi yoktur.

Yüklenecek PDF kitabın tamamı değil, yalnızca gösterilecek kısımdır: 1. sayfa ön kapak
(ya da arka kapak + sırt + ön kapak tek parça), ardından kitabın ilk sayfaları; kural
olarak sayfa sayısının yaklaşık dörtte biri (32 sayfalık kitapta 8). Çift sayfa (yan yana
iki sayfa) olarak kaydedilmiş PDF'ler otomatik ikiye bölünür. Seri sayfalarında her kitap
için ayrı satır eklenir ve **Başlık** yazılır (düğmede görünür).

Baskı dosyalarından (iç sayfalar + kapak PDF'i) bu önizlemeyi üretmek için:
`python3 _src/tools/make_sample_preview.py İÇ.pdf KAPAK.pdf ÇIKTI.pdf` (PyMuPDF ve
Pillow gerekir). Kesim payları ve baskı işaretleri kırpılır, sayfalar web boyutuna
indirilir; sonuç birkaç MB olur.

## Set / seri sayfaları

Bir sayfada birden çok kitap gösteriliyorsa (örneğin 8'li hayvan serisi) kitabın düzenleme
ekranında **Set / seri sayfası** açılır. Başlık küçük yazılır ve kapak alanı kaydırmalı olur.
İngilizce örneği olan kitapların kapağı otomatik gelir; örneği olmayanların kapağı **Setin
diğer kapakları** alanından eklenir. Listelerdeki kart görseli **Kapak** alanından gelmeye
devam eder.

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

## Kaldırılan eski workflow'lar

`Optimize website assets`, `Publish catalogue readers` ve `Import verified YA catalogue`
kaldırıldı: kapak dönüştürme ve katalog okuyucuları artık **Build site from content**
içinde yapılıyor; YA kataloğu içe aktarımı tek seferlikti. Betikleri `scripts/` altında ve
Git geçmişinde duruyor.
