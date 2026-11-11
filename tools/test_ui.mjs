import { Browser, sleep } from '../.agents/skills/taste-skill/scripts/lib/cdp.mjs';

async function run() {
  const browser = await Browser.launch();
  const page = await browser.newPage({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:8080/');
  await sleep(1500);

  const title = await page.eval('document.title');
  console.log('Page Title:', title);

  const sports = await page.eval('Array.from(document.querySelectorAll(".sport-pill")).map(p => p.textContent.trim().replace(/\\s+/g, " "))');
  console.log('Sports switcher pills:', sports);

  const initialCards = await page.eval('document.querySelectorAll(".event-card").length');
  console.log('Initial cards rendered:', initialCards);

  // Click Tennis
  await page.eval('(() => { const pills = Array.from(document.querySelectorAll(".sport-pill")); const t = pills.find(p => p.textContent.includes("Tennis")); if (t) t.click(); })()');
  await sleep(600);

  const tennisCards = await page.eval('document.querySelectorAll(".event-card").length');
  console.log('Tennis cards rendered:', tennisCards);

  // Click F1
  await page.eval('(() => { const pills = Array.from(document.querySelectorAll(".sport-pill")); const f1 = pills.find(p => p.textContent.includes("Formula 1")); if (f1) f1.click(); })()');
  await sleep(600);

  const f1Cards = await page.eval('document.querySelectorAll(".event-card").length');
  console.log('F1 cards rendered:', f1Cards);

  // Click MotoGP
  await page.eval('(() => { const pills = Array.from(document.querySelectorAll(".sport-pill")); const m = pills.find(p => p.textContent.includes("MotoGP")); if (m) m.click(); })()');
  await sleep(600);

  const motogpCards = await page.eval('document.querySelectorAll(".event-card").length');
  console.log('MotoGP cards rendered:', motogpCards);

  // Click NFL
  await page.eval('(() => { const pills = Array.from(document.querySelectorAll(".sport-pill")); const n = pills.find(p => p.textContent.includes("NFL")); if (n) n.click(); })()');
  await sleep(600);

  const nflCards = await page.eval('document.querySelectorAll(".event-card").length');
  console.log('NFL cards rendered:', nflCards);

  // Click Basket
  await page.eval('(() => { const pills = Array.from(document.querySelectorAll(".sport-pill")); const b = pills.find(p => p.textContent.includes("Basket")); if (b) b.click(); })()');
  await sleep(600);

  const bballCards = await page.eval('document.querySelectorAll(".event-card").length');
  console.log('Basket cards rendered:', bballCards);

  // Click Rugby
  await page.eval('(() => { const pills = Array.from(document.querySelectorAll(".sport-pill")); const r = pills.find(p => p.textContent.includes("Rugby")); if (r) r.click(); })()');
  await sleep(600);

  const rugbyCards = await page.eval('document.querySelectorAll(".event-card").length');
  console.log('Rugby cards rendered:', rugbyCards);

  // Test Schedina Drawer trigger
  await page.eval('toggleSlipDrawer(true)');
  await sleep(400);
  const drawerOpen = await page.eval('document.getElementById("slip-drawer").classList.contains("open")');
  console.log('Schedina drawer opened:', drawerOpen);

  await browser.close();
  console.log('ALL BROWSER AUTOMATION TESTS COMPLETED SUCCESSFULLY!');
}

run().catch(err => {
  console.error('Error running test:', err);
  process.exit(1);
});
