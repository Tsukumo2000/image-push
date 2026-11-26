#!/usr/bin/env node
/**
 * postinstall — 注册 agent preset 到 DSH 的 preset 扫描目录，
 * 并把插件包的真实绝对路径注入到 skill 文件中（模型据此拼出取数命令）。
 *
 * 为什么需要：
 *   1. pnpm 安装只把包放进 node_modules；DSH 的 agent preset 通过
 *      $DSH_HOME/.agent-presets/<id>/ 被发现。命令行 pnpm add 不会自动做这一步。
 *   2. preset 被复制到 .agent-presets 后，工作目录不再是插件包根目录。
 *      所以取数脚本的绝对路径必须在安装时固化进 skill 文本。
 */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PKG_ROOT = path.resolve(HERE, '..');
const SRC = path.join(PKG_ROOT, 'config', 'agent-presets');
const DSH_HOME = process.env.DSH_HOME
  || path.join(process.env.USERPROFILE || os.homedir(), '.dsh');
const DEST_ROOT = path.join(DSH_HOME, '.agent-presets');
const PY = process.platform === 'win32' ? 'python' : 'python3';

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, e.name);
    const d = path.join(dest, e.name);
    if (e.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

function injectPaths(root) {
  const skill = path.join(root, 'skills', 'local-financial-database', 'SKILL.md');
  if (!fs.existsSync(skill)) return;
  let txt = fs.readFileSync(skill, 'utf8');
  const marker = '<!-- INSTALL_PATHS -->';
  const block = [
    marker,
    '',
    '## 本机安装路径（安装时自动生成，勿手改）',
    '',
    `- 插件包根目录 \`PLUGIN_ROOT\` = \`${PKG_ROOT}\``,
    `- 取数脚本 = \`${path.join(PKG_ROOT, 'tools', 'query_finance.py')}\``,
    `- 数据库 = \`${path.join(PKG_ROOT, 'data', 'stock.db')}\``,
    '',
    '取数命令模板：',
    '',
    '```',
    `${PY} "${path.join(PKG_ROOT, 'tools', 'query_finance.py')}" list`,
    `${PY} "${path.join(PKG_ROOT, 'tools', 'query_finance.py')}" ratio 688981 2024`,
    '```',
    '',
    marker,
  ].join('\n');
  // 替换已有的注入块，或追加到末尾
  if (txt.includes(marker)) {
    const re = new RegExp(marker + '[\\s\\S]*?' + marker);
    txt = txt.replace(re, block);
  } else {
    txt = txt.trimEnd() + '\n\n' + block + '\n';
  }
  fs.writeFileSync(skill, txt, 'utf8');
}

if (!fs.existsSync(SRC)) {
  console.log('[dsh-finance-offline] 未找到 config/agent-presets，跳过 preset 注册');
  process.exit(0);
}
for (const id of fs.readdirSync(SRC)) {
  const src = path.join(SRC, id);
  if (!fs.statSync(src).isDirectory()) continue;
  const dest = path.join(DEST_ROOT, id);
  copyDir(src, dest);
  injectPaths(dest);
  console.log(`[dsh-finance-offline] preset 已注册: ${id} -> ${dest}`);
}
console.log(`[dsh-finance-offline] PLUGIN_ROOT = ${PKG_ROOT}`);
console.log(`[dsh-finance-offline] DSH_HOME   = ${DSH_HOME}`);
