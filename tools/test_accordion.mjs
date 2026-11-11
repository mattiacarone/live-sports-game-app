import { Browser, sleep } from '../.agents/skills/taste-skill/scripts/lib/cdp.mjs';

async function testToggle() {
  const browser = await Browser.launch();
  const page = await browser.newPage({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:8080/');
  await sleep(1500);

  // Click the first dossier-toggle-bar
  const toggled = await page.eval('(() => { const btn = document.querySelector(".dossier-toggle-bar"); if (!btn) return false; btn.click(); return true; })()');
  console.log('Clicked dossier toggle:', toggled);
  await sleep(500);

  const isOpen = await page.eval('(() => { const wrap = document.querySelector(".dossier-wrapper"); return wrap ? wrap.classList.contains("open") : false; })()');
  console.log('Dossier wrapper is open:', isOpen);

  const booksTableVisible = await page.eval('(() => { const t = document.querySelector(".dossier-wrapper .data-table"); return !!t; })()');
  console.log('12 Bookmakers table rendered inside open dossier:', booksTableVisible);

  await browser.close();
  console.log('Accordion test completed successfully!');
}

testToggle().catch(err => {
  console.error(err);
  process.exit(1);
});
how are the 