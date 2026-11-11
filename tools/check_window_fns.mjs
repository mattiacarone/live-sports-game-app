import { Browser, sleep } from '../.agents/skills/taste-skill/scripts/lib/cdp.mjs';

async function run() {
  const browser = await Browser.launch();
  const page = await browser.newPage({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:8080/');
  await sleep(1500);

  const res = await page.eval('(() => ({ typeofToggle: typeof toggleSlipDrawer, typeofFetch: typeof fetchMultisportData, typeofSelectSport: typeof selectSport }))()');
  console.log('Function types:', res);

  await browser.close();
}

run().catch(console.error);
