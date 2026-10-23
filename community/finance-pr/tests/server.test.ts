import { afterEach, describe, expect, it } from 'vitest';
import { createServer, type ViteDevServer } from 'vite';
import { mkdirSync, mkdtempSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

let server: ViteDevServer | undefined;
let root: string | undefined;
afterEach(async () => {
  await server?.close(); server = undefined;
  if (root) rmSync(root, { recursive: true, force: true }); root = undefined;
});
describe('demo server privacy', () => {
  it('denies legacy raw evidence files and disables public file serving', async () => {
    const marker = 'FICTIONAL-FINANCE-CANARY';
    root = mkdtempSync(join(realpathSync(tmpdir()), 'finance-pr-server-'));
    mkdirSync(join(root, 'public'));
    writeFileSync(join(root, 'public', 'private-canary.json'), JSON.stringify({ marker }));
    for (const name of ['bundle.json', 'evidence.json', 'fresh_supplier_invoice.json']) {
      writeFileSync(join(root, name), JSON.stringify({ marker }));
    }
    server = await createServer({ root, configFile: resolve('vite.config.ts'), logLevel: 'silent', optimizeDeps: { noDiscovery: true, include: [] }, server: { port: 0, host: '127.0.0.1' } });
    await server.listen();
    const address = server.httpServer!.address();
    if (!address || typeof address === 'string') throw new Error('Missing HTTP address');
    for (const name of ['bundle.json', 'evidence.json', 'fresh_supplier_invoice.json']) {
      for (const url of [`/${name}`, `/${name}?raw`, `/@fs${join(root, name)}`]) {
        const response = await fetch(`http://127.0.0.1:${address.port}${url}`);
        expect(response.status).toBe(403);
        expect(await response.text()).not.toContain(marker);
      }
    }
    const publicResponse = await fetch(`http://127.0.0.1:${address.port}/private-canary.json`);
    expect(publicResponse.status).toBe(404);
    expect(await publicResponse.text()).not.toContain(marker);
    expect(server.config.publicDir).toBe('');
  });
  it('defaults to loopback', async () => {
    server = await createServer({ optimizeDeps: { noDiscovery: true, include: [] } });
    expect(server.config.server.host).toBe('127.0.0.1');
  });
});
