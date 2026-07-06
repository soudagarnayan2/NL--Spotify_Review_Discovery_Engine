/**
 * build.js — Vercel build script (lives inside src/frontend/)
 * Uses __dirname so the path to config.js is always correct.
 * Reads BACKEND_URL env var injected by Vercel at build time.
 */
const fs = require('fs');
const path = require('path');

const backendUrl = process.env.BACKEND_URL || 'http://localhost:8082';
const outputPath = path.join(__dirname, 'config.js');

fs.writeFileSync(outputPath, `window.BACKEND_URL = '${backendUrl}';\n`, 'utf8');
console.log('config.js written with BACKEND_URL =', backendUrl);
