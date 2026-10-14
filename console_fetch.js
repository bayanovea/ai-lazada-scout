// Paste into DevTools on a logged-in lazada.co.th tab. Fetches each query via /tag/<slug>/?ajax=true,
// downloads lazada_dump.json, copies it to the clipboard and keeps window.lazadaOut.
// Split the dump into data/raw with split_dump.py.
(async () => {
  const queries = ["ไม้ถูพื้น ถังปั่น", "ไม้ม็อบ รีดน้ำ", "kitchen scale", "coffee scale"];  // paste the query strings from queries.py here
  const out = {};
  for (const [i, q] of queries.entries()) {
    const url = `/tag/${encodeURIComponent(q.toLowerCase().replace(/ /g, '-'))}/?ajax=true`;
    try {
      const r = await fetch(url, {credentials: 'include'});
      const d = JSON.parse(await r.text());
      out[q] = {mods: {listItems: d.mods.listItems || []}};
      console.log(`${i + 1}/${queries.length} ok ${q}: ${out[q].mods.listItems.length}`);
    } catch (e) { console.warn(`${i + 1}/${queries.length} FAIL ${q}`); }
    await new Promise(res => setTimeout(res, 3000 + Math.random() * 3000));
  }
  window.lazadaOut = out;  // survives a blocked download: run copy(JSON.stringify(lazadaOut)) by hand
  try { copy(JSON.stringify(out)); console.log('copied to clipboard'); } catch (e) { console.warn('auto-copy failed: run copy(JSON.stringify(lazadaOut))'); }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out)], {type: 'application/json'}));
  a.download = 'lazada_dump.json'; a.click();
  console.log('done:', Object.keys(out).length, 'of', queries.length);
})();