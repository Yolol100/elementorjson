const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

const templateDir = path.resolve(__dirname, '../../templates');
const screenshotDir = path.resolve(__dirname, '../../artifacts/screenshots');

const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 1024, height: 1366 },
  { name: 'mobile', width: 390, height: 844 }
];

function slugify(filename) {
  return path.basename(filename, '.json')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const templates = fs.existsSync(templateDir)
  ? fs.readdirSync(templateDir).filter((name) => name.endsWith('.json')).sort()
  : [];

if (templates.length === 0) {
  test('no templates supplied', async () => {
    test.skip(true, 'Add Elementor JSON files to templates/ to generate previews.');
  });
}

for (const template of templates) {
  const slug = slugify(template);

  for (const viewport of viewports) {
    test(`${template} - ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      const browserErrors = [];
      const consoleErrors = [];
      page.on('pageerror', (error) => browserErrors.push(error.message));
      page.on('console', (message) => {
        if (message.type() === 'error') {
          consoleErrors.push(message.text());
        }
      });

      const response = await page.goto(`/${slug}/`, { waitUntil: 'networkidle' });
      expect(response, 'Expected a WordPress response').not.toBeNull();
      expect(response.ok(), `Expected HTTP success for /${slug}/`).toBeTruthy();

      await expect(page.locator('body')).toBeVisible();
      await expect(
        page.locator('[data-elementor-type]').first(),
        'Expected the page to contain rendered Elementor markup'
      ).toBeVisible();

      fs.mkdirSync(screenshotDir, { recursive: true });

      await page.screenshot({
        path: path.join(screenshotDir, `${slug}-${viewport.name}.png`),
        fullPage: true,
        animations: 'disabled'
      });

      const metadataPath = path.join(screenshotDir, `${slug}-${viewport.name}.json`);
      fs.writeFileSync(
        metadataPath,
        JSON.stringify(
          {
            template,
            slug,
            viewport,
            url: page.url(),
            title: await page.title(),
            browser_errors: browserErrors,
            console_errors: consoleErrors
          },
          null,
          2
        ) + '\n'
      );

      expect(browserErrors, 'Expected no uncaught browser errors').toEqual([]);
      expect(consoleErrors, 'Expected no browser console errors').toEqual([]);
    });
  }
}
