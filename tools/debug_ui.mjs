import { Browser, sleep } from '../.agents/skills/taste-skill/scripts/lib/cdp.mjs';

async function run() {
  const browser = await Browser.launch();
  const page = await browser.newPage({ width: 1440, height: 900 });

  await page.goto('http://127.0.0.1:8080/');
  await sleep(2500);

  const errors = await page.eval('window.__errors || []');
  console.log('Window errors:', errors);

  const appState = await page.eval('(() => ({ hasApp: typeof APP !== "undefined", events: typeof APP !== "undefined" ? (APP.allEvents ? APP.allEvents.length : "no allEvents") : "no APP", sportsMeta: typeof APP !== "undefined" ? (APP.sportsMeta ? APP.sportsMeta.length : "no sportsMeta") : "no APP" }))()');
  console.log('App state in browser:', appState);

  const innerSwitcher = await page.eval('document.getElementById("sport-switcher-bar").innerHTML');
  console.log('Switcher innerHTML length:', innerSwitcher.length);

  await browser.close();
}

run().catch(console.error);
