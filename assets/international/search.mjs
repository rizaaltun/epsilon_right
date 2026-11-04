export function normalizeTurkish(str) {
  if (!str) return "";
  return str
    .toString()
    .replace(/İ/g, 'i')
    .replace(/I/g, 'i')
    .replace(/ı/g, 'i')
    .toLowerCase()
    .replace(/ğ/g, 'g')
    .replace(/ü/g, 'u')
    .replace(/ş/g, 's')
    .replace(/ö/g, 'o')
    .replace(/ç/g, 'c')
    .replace(/[âîûéèê]/g, (m) => ({ 'â': 'a', 'î': 'i', 'û': 'u', 'é': 'e', 'è': 'e', 'ê': 'e' }[m] || m))
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function phoneticSkeleton(normStr) {
  return normStr
    .replace(/ph/g, 'f')
    .replace(/w/g, 'v')
    .replace(/q/g, 'k')
    .replace(/x/g, 'ks')
    .replace(/([a-z])\1+/g, '$1');
}

export function levenshteinDistance(a, b) {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  if (Math.abs(a.length - b.length) > 5) return 99;

  const matrix = [];
  for (let i = 0; i <= b.length; i++) matrix[i] = [i];
  for (let j = 0; j <= a.length; j++) matrix[0][j] = j;

  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  return matrix[b.length][a.length];
}

export function bigramSimilarity(a, b) {
  if (a === b) return 1;
  if (a.length < 2 || b.length < 2) return 0;
  const bigramsA = new Map();
  for (let i = 0; i < a.length - 1; i++) {
    const bg = a.substring(i, i + 2);
    bigramsA.set(bg, (bigramsA.get(bg) || 0) + 1);
  }
  let intersection = 0;
  for (let i = 0; i < b.length - 1; i++) {
    const bg = b.substring(i, i + 2);
    const count = bigramsA.get(bg) || 0;
    if (count > 0) {
      bigramsA.set(bg, count - 1);
      intersection++;
    }
  }
  return (2.0 * intersection) / (a.length + b.length - 2);
}

export function score(query, value) {
  const q = normalizeTurkish(query), v = normalizeTurkish(value);
  if (!q) return 1;
  if (v === q) return 100;
  if (v.includes(q)) return 90;
  const words = v.split(' ');
  const tokens = q.split(' ');
  const scores = tokens.map(token => Math.max(...words.map(word => {
    if (word.startsWith(token)) return 85;
    const a = phoneticSkeleton(token), b = phoneticSkeleton(word);
    if (a === b) return 80;
    if (token.length < 3) return 0;
    const distance = levenshteinDistance(a, b);
    const similarity = 1 - distance / Math.max(a.length, b.length);
    return Math.max(similarity >= .6 ? similarity * 75 : 0, bigramSimilarity(a,b) >= .55 ? bigramSimilarity(a,b)*70 : 0);
  })));
  return scores.every(s => s >= 38) ? scores.reduce((a,b)=>a+b,0)/scores.length : 0;
}
export function searchBooks(books, query) {
  const digits = query.replace(/[\s-]/g, '');
  return books.map(book => ({book, score: /^\d+$/.test(digits) ? (book.isbn.includes(digits) ? 100 : 0) : Math.max(score(query,book.title),score(query,book.author),score(query,book.brand))}))
    .filter(r => r.score > 0).sort((a,b)=>b.score-a.score || a.book.title.localeCompare(b.book.title,'tr'));
}
export function detectMarket(timeZone = '', language = '') {
  const zones = {'Europe/Berlin':'DE','Europe/Busingen':'DE','Europe/London':'UK','Europe/Amsterdam':'NL','Europe/Brussels':'BE','Europe/Vienna':'AT','Europe/Zurich':'CH','Europe/Stockholm':'SE','Europe/Helsinki':'FI','Europe/Copenhagen':'DK','Europe/Oslo':'NO','Europe/Paris':'FR','Asia/Dubai':'AE'};
  if (zones[timeZone]) return zones[timeZone];
  if (/^Australia\//.test(timeZone)) return 'AU';
  if (/^America\/(New_York|Chicago|Denver|Los_Angeles|Detroit|Phoenix|Anchorage|Adak|Boise|Indiana\/|Kentucky\/|North_Dakota\/)/.test(timeZone) || timeZone === 'Pacific/Honolulu') return 'US';
  const region = language.split('-').pop().toUpperCase();
  return ['DE','GB','US','NL','BE','AT','CH','SE','FI','DK','NO','FR','AE','AU'].includes(region) ? (region==='GB'?'UK':region) : 'ALL';
}
