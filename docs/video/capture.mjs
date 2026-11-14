// Makes the stills and demo-silent.mp4 in this folder from the running app. See README.md.
// It drives headless Chrome over the DevTools protocol. No packages to install: Node 22+ has WebSocket and fetch built in.
// Needs Google Chrome, and ffmpeg for the video. Start the app first (python app/app.py), then from the repo folder:
//   node docs/video/capture.mjs stills docs/video                    five 1280x800 PNGs, opened through the page's # links
//   node docs/video/capture.mjs video  docs/video/demo-silent.mp4    the run sheet of docs/video-script.md, 1:58, silent
// Another port: APP=http://localhost:7863 node docs/video/capture.mjs ...
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const APP = process.env.APP || 'http://localhost:7860';
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9337, W = 1280, H = 800, FPS = 30;
const [mode, out] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const profile = mkdtempSync(join(tmpdir(), 'smokecheck-capture-'));   // a fresh Chrome profile: no remembered city
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  `--window-size=${W},${H}`, '--hide-scrollbars', '--force-device-scale-factor=1', 'about:blank'], { stdio: 'ignore' });

let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === 'page'); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let nextId = 0; const waiting = new Map(); const on = {};
ws.onmessage = ({ data }) => {
  const msg = JSON.parse(data);
  if (msg.id) { waiting.get(msg.id)?.(msg.result ?? msg); waiting.delete(msg.id); }
  else on[msg.method]?.(msg.params);
};
const send = (method, params = {}) => new Promise((r) => { waiting.set(++nextId, r); ws.send(JSON.stringify({ id: nextId, method, params })); });
const js = async (expression) => (await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result?.value;

await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
const open = async (hash) => {   // a hash-only change does not reload, so go through about:blank
  await send('Page.navigate', { url: 'about:blank' });
  await send('Page.navigate', { url: `${APP}/#${hash}` });
};
const text = () => js(`document.body.innerText.replace(/\\s+/g, ' ')`);

if (mode === 'stills') {
  mkdirSync(out, { recursive: true });
  const shots = [['01-tomorrow-live', 'tomorrow//Minneapolis'], ['02-minneapolis-0731', 'test/2025-07-31/Minneapolis'],
    ['03-chicago-0731', 'test/2025-07-31/Chicago'], ['04-chicago-0801', 'test/2025-08-01/Chicago'], ['05-does-it-work', 'results']];
  for (const [name, hash] of shots) {
    await open(hash);
    await sleep(5000);   // counts, letters and the stamp have all settled
    const { data } = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(`${out}/${name}.png`, Buffer.from(data, 'base64'));
    console.log(name, '|', await text());
  }
}

if (mode === 'video') {
  const ffmpeg = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-crf', '21', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  // Screencast frames arrive only when the picture changes, each with a timestamp. Repeat the last frame to fill a steady 30 fps.
  let t0 = null, written = 0, last = null, stopAt = Infinity;
  const fill = (upTo) => { for (; last && written < upTo; written++) ffmpeg.stdin.write(last); };
  on['Page.screencastFrame'] = ({ data, metadata, sessionId }) => {
    send('Page.screencastFrameAck', { sessionId });
    t0 ??= metadata.timestamp;
    fill(Math.min(Math.round((metadata.timestamp - t0) * FPS), stopAt));
    last = Buffer.from(data, 'base64');
  };

  // The cursor: headless Chrome draws none, so a yellow dot follows the mouse events. It swells for a moment on a click.
  const addCursor = () => js(`(() => {
    const dot = document.createElement('div');
    dot.style.cssText = 'position:fixed;left:0;top:0;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;background:#ffd400;' +
      'box-shadow:0 0 0 2px rgba(0,0,0,.55);pointer-events:none;z-index:99999;transition:scale .15s';
    document.body.append(dot);
    addEventListener('mousemove', (e) => { dot.style.translate = e.clientX + 'px ' + e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { dot.style.scale = 1.7; setTimeout(() => { dot.style.scale = 1; }, 220); }, true);
  })()`);
  let mx = 640, my = 520;
  const move = async (x, y, ms = 700) => {
    const x0 = mx, y0 = my, began = Date.now();
    for (let done = 0; done < 1;) {   // by the clock, so a move takes exactly `ms` and the next click lands on time
      done = Math.min((Date.now() - began) / ms, 1);
      const k = (1 - Math.cos(Math.PI * done)) / 2;   // ease in and out
      mx = x0 + (x - x0) * k; my = y0 + (y - y0) * k;
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: mx, y: my });
      await sleep(12);
    }
  };
  // Where to point: beside the words, never on top of them. side is 'right', 'left', 'under' or 'on' (for clicks).
  const beside = (selector, side) => js(`(() => { const range = document.createRange(); range.selectNodeContents(document.querySelector(${JSON.stringify(selector)}));
    let b = range.getBoundingClientRect();
    if (!b.width) b = document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();   // a <select> has no text to measure
    const midX = b.left + b.width / 2, midY = b.top + b.height / 2;
    return { right: [b.right + 16, midY], left: [b.left - 14, midY], under: [midX, b.bottom + 12], on: [midX, midY + 8] }[${JSON.stringify(side)}]; })()`);
  const moveTo = async (selector, ms, side = 'right') => move(...(await beside(selector, side)), ms);
  const click = async () => {
    for (const type of ['mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type, x: mx, y: my, button: 'left', clickCount: 1 });
  };

  await open('tomorrow//Minneapolis');
  await sleep(4000);   // page loaded and settled before the recording starts
  if (/Updating|Couldn't update/.test(await text())) throw new Error('Tomorrow view is not settled: ' + await text());
  await addCursor();
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: mx, y: my });
  await send('Page.startScreencast', { format: 'jpeg', quality: 92, everyNthFrame: 1 });
  const start = Date.now();
  const at = (seconds) => sleep(Math.max(0, start + seconds * 1000 - Date.now()));   // wait until this moment of the run sheet
  const log = async (label) => console.log(((Date.now() - start) / 1000).toFixed(1).padStart(6), label, '|', await text());

  // ---- The run sheet (docs/video-script.md). Each click lands on its run-sheet second. ----
  await log('0:00 Tomorrow');
  await at(15.5);  await moveTo('#n-forecast', 900);                       // "tomorrow's real forecast": the number...
  await at(19);    await moveTo('#made', 800);                             // ...and when it was made
  await at(21.8);  await moveTo('.views button[data-view="test"]', 1000, 'on');
  await at(23);    await click();                                          // 0:23 2025 test run (Minneapolis, Jul 31)
  await at(27.5);  await moveTo('#n-forecast', 900);   await log('0:23 test run');
  await at(30.5);  await moveTo('#n-noaa', 800);
  await at(32);    await moveTo('#n-measured', 700, 'left');
  await at(34);    await moveTo('#stamp-title', 700);
  await at(36);    await moveTo('#n-line', 1100);                          // 0:36 the line at 32
  await at(41);    await moveTo('#legend-line', 1100);
  await at(46.6);  await moveTo('#city', 1200, 'on');
  await at(48);    await click();                                          // 0:48 city picker -> Chicago
  // Headless Chrome cannot draw the picker's drop-down list, so the choice is set the way picking it would.
  await js(`(() => { const c = document.querySelector('#city'); c.value = 'Chicago'; c.dispatchEvent(new Event('change', { bubbles: true })); c.blur(); })()`);
  await at(51);    await moveTo('#n-forecast', 1000);  await log('0:48 Chicago');
  await at(54);    await moveTo('#n-measured', 900, 'left');
  await at(56);    await moveTo('#stamp-title', 700);
  await at(61.6);  await moveTo('#next', 1200, 'on');
  await at(63);    await click();                                          // 1:03 next day -> Aug 1
  await at(66);    await moveTo('#n-noaa', 900);       await log('1:03 Aug 1');
  await at(67.8);  await moveTo('#n-forecast', 900);
  await at(69.6);  await moveTo('#n-measured', 800, 'left');
  await at(70.8);  await moveTo('.views button[data-view="results"]', 1000, 'on');
  await at(72);    await click();                                          // 1:12 Does it work?
  await at(74);    await move(1210, 680, 900);         await log('1:12 Does it work?');   // out of the way while the inputs are listed
  await at(89);    await moveTo('#table tbody tr:nth-child(1) td:nth-child(2)', 900);   // 2.36
  await at(92);    await moveTo('#table tbody tr:nth-child(2) td:nth-child(2)', 700);   // 3.20
  await at(98.5);  await moveTo('#but', 900);                                           // warnings: 127 against 123
  await at(103.5); await moveTo('#weak', 900);                                          // 1:44 the weak spot
  await at(118);   await log('1:58 end');

  stopAt = 118 * FPS;
  await send('Page.stopScreencast');
  fill(stopAt);
  ffmpeg.stdin.end();
  await new Promise((r) => ffmpeg.on('close', r));
  console.log('frames', written, '=', (written / FPS).toFixed(2), 's');
}

ws.close();
chrome.kill();
chrome.on('close', () => rmSync(profile, { recursive: true, force: true }));
