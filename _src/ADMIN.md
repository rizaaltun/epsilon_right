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
yükleme), **Yazarlar**, **Haberler**, **Fuarlar & Etkinlikler**, **Yayınevleri**,
**Ana sayfa vitrinleri**, **Site ayarları**. Sayfa metinleri ve kataloglar sonraki adımlarda eklenecek.

Kitap sayıları (yayınevi kartları, yazarlar listesi, Representations) her derlemede
kitaplardan hesaplanır; elle güncellenmez.

Fuarlar bitiş tarihlerine göre "Upcoming" ya da "Past" görünür; workflow her sabah da
çalıştığı için bir etkinlik bittiğinde ertesi sabah kendiliğinden "Past"a geçer.

## Kimler girebilir

Repoya **Write** yetkisi olan GitHub hesapları. Yeni bir editör için:
repo → Settings → Collaborators → Add people → rol: Write. Yetkisi olmayan biri
paneli açsa bile hiçbir şeyi okuyamaz ya da değiştiremez. Editörlerin GitHub
hesaplarında iki adımlı doğrulamanın açık olması önerilir.

## GitHub ile giriş kurulumu (bir kez, ~15 dakika)

Site sunucusuz olduğu için "GitHub ile Giriş Yap" düğmesi, OAuth adımını yapan küçük
ve ücretsiz bir Cloudflare Worker'a ihtiyaç duyar: [Sveltia CMS Authenticator](https://github.com/sveltia/sveltia-cms-auth).
Ayrıntılı ve güncel adımlar o reponun README'sindedir; özetle:

1. **Worker'ı kurun.** sveltia-cms-auth README'sindeki "Deploy to Cloudflare Workers"
   düğmesiyle (ya da `wrangler deploy`) kurun. Adresini not edin, örn.
   `https://epsilon-cms-auth.<hesap>.workers.dev`.
2. **GitHub OAuth App oluşturun.** GitHub → Settings → Developer settings → OAuth Apps → New OAuth App
   - Homepage URL: `https://epsilonpublishinggroup.com`
   - Authorization callback URL: `<worker adresi>/callback`
3. **Worker'a değişkenleri girin** (Cloudflare → Workers → ayarlar → Variables):
   - `GITHUB_CLIENT_ID`: OAuth App'in Client ID'si
   - `GITHUB_CLIENT_SECRET`: OAuth App'in Client Secret'ı (secret olarak, şifreli)
   - `ALLOWED_DOMAINS`: `epsilonpublishinggroup.com`
4. **`admin/config.yml`** içindeki `base_url` satırının başındaki `#` işaretini kaldırıp
   worker adresini yazın ve commit edin.

O zamana kadar yetkili kişiler "Erişim Token'ı Kullanarak Giriş Yap" ile girebilir:
GitHub → Settings → Developer settings → Fine-grained tokens, yalnızca bu repo,
Contents: Read and write.

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

## Dikkat: HTML'i doğrudan değiştiren eski workflow'lar

`Optimize website assets`, `Publish catalogue readers` ve `Import verified YA catalogue`
workflow'ları üretilmiş HTML'i doğrudan düzenler. Bir sonraki içerik derlemesi bu
değişiklikleri geri alır. Bunlardan biri çalıştırılmadan önce ilgili değişikliğin
`_src/content/` tarafına da yapılması gerekir (ayrıntı: `_src/README.md`).
