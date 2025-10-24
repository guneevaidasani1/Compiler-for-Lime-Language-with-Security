// Enhanced app.js - Modern client logic for the Secure Compiler Assistant
const editor = document.getElementById('editor');
const analyzeBtn = document.getElementById('analyzeBtn');
const confSlider = document.getElementById('minConfidence');
const confVal = document.getElementById('confVal');
const optimizeChk = document.getElementById('optimize');
const runChk = document.getElementById('runProgram');
const riskBanner = document.getElementById('riskBanner');
const findingsEl = document.getElementById('findings');
const errorsEl = document.getElementById('errors');
const irEl = document.getElementById('ir');
const astEl = document.getElementById('ast');
const outputEl = document.getElementById('output');
const dlAst = document.getElementById('dlAst');
const dlIr = document.getElementById('dlIr');
const themeToggle = document.getElementById('themeToggle');
const mobileMenuToggle = document.getElementById('mobileMenuToggle');
const leftPane = document.getElementById('leftPane');
const loadingOverlay = document.getElementById('loadingOverlay');
const toastContainer = document.getElementById('toastContainer');
const lineCount = document.getElementById('lineCount');
const charCount = document.getElementById('charCount');
const particleCanvas = document.getElementById('particleCanvas');

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendChatBtn = document.getElementById('sendChatBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const expandChatBtn = document.getElementById('expandChatBtn');
const chatPanel = document.getElementById('chatPanel');
const expandIcon = document.getElementById('expandIcon');
let lastResults = null;


const GEMINI_API_KEY = 'AIzaSyD33KJwZj9CN2skx61N0cYDhz2Xa_VI6l0   ';
const GEMINI_MODEL = 'gemini-2.5-flash';
const GEMINI_URL = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${encodeURIComponent(GEMINI_API_KEY)}`;


const LIME_PRIMER = `You are an expert assistant for the Lime programming language used in this app.
Teach, answer questions, and generate Lime code. Be concise and accurate.
When you provide code, use idiomatic Lime and end statements with semicolons.

Lime Lexical/Syntax:
- Line comments: // ...
- Literals: integers (123), floats (1.23), strings ("text"), booleans true/false.
- Operators: +, -, *, /, %, ^ (power). Comparisons: <, <=, >, >=, ==, !=. Assignment: =.
- Types: int, float, str, void.

Core forms:
- Variable declaration: let name: TYPE = EXPR;
- Assignment: name = EXPR;
- Function: fn name(param1: TYPE, param2: TYPE) -> RETTYPE { STATEMENTS }
  - return EXPR; inside function.
- Conditionals: if CONDITION { ... } else { ... }
- Loops: while CONDITION { ... }
- For loop: for (let i: int = 0; i < N; i = i + 1) { ... }
- Function call: ident(arg1, arg2);
- Import file: import "path";
- Grouping with ( ) and blocks with { }.

Alternate aliases supported by the compiler (map to real tokens):
- lit -> let, bruh -> fn, pause -> return, sus -> if, imposter -> else,
  wee -> while, yeet -> break, anothaone -> continue, dab -> for, gib -> import,
  be -> =, rn -> ;, 3--D -> ->

Conventions and examples:
- Printing uses printf("%s\\n", value); prefer constant format strings.
- Example program:
  fn greet(name: str) -> void {
      printf("Hello, %s\\n", name);
  }
  fn add(a: int, b: int) -> int {
      return a + b;
  }
  fn main() -> int {
      let x: int = 2;
      let y: int = 3;
      let z: int = add(x, y);
      if z > 4 { printf("big\\n"); } else { printf("small\\n"); }
      for (let i: int = 0; i < 3; i = i + 1) { printf("%s\\n", "loop"); }
      return 0;
  }

Assistant behavior:
- Explain Lime syntax and semantics clearly.
- Provide step-by-step reasoning when asked; otherwise keep it short.
- When a user pastes Lime, identify errors with exact fixes and secure patterns.
`;

let currentTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', currentTheme);

if (themeToggle) {
  themeToggle.innerHTML = `<span class="theme-icon">${currentTheme === 'dark' ? '☀️' : '🌙'}</span>`;
  themeToggle.setAttribute('aria-label', `Switch to ${currentTheme === 'dark' ? 'light' : 'dark'} theme`);
  
  themeToggle.addEventListener('click', () => {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    themeToggle.innerHTML = `<span class="theme-icon">${currentTheme === 'dark' ? '☀️' : '🌙'}</span>`;
    themeToggle.setAttribute('aria-label', `Switch to ${currentTheme === 'dark' ? 'light' : 'dark'} theme`);
    showToast(`Switched to ${currentTheme} theme`, 'success');
  });
}


if (mobileMenuToggle && leftPane) {
  mobileMenuToggle.addEventListener('click', () => {
    mobileMenuToggle.classList.toggle('active');
    leftPane.classList.toggle('mobile-open');
  });
}


function attachTilt(selector, opts = { maxTilt: 6, translate: 6 }) {
  document.querySelectorAll(selector).forEach(el => {
    el.classList.add('tiltable');
    const maxT = opts.maxTilt, maxTr = opts.translate;
    function onMove(e) {
      const rect = el.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width - 0.5;
      const py = (e.clientY - rect.top) / rect.height - 0.5;
      el.style.setProperty('--tiltX', `${(-py * maxT).toFixed(2)}deg`);
      el.style.setProperty('--tiltY', `${(px * maxT).toFixed(2)}deg`);
      el.style.setProperty('--tx', `${(px * maxTr).toFixed(1)}px`);
      el.style.setProperty('--ty', `${(py * maxTr).toFixed(1)}px`);
    }
    function onLeave() {
      el.style.setProperty('--tiltX', '0deg');
      el.style.setProperty('--tiltY', '0deg');
      el.style.setProperty('--tx', '0px');
      el.style.setProperty('--ty', '0px');
    }
    el.addEventListener('mousemove', onMove);
    el.addEventListener('mouseleave', onLeave);
  });
}
attachTilt('.editor-card, .panel, .finding', { maxTilt: 5, translate: 4 });
attachTilt('.analyze-btn', { maxTilt: 4, translate: 3 });
attachTilt('.pill', { maxTilt: 4, translate: 2 });


function showToast(message, type = 'info', duration = 3000) {
  if (!toastContainer) return;
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.5rem;">
      <span style="font-size: 1.2rem;">${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>
      <span>${message}</span>
    </div>
  `;
  
  toastContainer.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 300ms ease forwards';
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }, duration);
}


