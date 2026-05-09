/**
 * Extension tests -- run via the extension_test_run MCP tool.
 *
 * These tests connect to the running Nimbalyst instance via CDP.
 * Make sure Nimbalyst is running in dev mode (npm run dev).
 *
 * Usage:
 *   extension_test_run({ testFile: "<absolute-path>/tests/basics.spec.ts" })
 */
import { test, expect, extensionEditor } from '@nimbalyst/extension-sdk/testing';

test.describe('My Nimbalyst Extension', () => {
  test('editor renders for the target file', async ({ page }) => {
    const editor = extensionEditor(page, 'com.developer.my-nimbalyst-extension');
    await expect(editor).toBeVisible({ timeout: 5000 });
  });

  // Add more tests here as you build out the extension
});
