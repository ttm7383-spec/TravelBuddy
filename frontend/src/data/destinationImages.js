const DESTINATION_IMAGES = {
  // UK
  london: "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&q=80",
  edinburgh: "https://images.unsplash.com/photo-1506377585622-bedcbb027afc?w=800&q=80",
  manchester: "https://images.unsplash.com/photo-1515586838455-8f8f940d6853?w=800&q=80",
  bath: "https://images.unsplash.com/photo-1580137189272-c9379f8864fd?w=800&q=80",
  york: "https://images.unsplash.com/photo-1575378607280-9a0e64d194cc?w=800&q=80",
  oxford: "https://images.unsplash.com/photo-1590058175520-68e9aa8e0713?w=800&q=80",
  cambridge: "https://images.unsplash.com/photo-1579782483458-83d02161294e?w=800&q=80",
  brighton: "https://images.unsplash.com/photo-1520942702018-0862200e6873?w=800&q=80",
  bristol: "https://images.unsplash.com/photo-1578390432942-d38a498df82c?w=800&q=80",
  liverpool: "https://images.unsplash.com/photo-1560107806-8bcc2e651d2a?w=800&q=80",
  glasgow: "https://images.unsplash.com/photo-1583264277915-d5e934f55bb2?w=800&q=80",
  cardiff: "https://images.unsplash.com/photo-1572883454114-efb8ff2e24fe?w=800&q=80",

  // Western Europe
  paris: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=80",
  amsterdam: "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=800&q=80",
  brussels: "https://images.unsplash.com/photo-1559113202-c916b8e44373?w=800&q=80",
  lisbon: "https://images.unsplash.com/photo-1585208798174-6cedd4454a2d?w=800&q=80",
  madrid: "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=800&q=80",
  barcelona: "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800&q=80",
  seville: "https://images.unsplash.com/photo-1515443961218-a51367888e4b?w=800&q=80",
  porto: "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=800&q=80",
  valencia: "https://images.unsplash.com/photo-1599030870797-c3ab7a4b7e88?w=800&q=80",
  rome: "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800&q=80",
  florence: "https://images.unsplash.com/photo-1543429258-3bbb779feda6?w=800&q=80",
  venice: "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=800&q=80",
  milan: "https://images.unsplash.com/photo-1520440229-6469a149ac59?w=800&q=80",
  naples: "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=800&q=80",
  athens: "https://images.unsplash.com/photo-1555993539-1732b0258235?w=800&q=80",
  santorini: "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800&q=80",
  mykonos: "https://images.unsplash.com/photo-1601581875309-fafbf2d3ed3a?w=800&q=80",

  // Central Europe
  berlin: "https://images.unsplash.com/photo-1560969184-10fe8719e047?w=800&q=80",
  munich: "https://images.unsplash.com/photo-1595867818082-083862f3d630?w=800&q=80",
  vienna: "https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=800&q=80",
  prague: "https://images.unsplash.com/photo-1541849546-216549ae216d?w=800&q=80",
  budapest: "https://images.unsplash.com/photo-1565426873118-a17ed65d74b9?w=800&q=80",
  warsaw: "https://images.unsplash.com/photo-1519197924294-4ba991a11128?w=800&q=80",
  krakow: "https://images.unsplash.com/photo-1558005137-d9619a5c539f?w=800&q=80",

  // Northern Europe
  copenhagen: "https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?w=800&q=80",
  stockholm: "https://images.unsplash.com/photo-1509356843151-3e7d96241e11?w=800&q=80",
  oslo: "https://images.unsplash.com/photo-1433757890385-a5e5e27b048e?w=800&q=80",
  reykjavik: "https://images.unsplash.com/photo-1474690870753-1b92efa1f2d8?w=800&q=80",
  helsinki: "https://images.unsplash.com/photo-1538332576228-eb5b4c4de6f5?w=800&q=80",
  dublin: "https://images.unsplash.com/photo-1549918864-48ac978761a4?w=800&q=80",

  // Mediterranean
  dubrovnik: "https://images.unsplash.com/photo-1555990538-1e2a5245b891?w=800&q=80",
  split: "https://images.unsplash.com/photo-1565186999622-7e8e2a7b5a5e?w=800&q=80",
  valletta: "https://images.unsplash.com/photo-1514222134-b57cbb8ce073?w=800&q=80",
  nicosia: "https://images.unsplash.com/photo-1567606404464-4d3c1b8e2938?w=800&q=80",
};

const CATEGORY_IMAGES = {
  beach: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&q=80",
  adventure: "https://images.unsplash.com/photo-1551632811-561732d1e306?w=600&q=80",
  culture: "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=600&q=80",
  city: "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=600&q=80",
  nature: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&q=80",
  nightlife: "https://images.unsplash.com/photo-1519214605650-76a613ee3245?w=600&q=80",
  food: "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80",
  wellness: "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=600&q=80",
  luxury: "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=600&q=80",
  family: "https://images.unsplash.com/photo-1511895426328-dc8714191300?w=600&q=80",
};

export { DESTINATION_IMAGES, CATEGORY_IMAGES };
export default DESTINATION_IMAGES;