let autoSaveTimeout;
function updateEditorStats() {
  if (!editor || !lineCount || !charCount) return;
  
  const text = editor.value;
  const lines = text.split('\n').length;
  const chars = text.length;
  
  lineCount.textContent = `Lines: ${lines}`;
  charCount.textContent = `Characters: ${chars}`;
  
  // Auto-save to localStorage
  clearTimeout(autoSaveTimeout);
  autoSaveTimeout = setTimeout(() => {
    localStorage.setItem('editor-content', text);
  }, 1000);
}

// Add pulse on analyze click (visual only)
if (analyzeBtn) {
  analyzeBtn.addEventListener('click', () => {
    analyzeBtn.classList.remove('pulse');
    // reflow to restart animation
    void analyzeBtn.offsetWidth;
    analyzeBtn.classList.add('pulse');
  });
}

// Load saved content
if (editor) {
  const saved = localStorage.getItem('editor-content');
  if (saved && !editor.value) {
    editor.value = saved;
  }
  
  editor.addEventListener('input', updateEditorStats);
  editor.addEventListener('keydown', handleEditorKeyboard);
  updateEditorStats();
}

// Enhanced keyboard shortcuts
function handleEditorKeyboard(e) {
  // Ctrl/Cmd + S to analyze
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    if (analyzeBtn && !analyzeBtn.disabled) {
      analyzeBtn.click();
    }
  }
  
  // Tab handling for better indentation
  if (e.key === 'Tab') {
    e.preventDefault();
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    const value = editor.value;
    
    if (e.shiftKey) {
      // Shift+Tab: unindent
      const lines = value.substring(0, start).split('\n');
      const currentLine = lines[lines.length - 1];
      if (currentLine.startsWith('  ')) {
        const newStart = start - 2;
        editor.value = value.substring(0, newStart) + value.substring(start);
        editor.selectionStart = editor.selectionEnd = newStart;
      }
    } else {
      // Tab: indent
      editor.value = value.substring(0, start) + '  ' + value.substring(end);
      editor.selectionStart = editor.selectionEnd = start + 2;
    }
    updateEditorStats();
  }
}

confSlider.addEventListener('input', () => {
  confVal.textContent = Number(confSlider.value).toFixed(2);
});

