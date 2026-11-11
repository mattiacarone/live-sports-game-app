import { Browser, sleep } from '../.agents/skills/taste-skill/scripts/lib/cdp.mjs';

async function run() {
  const browser = await Browser.launch();
  const page = await browser.newPage({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:8080/');
  await sleep(2500);

  const trace = await page.eval('window.__fetch_trace || "not_run"');
  console.log('Fetch trace:', trace);

  const pCount = await page.eval('document.querySelectorAll(".sport-pill").length');
  console.log('Sport pills count:', pCount);

  const cCount = await page.eval('document.querySelectorAll(".event-card").length');
  console.log('Event cards count:', cCount);

  await browser.close();
}

run().catch(console.error);
