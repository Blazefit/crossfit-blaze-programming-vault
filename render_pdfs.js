const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const root = '/home/daneelbrain/hermes-workspace/crossfit-blaze-programming-vault';
  const cycles = JSON.parse(fs.readFileSync(path.join(root, 'data/cycles.json'), 'utf8'));
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 1600 } });
  for (const c of cycles) {
    const url = 'file://' + path.join(root, 'cycles', c.file);
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.pdf({
      path: path.join(root, 'pdfs', `${c.id}.pdf`),
      format: 'Letter',
      printBackground: true,
      margin: { top: '0.35in', right: '0.35in', bottom: '0.45in', left: '0.35in' }
    });
    console.log(`${c.id}.pdf`);
  }
  await browser.close();
})();