// Copy output
const copyOutputBtn = document.getElementById('copyOutput');
if (copyOutputBtn) {
  copyOutputBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(outputEl ? outputEl.textContent : '');
      showToast('Output copied to clipboard', 'success');
    } catch (e) {
      showToast('Copy failed', 'error');
    }
  });
}
// Initialize confidence value on load
if (confSlider && confVal) {
  confVal.textContent = Number(confSlider.value).toFixed(2);
}

// Animated particle background (subtle)
(function initParticles(){
  if (!particleCanvas) return;
  const ctx = particleCanvas.getContext('2d');
  const state = { dpr: Math.min(window.devicePixelRatio || 1, 2), w: 0, h: 0, parts: [], mouse: { x: 0, y: 0 } };
  const MAX = 80, LINK_DIST = 120;
  function resize(){
    const rect = particleCanvas.getBoundingClientRect();
    state.w = Math.floor(rect.width);
    state.h = Math.floor(rect.height);
    const dpr = state.dpr;
    particleCanvas.width = Math.max(1, Math.floor(state.w * dpr));
    particleCanvas.height = Math.max(1, Math.floor(state.h * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!state.parts.length) {
      for (let i=0;i<MAX;i++) state.parts.push(spawn());
    }
  }
  function rand(a,b){ return a + Math.random()*(b-a); }
  function spawn(){
    return { x: rand(0, state.w), y: rand(0, state.h), vx: rand(-0.2,0.2), vy: rand(-0.2,0.2), r: rand(0.8,1.8) };
  }
  function step(){
    ctx.clearRect(0,0,state.w,state.h);
    const hue = 224; // indigo-ish
    for (let i=0;i<state.parts.length;i++){
      const p = state.parts[i];
      // gentle mouse parallax
      p.vx += (state.mouse.x - state.w/2) * 0.000002;
      p.vy += (state.mouse.y - state.h/2) * 0.000002;
      p.x += p.vx; p.y += p.vy;
      if (p.x < -10 || p.x > state.w+10 || p.y < -10 || p.y > state.h+10){ state.parts[i] = spawn(); continue; }
      ctx.fillStyle = `rgba(255,255,255,0.12)`;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2); ctx.fill();
    }
    // links
    ctx.strokeStyle = 'rgba(90,122,255,0.10)';
    for (let i=0;i<state.parts.length;i++){
      const a = state.parts[i];
      for (let j=i+1;j<state.parts.length;j++){
        const b = state.parts[j];
        const dx=a.x-b.x, dy=a.y-b.y, d=Math.hypot(dx,dy);
        if (d<LINK_DIST){
          ctx.globalAlpha = 1 - d/LINK_DIST;
          ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(step);
  }
  resize(); step();
  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', (e)=>{ state.mouse.x = e.clientX; state.mouse.y = e.clientY; });
  // Re-paint after theme change
  if (themeToggle) themeToggle.addEventListener('click', ()=> setTimeout(resize, 50));
})();

// Sample Lime programs (aligned with your grammar)
const samples = {
  overflow: `// Lime sample (illustrative): tight loop without guard can hint at resource issues
fn main() -> int {
    let n: int = 1;
    while (n < 1000000) {
        n = n + 1;
    }
    printf("Done\\n");
    return 0;
}
`,
  fmt: `// Format String vulnerability: user input as format string
fn main() -> int {
    let user_input: str = "admin";
    printf(user_input);
    return 0;
}
`,
  concat: `// Injection-like concatenation pattern (modeled)
fn main() -> int {
    let table: str = "users";
    let name: str = "bob";
    // Building a query-like string (for AI pattern demo)
    printf("%s\\n", table);
    printf(name);
    return 0;
}
`,
  cmd: `// Command-like call representation (pattern demo)
fn main() -> int {
    let cmd: str = "ls -la";
    printf(cmd);
    return 0;
}
`,
  secure: `// Secure: constant format string + parameterization
fn main() -> int {
    let user_input: str = "world";
    printf("%s\\n", user_input);
    return 0;
}
`
};

// Load a default sample
editor.value = samples.fmt;

// Hook up pill buttons
Array.from(document.querySelectorAll('.pill')).forEach(btn => {
  btn.addEventListener('click', () => {
    const key = btn.getAttribute('data-sample');
    editor.value = samples[key] || '';
    updateEditorStats();
    clearOutputs();
  });
});

function setBanner(state, title, sub) {
  riskBanner.classList.remove('neutral', 'low', 'med', 'high');
  riskBanner.classList.add(state);
  riskBanner.querySelector('.risk-title').textContent = title;
  riskBanner.querySelector('.risk-sub').textContent = sub;
}

function clearOutputs() {
  setBanner('neutral', 'Awaiting Analysis', 'Click "Compile & Analyze" to see results.');
  findingsEl.innerHTML = '';
  errorsEl.textContent = '';
  irEl.textContent = '';
  if (astEl) astEl.textContent = '';
  dlAst.classList.add('disabled');
  dlAst.href = '#';
  dlIr.classList.add('disabled');
  dlIr.href = '#';
  if (outputEl) outputEl.textContent = '';
}

analyzeBtn.addEventListener('click', async () => {
  clearOutputs();
  setBanner('neutral', 'Analyzing...', 'Running lexer, parser, compiler and AI checks...');
  if (analyzeBtn) {
    analyzeBtn.disabled = true;
    analyzeBtn.classList.add('loading');
  }
  if (loadingOverlay) loadingOverlay.classList.add('active');

  const payload = {
    code: editor.value,
    minConfidence: Number(confSlider.value),
    optimize: !!optimizeChk.checked,
    securityLevel: 'strict',
    // If the checkbox is missing (cached HTML), default to true so execution still happens
    run: (runChk ? !!runChk.checked : true)
  };

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    lastResults = data || null;
    renderResults(data);
    showToast('Analysis completed', 'success');
  } catch (e) {
    setBanner('high', 'Request Failed', 'Could not reach the analysis service.');
    errorsEl.textContent = String(e);
    showToast('Request failed', 'error');
  } finally {
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
      analyzeBtn.classList.remove('loading');
    }
    if (loadingOverlay) loadingOverlay.classList.remove('active');
  }
});

function renderResults(data) {
  if (!data || data.ok === false) {
    setBanner('high', 'Analysis Error', data && data.error ? data.error : 'Unknown error');
    return;
  }

  const parseErrs = data.parseErrors || [];
  const compErrs = data.compileErrors || [];
  const allErrs = [];
  if (parseErrs.length) {
    allErrs.push('PARSER ERRORS:');
    parseErrs.forEach(e => allErrs.push('  - ' + e));
  }
  if (compErrs.length) {
    allErrs.push('COMPILER ERRORS:');
    compErrs.forEach(e => allErrs.push('  - ' + e));
  }
  errorsEl.textContent = allErrs.join('\n');

  // AST (pretty print if available)
  if (astEl) {
    try {
      if (data.ast) {
        const astStr = typeof data.ast === 'string' ? data.ast : JSON.stringify(data.ast, null, 2);
        astEl.textContent = astStr.slice(0, 10000);
      } else if (data.artifacts && data.artifacts.astUrl) {
        // Load AST from artifact URL for on-screen accessibility
        fetch(data.artifacts.astUrl + '&_=' + Date.now())
          .then(r => r.text())
          .then(t => { astEl.textContent = t.slice(0, 10000); })
          .catch(() => {});
      } else {
        astEl.textContent = '';
      }
    } catch (_) {
      astEl.textContent = '';
    }
  }

  // IR
  irEl.textContent = (data.ir || '').slice(0, 10000);

  // Security report
  const security = data.security || { summary: {}, findings: [] };
  const findings = security.findings || [];
  const total = findings.length;

  // Execution output
  const exec = data.execution || null;
  if (outputEl) {
    if (exec && exec.ran) {
      const lines = [];
      lines.push(`Return code: ${exec.returnCode}`);
      lines.push(`Duration: ${Number(exec.duration_ms || 0).toFixed(2)} ms`);
      if (exec.stdout) {
        lines.push('--- stdout ---');
        lines.push(exec.stdout);
      }
      if (exec.error) {
        lines.push('--- note ---');
        lines.push(exec.error);
      }
      outputEl.textContent = lines.join('\n');
    } else if (data.blocked) {
      outputEl.textContent = 'Execution blocked due to security findings (strict mode).';
    } else if (data.parseErrors && data.parseErrors.length) {
      outputEl.textContent = 'Not executed due to parse errors.';
    } else {
      outputEl.textContent = 'Not executed.';
    }
  }

  // Enable downloads if artifacts available
  const artifacts = data.artifacts || {};
  if (artifacts.astAvailable && artifacts.astUrl) {
    dlAst.classList.remove('disabled');
    dlAst.href = artifacts.astUrl + '&_=' + Date.now();
  }
  if (artifacts.irAvailable && artifacts.irUrl) {
    dlIr.classList.remove('disabled');
    dlIr.href = artifacts.irUrl + '&_=' + Date.now();
  }
  let sevClass = 'low';
  let title = 'No Vulnerabilities Found';
  let sub = 'Your code appears safe under current rules.';

  const hasCritical = findings.some(f => f.severity === 'CRITICAL');
  const hasHigh = findings.some(f => f.severity === 'HIGH');
  const hasMedium = findings.some(f => f.severity === 'MEDIUM');

  if (hasCritical || hasHigh) {
    sevClass = 'high';
    title = `${total} Vulnerabilit${total === 1 ? 'y' : 'ies'} Found`;
    sub = 'Critical/High issues detected. Compilation would be blocked (strict).';
  } else if (hasMedium) {
    sevClass = 'med';
    title = `${total} Vulnerabilit${total === 1 ? 'y' : 'ies'} Found`;
    sub = 'Medium risk issues detected. Review recommended.';
  } else if (total > 0) {
    sevClass = 'low';
    title = `${total} Low-risk Finding${total === 1 ? '' : 's'}`;
    sub = 'Consider applying suggested mitigations.';
  } else {
    sevClass = 'low';
    title = 'No Vulnerabilities Found';
    sub = 'Security checks passed.';
  }
  setBanner(sevClass, title, sub);

  // Render findings
  findingsEl.innerHTML = findings.map(f => findingCard(f)).join('');
  // Re-attach tilt for dynamically inserted findings
  attachTilt('.finding', { maxTilt: 5, translate: 4 });
}

function findingCard(f) {
  const sev = (f.severity || 'LOW').toLowerCase();
  return `
    <div class="finding">
      <div class="row">
        <span class="badge ${sev}">${f.severity || 'LOW'}</span>
        <strong>${escapeHtml(f.description || f.type || 'Finding')}</strong>
        <span class="small-note">(Confidence: ${Number(f.confidence ?? 0).toFixed(2)}, CWE: ${escapeHtml(f.cwe_id || '—')})</span>
      </div>
      <div class="location">${escapeHtml(f.location || 'Unknown location')}</div>
      <div class="small-note">${escapeHtml(f.explanation || '')}</div>
      <div class="small-note">Risk: ${escapeHtml(f.risk_impact || '')}</div>
      <div class="small-note">Fix: ${escapeHtml(f.fix_suggestion || '')}</div>
      ${f.code_example ? `<pre class="code-example">${escapeHtml(f.code_example)}</pre>` : ''}
    </div>
  `;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// ========== Extra UI behaviors ==========
// Clear editor
const clearBtn = document.getElementById('clearBtn');
if (clearBtn) {
  clearBtn.addEventListener('click', () => {
    if (!editor) return;
    editor.value = '';
    updateEditorStats();
    clearOutputs();
    showToast('Editor cleared', 'info');
  });
}

// Simple formatter: trim trailing spaces and normalize indentation (basic)
const formatBtn = document.getElementById('formatBtn');
if (formatBtn) {
  formatBtn.addEventListener('click', () => {
    if (!editor) return;
    const formatted = editor.value
      .split('\n')
      .map(line => line.replace(/\s+$/g, ''))
      .join('\n')
      .trim() + '\n';
    editor.value = formatted;
    updateEditorStats();
    showToast('Formatted code', 'success');
  });
}

// Copy AST to clipboard
const copyAstBtn = document.getElementById('copyAst');
if (copyAstBtn) {
  copyAstBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(astEl ? astEl.textContent : '');
      showToast('AST copied to clipboard', 'success');
    } catch (e) {
      showToast('Copy failed', 'error');
    }
  });
}

