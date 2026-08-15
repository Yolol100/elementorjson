const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: 'http://127.0.0.1:8888',
    trace: 'retain-on-failure'
  },
  reporter: [['list'], ['html', { outputFolder: 'artifacts/playwright-report', open: 'never' }]]
});
