import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const { chromium } = createRequire('/tmp/kage-browser/package.json')('playwright');
const out = resolve('browser-results');
mkdirSync(out, { recursive: true });
const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '4184', '--strictPort'], { cwd: resolve('app'), stdio: 'pipe' });
server.stderr.on('data', d => process.stderr.write(d));
let browser, page;
const errors = [];
const key = 'shadow-village-save-v3-slot-1';
try {
  let ready = false;
  for (let i = 0; i < 80; i++) {
    try { ready = (await fetch('http://127.0.0.1:4184')).ok; } catch {}
    if (ready) break;
    await new Promise(r => setTimeout(r, 250));
  }
  assert(ready, 'Vite started');
  browser = await chromium.launch({ headless: true });
  page = await browser.newPage({ viewport: { width: 412, height: 915 } });
  page.setDefaultTimeout(15000);
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', e => { if (e.type() === 'error') errors.push(e.text()); });
  await page.goto('http://127.0.0.1:4184', { waitUntil: 'networkidle' });
  assert((await page.locator('body').innerText()).length > 100);
  assert.match(await page.locator('meta[name=viewport]').getAttribute('content'), /viewport-fit=contain/);
  await page.evaluate(async key => {
    const { createState } = await import('/src/game/engine.ts');
    const { SUMMONS } = await import('/src/game/summons.ts');
    const state = createState('playing', 'V34 Mobile QC');
    Object.assign(state, { gold: 100000, rice: 100000, ap: 50, threat: 0 });
    state.summons = { inventory: Object.fromEntries(SUMMONS.map(x => [x.id, 1])), recent: [], totalPulls: 10, sinceEpic: 11 };
    state.ninjas.forEach((n, i) => Object.assign(n, {
      name: ['Paper Tester', 'Sound Tester', 'Venom Tester'][i] ?? n.name,
      traits: [['kamioriClan'], ['hibikiClan'], ['kasumoriClan']][i % 3].concat('kekkeiTalent'),
      nature: 'fire', secondaryNature: 'water', level: 80, rank: 'jonin', legend: null, sp: 5,
      summonId: null, status: 'ready', jutsuKnown: [], jutsuGranted: [], jutsuEquipped: [],
      genjutsuKnown: [], genjutsuEquipped: [], perks: [], techniqueTree: undefined,
    }));
    localStorage.setItem(key, JSON.stringify({ version: 3, savedAt: Date.now(), state }));
  }, key);
  const saved = () => page.evaluate(key => JSON.parse(localStorage.getItem(key)).state, key);
  const resume = async () => {
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('button', { name: /V34 Mobile QC.*CONTINUE/ }).first().click();
    await page.getByRole('button', { name: 'Summons', exact: true }).click();
  };
  await resume();
  assert.equal(await page.getByRole('button', { name: /^View .* pact$/ }).count(), 10);
  await page.getByRole('button', { name: 'Bond Gamaza to Paper Tester', exact: true }).click();
  assert.equal((await saved()).ninjas[0].summonId, 'sum_toad');
  assert(await page.getByRole('button', { name: 'Bond Gamaza to Sound Tester', exact: true }).isDisabled());
  await resume();
  assert.equal((await saved()).ninjas[0].summonId, 'sum_toad');
  await page.getByRole('button', { name: 'RELEASE', exact: true }).click();
  assert.equal((await saved()).ninjas[0].summonId, null);
  const before = await saved();
  await page.getByRole('button', { name: /^5 PACTS/ }).click();
  const reveal = page.getByRole('dialog', { name: 'Pact sealed' });
  await reveal.waitFor();
  assert.equal(await reveal.locator('img').count(), 5);
  assert.match(await reveal.innerText(), /EPIC|LEGENDARY/);
  await page.screenshot({ path: `${out}/summon-five-pull.png` });
  await reveal.getByRole('button', { name: 'CLOSE', exact: true }).click();
  const after = await saved();
  assert.equal(after.summons.totalPulls, before.summons.totalPulls + 5);
  assert.equal(after.ap, before.ap - 1);
  assert(after.gold < before.gold && after.rice < before.rice);
  for (const width of [412, 360]) {
    await page.setViewportSize({ width, height: width === 360 ? 740 : 855 });
    await page.getByRole('button', { name: 'View Byakko pact', exact: true }).click();
    await page.getByRole('button', { name: 'Bond Byakko to Paper Tester', exact: true }).scrollIntoViewIfNeeded();
    const layout = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth, overlay: !!document.querySelector('vite-error-overlay'), images: [...document.images].filter(i => i.src.includes('/summons/')).map(i => i.complete && i.naturalWidth > 0) }));
    assert(layout.scroll <= layout.width, JSON.stringify(layout));
    assert(!layout.overlay && layout.images.length >= 10 && layout.images.every(Boolean));
    await page.screenshot({ path: `${out}/summons-${width}.png` });
  }
  await page.getByRole('button', { name: 'Bond Byakko to Paper Tester', exact: true }).click();
  assert.equal((await saved()).ninjas[0].summonId, 'sum_fox');
  await page.getByRole('button', { name: /^Shinobi/ }).click();
  await page.getByText('Paper Tester', { exact: true }).click();
  await page.getByRole('button', { name: 'JUTSU', exact: true }).click();
  const text = await page.locator('body').innerText();
  assert.match(text, /Paper Seals/);
  assert.match(text, /Steam Veil/);
  assert.match(text, /HP\/round/);
  const knownBefore = (await saved()).ninjas[0].jutsuKnown.length;
  await page.getByRole('button', { name: 'LEARN · 1 JP', exact: true }).first().click();
  assert.equal((await saved()).ninjas[0].jutsuKnown.length, knownBefore + 1);
  await page.screenshot({ path: `${out}/clan-and-kekkei-jutsu.png` });
  // The scrollable details dialog must not clip its point-spend overlay.
  await page.getByRole('button', { name: 'Train Ninjutsu', exact: true }).click();
  await page.getByText('CONFIRM POINT SPEND', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'CANCEL', exact: true }).click();
  const close = page.getByRole('button', { name: 'Close ninja details', exact: true });
  await close.scrollIntoViewIfNeeded();
  const bounds = await close.boundingBox();
  const viewport = page.viewportSize();
  assert(bounds && bounds.y >= 0 && bounds.x >= 0 && bounds.y + bounds.height <= viewport.height && bounds.x + bounds.width <= viewport.width);
  await page.screenshot({ path: `${out}/phone-safe-area-close.png` });
  await close.click();
  assert.equal(await page.getByRole('dialog', { name: 'Paper Tester details' }).count(), 0);
  assert.deepEqual(errors, []);
  console.log('PASS mobile: 360/412px; ten artworks; five-pull reveal and pity; costs; copy locks; bond/release/save reload; clan + Kekkei tree, DoT preview and learning');
} catch (e) {
  if (page) {
    await page.screenshot({ path: `${out}/failure.png` }).catch(() => {});
    writeFileSync(`${out}/failure.txt`, `${e.stack}\n${errors.join('\n')}\n${await page.locator('body').innerText().catch(() => '')}`);
  }
  throw e;
} finally {
  await browser?.close();
  server.kill();
}