// Copy IR to clipboard
const copyIrBtn = document.getElementById('copyIr');
if (copyIrBtn) {
  copyIrBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(irEl.textContent || '');
      showToast('IR copied to clipboard', 'success');
    } catch (e) {
      showToast('Copy failed', 'error');
    }
  });
}

// Export findings as JSON
const exportBtn = document.getElementById('exportFindings');
if (exportBtn) {
  exportBtn.addEventListener('click', () => {
    const findings = (lastResults && lastResults.security && lastResults.security.findings) || [];
    const summary = (lastResults && lastResults.security && lastResults.security.summary) || {};
    const exportData = { summary, findings };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `security_findings_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Findings exported', 'success');
  });
}

// Panel collapse toggles
document.querySelectorAll('.panel .panel-toggle').forEach(btn => {
  btn.addEventListener('click', () => {
    const panel = btn.closest('.panel');
    if (!panel) return;
    panel.classList.toggle('collapsed');
    const icon = btn.querySelector('.toggle-icon');
    if (icon) icon.textContent = panel.classList.contains('collapsed') ? '►' : '▼';
  });
});

// ========== Simple Gemini Chatbot ==========
const chatHistory = [];
// Seed conversation with the Lime primer once per session
if (!sessionStorage.getItem('limePrimerSeeded')) {
  chatHistory.push({ role: 'user', parts: [{ text: LIME_PRIMER }] });
  sessionStorage.setItem('limePrimerSeeded', '1');
}

// Simple markdown parser for bot responses
function parseMarkdown(text) {
  return text
    // Code blocks ```code```
    .replace(/```([\s\S]*?)```/g, '<pre style="background:rgba(255,255,255,0.1);padding:0.5rem;border-radius:4px;margin:0.5rem 0;overflow-x:auto;"><code>$1</code></pre>')
    // Inline code `code`
    .replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">$1</code>')
    // Bold **text**
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic *text*
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Line breaks
    .replace(/\n/g, '<br>');
}

function appendChat(role, text) {
  if (!chatMessages) return;
  const who = role === 'user' ? 'You' : 'Assistant';
  const color = role === 'user' ? '#9ae6b4' : '#c3dafe';
  const block = document.createElement('div');
  block.style.margin = '0.5rem 0';
  block.style.padding = '0.5rem';
  block.style.borderLeft = `3px solid ${color}`;
  block.style.backgroundColor = 'rgba(255,255,255,0.02)';
  block.style.borderRadius = '4px';
  
  const content = role === 'user' ? escapeHtml(text) : parseMarkdown(escapeHtml(text));
  block.innerHTML = `<strong style="color:${color};margin-bottom:0.25rem;display:block;">${who}:</strong><div>${content}</div>`;
  
  chatMessages.appendChild(block);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendChat() {
  if (!chatInput || !sendChatBtn) return;
  const userMsg = chatInput.value.trim();
  if (!userMsg) return;

  // Include editor content to ground answers in your current Lime code
  const ctx = editor && editor.value ? `\n\nContext (current Lime code):\n${editor.value.slice(0, 4000)}` : '';
  const prompt = `${userMsg}${ctx}`;

  appendChat('user', userMsg);
  chatHistory.push({ role: 'user', parts: [{ text: prompt }] });
  chatInput.value = '';
  sendChatBtn.disabled = true;
  sendChatBtn.textContent = 'Sending...';
  try {
    const res = await fetch(GEMINI_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents: chatHistory })
    });
    const data = await res.json();
    const parts = (((data || {}).candidates || [])[0] || {}).content?.parts || [];
    const text = parts.map(p => p && p.text ? p.text : '').join('') || 'No response';
    chatHistory.push({ role: 'model', parts: [{ text }] });
    appendChat('model', text);
  } catch (e) {
    showToast('Chat request failed', 'error');
  } finally {
    sendChatBtn.disabled = false;
    sendChatBtn.textContent = 'Send';
  }
}

if (sendChatBtn && chatInput) {
  sendChatBtn.addEventListener('click', sendChat);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
  });
}

// Clear chat history
if (clearChatBtn) {
  clearChatBtn.addEventListener('click', () => {
    if (chatMessages) chatMessages.innerHTML = '';
    chatHistory.length = 0;
    sessionStorage.removeItem('limePrimerSeeded');
    chatHistory.push({ role: 'user', parts: [{ text: LIME_PRIMER }] });
    sessionStorage.setItem('limePrimerSeeded', '1');
    showToast('Chat cleared', 'success');
  });
}

// Expand/restore chat panel
if (expandChatBtn && chatPanel) {
  expandChatBtn.addEventListener('click', () => {
    chatPanel.classList.toggle('expanded');
    if (expandIcon) expandIcon.textContent = chatPanel.classList.contains('expanded') ? '⤡' : '⤢';
  });
}
