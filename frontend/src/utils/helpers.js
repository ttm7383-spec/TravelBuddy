// Small, shared helpers used across the app.

export const toTitleCase = (str) =>
  str
    ?.split(' ')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ') || '';

export const decodeText = (str) =>
  str
    ?.replace(/\\u2013/g, '\u2013')
    .replace(/\\u00b0/g, '\u00b0')
    .replace(/\\u00a3/g, '\u00a3')
    .replace(/\\u2019/g, "'")
    .replace(/\\u201c/g, '"')
    .replace(/\\u201d/g, '"') || str;

// Default fallback image used when an Unsplash photo fails to load.
export const FALLBACK_IMG =
  'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=600&q=80';

const UNSPLASH_IDS = {
  barcelona: 'photo-1583422409516-2895a77efded',
  paris: 'photo-1502602898657-3e91760cbb34',
  tokyo: 'photo-1540959733332-eab4deabeeaf',
  bali: 'photo-1537996194471-e657df975ab4',
  rome: 'photo-1552832230-c0197dd311b5',
  amsterdam: 'photo-1534351590666-13e3e96b5017',
  london: 'photo-1513635269975-59663e0ac1ad',
  edinburgh: 'photo-1506377585622-bedcbb5a9d13',
  lisbon: 'photo-1585208798174-6cedd4454a2d',
  prague: 'photo-1541849546-216549ae216d',
  budapest: 'photo-1565426873118-a17ed65d74b9',
  santorini: 'photo-1570077188670-e3a8d69ac5ff',
  madrid: 'photo-1543783207-ec64e4d95325',
  athens: 'photo-1555993539-1732b0258235',
  dubrovnik: 'photo-1555990538-c4d6c8888a4c',
  vienna: 'photo-1516550893923-42d28e5677af',
  berlin: 'photo-1560969184-10fe8719e047',
  cotswolds: 'photo-1500534314209-a25ddb2bd429',
  'lake-district': 'photo-1464822759023-fed622ff2c3b',
  bath: 'photo-1580974852861-e5eba6a1d33d',
  brighton: 'photo-1567157577867-05ccb1388e66',
  york: 'photo-1519944159571-9cca1c8e3dd6',
  cornwall: 'photo-1510812431401-41d2bd2722f3',
  hotel1: 'photo-1566073771259-6a8506099945',
  hotel2: 'photo-1520250497591-112f2f40a3f4',
  hotel3: 'photo-1551882547-ff40c4a49f7e',
};

export const unsplashImage = (key, w = 600) => {
  const id = UNSPLASH_IDS[String(key || '').toLowerCase()];
  if (!id) return FALLBACK_IMG;
  return `https://images.unsplash.com/${id}?w=${w}&q=80`;
};

export const onImgError = (e) => {
  e.target.onerror = null;
  e.target.src = FALLBACK_IMG;
};
