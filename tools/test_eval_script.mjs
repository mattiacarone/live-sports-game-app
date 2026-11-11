import { Browser } from '../.agents/skills/taste-skill/scripts/lib/cdp.mjs';

async function run() {
  const browser = await Browser.launch();
  const page = await browser.newPage({ width: 1440, height: 900 });

  await page.goto('http://127.0.0.1:8080/');
  await new Promise(r => setTimeout(r, 1000));

  const count = await page.eval('document.scripts.length');
  console.log('document.scripts.length:', count);

  for (let i = 0; i < count; i++) {
    const text = await page.eval(`document.scripts[${i}].textContent.slice(0, 100)`);
    console.log(`Script ${i}:`, text.replace(/\s+/g, ' '));
  }

  // Now let's try evaluating a simple statement inside the page
  const testEval = await page.eval('(() => { try { eval(document.scripts[1].textContent); return "eval_succeeded"; } catch(e) { return "eval_error: " + e.message + " at " + e.stack; } })()');
  console.log('Result of eval(document.scripts[1]):', testEval);

  await browser.close();
}

run().catch(console.error);
