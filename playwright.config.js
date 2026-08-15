const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  timeout: 90000,
  expect: {
    timeout: 10000,
    toHaveScreenshot: {
      animations: 'disabled',
      maxDiffPixelRatio: 0.002
    }
  },
  use: {
    baseURL: 'http://127.0.0.1:8888',
    trace: 'retain-on-failure'
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
    { name: 'webkit', use: { browserName: 'webkit' } }
  ],
  reporter: [['list'], ['html', { outputFolder: 'artifacts/playwright-report', open: 'never' }]]
});
