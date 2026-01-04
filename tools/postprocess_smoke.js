#!/usr/bin/env node
/**
 * Smoke test for UI postprocessing stability.
 *
 * Goals:
 * - Ensure Word→txt→parse→UI formatter does "hậu kỳ" (break long blobs, split inline lists).
 * - Catch regressions that cause unreadable run-on paragraphs or broken numbering.
 *
 * Usage:
 *   node UI\\ GLM/tools/postprocess_smoke.js
 *   FULL_DATA_JS=UI\\ GLM/full_data.js node UI\\ GLM/tools/postprocess_smoke.js
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ContentFormatter = require(path.join(__dirname, '..', 'scripts', 'content_formatter.js'));

function loadFullData(fullDataPath) {
  const code = fs.readFileSync(fullDataPath, 'utf8');
  const sandbox = { FULL_DATA: undefined, console: console };
  vm.createContext(sandbox);
  vm.runInContext(code + '\n;this.__FULL_DATA__ = FULL_DATA;', sandbox, { filename: fullDataPath });
  const data = sandbox.__FULL_DATA__;
  if (!data || typeof data !== 'object') throw new Error('FULL_DATA not found / invalid');
  return data;
}

function stripTags(html) {
  return String(html || '').replace(/<[^>]*>/g, '');
}

function maxRunOnParagraphLen(plain) {
  const paras = String(plain || '')
    .split(/\n{2,}/g)
    .map((p) => p.trim())
    .filter(Boolean);
  let maxLen = 0;
  for (const p of paras) {
    if (!p.includes('\n')) maxLen = Math.max(maxLen, p.length);
  }
  return maxLen;
}

function hasInlineNumberedListBlob(plain) {
  // Detect "1. ... 2. ... 3. ..." on the same line.
  const lines = String(plain || '').split('\n').map((l) => l.trim());
  for (const l of lines) {
    if (l.length < 80) continue;
    if (/\b1\.\s+.+\b2\.\s+.+\b3\.\s+/i.test(l)) return true;
  }
  return false;
}

function isHeadBulleted(plain, head) {
  const lines = String(plain || '')
    .split('\n')
    .map((l) => l.replace(/\s+/g, ' ').trim())
    .filter(Boolean);

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    if (!line.startsWith(`${head}:`)) continue;
    // Look around for a bullet marker rendered by the formatter.
    for (let j = Math.max(0, i - 4); j <= Math.min(lines.length - 1, i + 1); j += 1) {
      const near = lines[j];
      if (near === '•' || near.startsWith('• ') || near.startsWith('- ') || near.startsWith('•')) {
        return true;
      }
    }
    return false;
  }
  return true; // head not present as a standalone line
}

function run() {
  const fullDataPath =
    process.env.FULL_DATA_JS ||
    path.join(__dirname, '..', 'full_data.js');

  const data = loadFullData(fullDataPath);
  const formatter = new ContentFormatter();

  const failures = [];
  const stats = { sections: 0 };

  for (const [indexKey, indexData] of Object.entries(data)) {
    const sections = (indexData && Array.isArray(indexData.sections)) ? indexData.sections : [];
    for (let i = 0; i < sections.length; i += 1) {
      const sec = sections[i];
      const raw = String(sec && sec.content ? sec.content : '');
      if (!raw) continue;

      const formattedHtml = formatter.format(raw);
      const plain = stripTags(formattedHtml).replace(/\s+\n/g, '\n');

      stats.sections += 1;

      const maxLen = maxRunOnParagraphLen(plain);
      if (maxLen > 520) {
        failures.push({
          indexKey,
          title: (sec && sec.title) ? String(sec.title) : '',
          type: 'run_on_paragraph',
          detail: `max paragraph length=${maxLen}`,
        });
      }

      if (hasInlineNumberedListBlob(plain)) {
        failures.push({
          indexKey,
          title: (sec && sec.title) ? String(sec.title) : '',
          type: 'inline_numbered_list',
          detail: 'found 1./2./3. on same line',
        });
      }

      // Ensure common "heads" become bullets when present.
      const heads = ['Độ rộng', 'Dòng tiền', 'Điểm nhấn', 'Thanh khoản', 'Sức mạnh'];
      for (const h of heads) {
        if (plain.includes(`${h}:`) && !isHeadBulleted(plain, h)) {
          failures.push({
            indexKey,
            title: (sec && sec.title) ? String(sec.title) : '',
            type: 'head_not_bulleted',
            detail: `found "${h}:" but not as bullet`,
          });
          break;
        }
      }
    }
  }

  if (failures.length) {
    console.error(`❌ Postprocess smoke FAILED (${failures.length} issues across ${stats.sections} sections)`);
    for (const f of failures.slice(0, 30)) {
      console.error(`- [${f.indexKey}] ${f.title} :: ${f.type} (${f.detail})`);
    }
    if (failures.length > 30) console.error(`… and ${failures.length - 30} more`);
    process.exit(2);
  }

  console.log(`✅ Postprocess smoke OK (${stats.sections} sections checked)`);
}

run();
