// Gita AI Guide - Client Application Logic with Bhagavad Gita RAG

localStorage.setItem('gita_model', 'gemini-3.6-flash');

const state = {
  messages: [],
  isStreaming: false,
  apiKey: localStorage.getItem('gita_gemini_api_key') || '',
  model: 'gemini-3.6-flash',
  hasServerKey: true,
  speakingUtterance: null,
  searchDebounceTimer: null
};

// Elements
const chatContainer = document.getElementById('chatContainer');
const welcomeHero = document.getElementById('welcomeHero');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const apiKeyInput = document.getElementById('apiKeyInput');
const modelSelect = document.getElementById('modelSelect');
const keyStatusBadge = document.getElementById('keyStatusBadge');

// Search Modal Elements
const searchVerseBtn = document.getElementById('searchVerseBtn');
const searchModal = document.getElementById('searchModal');
const closeSearchBtn = document.getElementById('closeSearchBtn');
const verseSearchInput = document.getElementById('verseSearchInput');
const verseSearchResults = document.getElementById('verseSearchResults');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  setupAutoResize();
  setupSearchModal();
  await checkServerConfig();
});

// Check Server Config
async function checkServerConfig() {
  state.hasServerKey = true;
  state.model = 'gemini-3.6-flash';
  updateKeyStatusIndicator();

  try {
    const res = await fetch('/api/config');
    if (res.ok && res.headers.get('content-type')?.includes('json')) {
      const data = await res.json();
      if (typeof data.hasServerKey === 'boolean') {
        state.hasServerKey = data.hasServerKey;
      }
      if (data.defaultModel) {
        state.model = data.defaultModel;
      }
      updateKeyStatusIndicator();
    }
  } catch (e) {
    // Keep defaults
  }
}

function updateKeyStatusIndicator() {
  if (state.apiKey) {
    keyStatusBadge.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/60">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Custom Key Active
    </span>`;
  } else if (state.hasServerKey) {
    keyStatusBadge.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-950/80 text-amber-300 border border-amber-800/60">
      <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Server Key Connected
    </span>`;
  } else {
    keyStatusBadge.innerHTML = `<button onclick="openSettings()" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-950/80 text-rose-300 border border-rose-800/60 hover:bg-rose-900/80 transition">
      <span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span> Set Gemini API Key
    </button>`;
  }
}

// Event Listeners
function setupEventListeners() {
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSubmit();
  });

  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  });

  clearChatBtn.addEventListener('click', () => {
    if (confirm('Start a new session with Gita AI Guide?')) {
      resetChat();
    }
  });

  settingsBtn.addEventListener('click', openSettings);
  closeSettingsBtn.addEventListener('click', closeSettings);
  saveSettingsBtn.addEventListener('click', saveSettings);

  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) closeSettings();
  });

  // Prompt chips
  document.querySelectorAll('.prompt-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        userInput.value = prompt;
        handleSubmit();
      }
    });
  });
}

// Scripture Explorer Modal Logic
function setupSearchModal() {
  if (searchVerseBtn) searchVerseBtn.addEventListener('click', openSearchModal);
  if (closeSearchBtn) closeSearchBtn.addEventListener('click', closeSearchModal);

  if (searchModal) {
    searchModal.addEventListener('click', (e) => {
      if (e.target === searchModal) closeSearchModal();
    });
  }

  if (verseSearchInput) {
    verseSearchInput.addEventListener('input', () => {
      clearTimeout(state.searchDebounceTimer);
      const q = verseSearchInput.value.trim();
      if (!q) {
        verseSearchResults.innerHTML = `
          <div class="text-center py-8 text-gray-400 text-xs">
            Type a concept, dilemma, or chapter/verse reference above to retrieve verses.
          </div>`;
        return;
      }
      state.searchDebounceTimer = setTimeout(() => executeVerseSearch(q), 300);
    });

    verseSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        clearTimeout(state.searchDebounceTimer);
        const q = verseSearchInput.value.trim();
        if (q) executeVerseSearch(q);
      }
    });
  }

  document.querySelectorAll('.search-quick-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const query = chip.getAttribute('data-q');
      if (query && verseSearchInput) {
        verseSearchInput.value = query;
        executeVerseSearch(query);
      }
    });
  });
}

function openSearchModal() {
  searchModal.classList.remove('hidden');
  setTimeout(() => verseSearchInput?.focus(), 50);
}

function closeSearchModal() {
  searchModal.classList.add('hidden');
}

async function executeVerseSearch(query) {
  if (!verseSearchResults) return;
  verseSearchResults.innerHTML = `
    <div class="text-center py-6 text-amber-400/80 text-xs flex items-center justify-center gap-2">
      <span class="animate-spin text-sm">🕉</span> Searching sacred verses via RAG...
    </div>`;

  try {
    const res = await fetch(`/api/verses/search?q=${encodeURIComponent(query)}&limit=6`, {
      headers: state.apiKey ? { 'Authorization': `Bearer ${state.apiKey}` } : {}
    });
    if (!res.ok) throw new Error('Search failed');
    const data = await res.json();
    const verses = data.verses || [];

    if (verses.length === 0) {
      verseSearchResults.innerHTML = `
        <div class="text-center py-8 text-gray-400 text-xs">
          No verses found matching "${escapeHtml(query)}". Try another topic or reference (e.g. 2.47).
        </div>`;
      return;
    }

    let html = '';
    verses.forEach((v) => {
      const scoreBadge = v.match_type === 'exact_reference'
        ? `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Exact Reference</span>`
        : `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/25">${Math.round(v.score * 100)}% Match</span>`;

      html += `
        <div class="p-3.5 rounded-xl glass-panel border border-amber-500/20 hover:border-amber-500/50 transition space-y-2">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="font-cinzel text-xs font-bold text-amber-300">${escapeHtml(v.reference)}</span>
              <span class="text-[11px] text-gray-400">· ${escapeHtml(v.chapter_name || '')}</span>
            </div>
            ${scoreBadge}
          </div>

          <div class="font-sanskrit text-sm text-amber-100 whitespace-pre-line leading-relaxed bg-black/20 p-2.5 rounded-lg border border-amber-500/10">
            ${escapeHtml(v.slok)}
          </div>

          <div class="text-xs text-amber-300/80 italic font-mono text-[11px]">
            ${escapeHtml(v.transliteration)}
          </div>

          <p class="text-xs text-gray-200 leading-relaxed">
            <strong class="text-amber-300 font-medium">Translation:</strong> ${escapeHtml(v.translation_en)}
          </p>

          <div class="flex items-center justify-between pt-2 border-t border-gray-800/80">
            <button onclick="askAboutVerse('${escapeHtml(v.reference)}')" class="text-xs text-amber-400 hover:text-amber-300 hover:underline inline-flex items-center gap-1 font-medium">
              <span>✦</span> Ask Mayank for guidance on this verse
            </button>
            <button onclick="toggleSpeech('${escapeHtml(v.translation_en)}', this)" class="p-1 rounded text-gray-400 hover:text-amber-300 text-xs transition" title="Listen">
              🔊
            </button>
          </div>
        </div>
      `;
    });

    verseSearchResults.innerHTML = html;
  } catch (err) {
    verseSearchResults.innerHTML = `
      <div class="text-center py-6 text-rose-400 text-xs">
        Failed to search verses: ${escapeHtml(err.message)}
      </div>`;
  }
}

window.askAboutVerse = function(ref) {
  closeSearchModal();
  userInput.value = `Explain the practical guidance and wisdom of ${ref} for my modern life.`;
  handleSubmit();
};

function openSettings() {
  apiKeyInput.value = state.apiKey;
  modelSelect.value = state.model;
  settingsModal.classList.remove('hidden');
}

function closeSettings() {
  settingsModal.classList.add('hidden');
}

function saveSettings() {
  const newKey = apiKeyInput.value.trim();
  const newModel = modelSelect.value;
  state.apiKey = newKey;
  state.model = newModel;

  if (newKey) {
    localStorage.setItem('gita_gemini_api_key', newKey);
  } else {
    localStorage.removeItem('gita_gemini_api_key');
  }
  localStorage.setItem('gita_model', newModel);

  updateKeyStatusIndicator();
  closeSettings();
  showToast('Settings saved successfully!');
}

function resetChat() {
  state.messages = [];
  window.speechSynthesis?.cancel();
  chatContainer.innerHTML = '';
  welcomeHero.classList.remove('hidden');
}

function setupAutoResize() {
  userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 180) + 'px';
  });
}

// Main Submit Flow
async function handleSubmit() {
  const text = userInput.value.trim();
  if (!text || state.isStreaming) return;

  welcomeHero.classList.add('hidden');

  appendUserMessage(text);
  userInput.value = '';
  userInput.style.height = 'auto';

  const historyPayload = state.messages.map(m => ({ role: m.role, content: m.content }));

  const assistantMsgEl = createAssistantMessageElement();
  chatContainer.appendChild(assistantMsgEl);
  scrollToBottom();

  const contentArea = assistantMsgEl.querySelector('.response-content');
  contentArea.classList.add('typing-cursor');
  let rawAccumulated = '';
  let retrievedVerses = [];

  state.isStreaming = true;
  setControlsDisabled(true);

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(state.apiKey ? { 'Authorization': `Bearer ${state.apiKey}` } : {})
      },
      body: JSON.stringify({
        message: text,
        history: historyPayload,
        apiKey: state.apiKey || undefined,
        model: state.model,
        stream: true
      })
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: 'Request failed.' }));
      throw new Error(errData.detail || `Server error: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.replace('data: ', '').trim();
          if (!jsonStr) continue;

          let data;
          try {
            data = JSON.parse(jsonStr);
          } catch (pe) {
            console.error('Error parsing SSE JSON:', pe, jsonStr);
            continue;
          }

          if (data.type === 'rag') {
            retrievedVerses = data.verses || [];
            renderRagVerses(assistantMsgEl, retrievedVerses);
            scrollToBottom();
          } else if (data.type === 'chunk') {
            rawAccumulated += data.content;
            contentArea.innerHTML = formatIntermediateStreaming(rawAccumulated);
            scrollToBottom();
          } else if (data.type === 'error') {
            throw new Error(data.error);
          } else if (data.type === 'done') {
            break;
          }
        }
      }
    }

    if (!rawAccumulated.trim()) {
      throw new Error("No response received from the model. Please check the model name and API key in Settings.");
    }

    contentArea.classList.remove('typing-cursor');
    renderStructuredWisdom(assistantMsgEl, rawAccumulated, retrievedVerses);

    state.messages.push({ role: 'user', content: text });
    state.messages.push({ role: 'assistant', content: rawAccumulated });

  } catch (error) {
    contentArea.classList.remove('typing-cursor');
    contentArea.innerHTML = `
      <div class="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200">
        <div class="flex items-center gap-2 font-semibold mb-1 text-rose-300">
          <svg class="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          Guidance Unavailable
        </div>
        <p class="text-sm">${escapeHtml(error.message)}</p>
        <button onclick="openSettings()" class="mt-3 px-3 py-1.5 text-xs rounded-lg bg-rose-900/60 hover:bg-rose-800/80 border border-rose-700/50 text-white transition inline-flex items-center gap-1.5">
          Configure API Key in Settings
        </button>
      </div>
    `;
  } finally {
    state.isStreaming = false;
    setControlsDisabled(false);
    scrollToBottom();
  }
}

// UI Append Helpers
function appendUserMessage(text) {
  const msgEl = document.createElement('div');
  msgEl.className = 'flex justify-end items-start gap-3 message-enter';
  msgEl.innerHTML = `
    <div class="max-w-[85%] md:max-w-[70%] rounded-2xl rounded-tr-none px-5 py-3.5 bg-gradient-to-r from-amber-600 to-amber-700 text-white shadow-lg border border-amber-500/30">
      <div class="text-xs text-amber-200 font-semibold mb-1 tracking-wide uppercase">You</div>
      <p class="text-sm md:text-base leading-relaxed whitespace-pre-wrap">${escapeHtml(text)}</p>
    </div>
    <div class="w-9 h-9 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300 text-sm font-semibold shrink-0">
      👤
    </div>
  `;
  chatContainer.appendChild(msgEl);
}

function createAssistantMessageElement() {
  const msgEl = document.createElement('div');
  msgEl.className = 'flex items-start gap-3 message-enter w-full';
  msgEl.innerHTML = `
    <div class="w-9 h-9 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white text-base font-cinzel shrink-0 shadow-md lotus-pulse">
      🕉
    </div>
    <div class="flex-1 max-w-full md:max-w-[85%] glass-panel rounded-2xl rounded-tl-none p-5 text-gray-100 border border-amber-500/20 shadow-xl overflow-hidden">
      <div class="flex items-center justify-between pb-3 mb-3 border-b border-gray-800/80">
        <div class="flex items-center gap-2">
          <span class="font-cinzel font-semibold text-amber-400 text-sm tracking-wide">Mayank · Gita Guide</span>
          <span class="text-[10px] sm:text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300/90 border border-amber-500/20">
            Bhagavad Gita · RAG
          </span>
        </div>
        <div class="flex items-center gap-1 action-buttons opacity-0 transition-opacity">
          <button class="listen-btn p-1.5 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-amber-300 text-xs transition" title="Listen to counsel">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
          </button>
          <button class="copy-btn p-1.5 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-amber-300 text-xs transition" title="Copy wisdom">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
        </div>
      </div>

      <!-- RAG Grounding Verses Container -->
      <div class="rag-grounding-container mb-4 hidden"></div>

      <!-- Main Wisdom Content Area -->
      <div class="response-content wisdom-content space-y-4 text-sm md:text-base leading-relaxed">
        <span class="text-amber-400/60 italic text-sm">Consulting the verses of the Gita...</span>
      </div>
    </div>
  `;
  return msgEl;
}

// Render Retrieved RAG Verses Accordion
function renderRagVerses(messageContainer, verses) {
  if (!verses || verses.length === 0) return;
  const ragContainer = messageContainer.querySelector('.rag-grounding-container');
  if (!ragContainer) return;

  ragContainer.classList.remove('hidden');

  let cardsHtml = '';
  verses.forEach((v, idx) => {
    const scoreBadge = v.match_type === 'exact_reference'
      ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Exact Reference</span>`
      : `<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/25">${Math.round(v.score * 100)}% Match</span>`;

    cardsHtml += `
      <div class="p-3 rounded-xl bg-black/30 border border-amber-500/20 text-xs space-y-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <span class="font-cinzel font-bold text-amber-400 text-xs">${escapeHtml(v.reference)}</span>
            <span class="text-gray-400 text-[11px]">(${escapeHtml(v.chapter_name || '')})</span>
          </div>
          ${scoreBadge}
        </div>

        <div class="font-sanskrit text-amber-100 text-sm leading-relaxed p-2 rounded-lg bg-amber-950/20 border border-amber-500/10">
          ${escapeHtml(v.slok)}
        </div>

        <div class="text-amber-400/80 italic font-mono text-[11px]">
          ${escapeHtml(v.transliteration)}
        </div>

        <p class="text-gray-200 leading-relaxed text-xs">
          <strong class="text-amber-300">Translation:</strong> ${escapeHtml(v.translation_en)}
        </p>

        ${v.translation_hi ? `
          <div class="text-gray-300/90 text-xs pt-1 border-t border-gray-800">
            <strong class="text-orange-300">हिंदी भावार्थ:</strong> ${escapeHtml(v.translation_hi)}
          </div>
        ` : ''}
      </div>
    `;
  });

  ragContainer.innerHTML = `
    <details class="group rounded-xl bg-amber-950/25 border border-amber-500/30 overflow-hidden" open>
      <summary class="cursor-pointer px-3.5 py-2.5 flex items-center justify-between text-xs font-semibold text-amber-300 hover:bg-amber-900/20 transition select-none">
        <div class="flex items-center gap-2">
          <span>📜</span>
          <span>Grounded in Authentic Gita Verses (${verses.length} Retrieved)</span>
        </div>
        <span class="text-amber-400 text-[11px] group-open:rotate-180 transition-transform">▼</span>
      </summary>
      <div class="p-3 pt-1 space-y-2.5">
        ${cardsHtml}
      </div>
    </details>
  `;
}

// Intermediate streaming format (while typing)
function formatIntermediateStreaming(text) {
  return text
    .split('\n')
    .map(line => `<p>${escapeHtml(line)}</p>`)
    .join('');
}

// Parse Structured Wisdom Sections
function renderStructuredWisdom(messageContainer, rawText, retrievedVerses = []) {
  const contentArea = messageContainer.querySelector('.response-content');
  const actionButtons = messageContainer.querySelector('.action-buttons');
  if (actionButtons) actionButtons.classList.remove('opacity-0');

  const listenBtn = messageContainer.querySelector('.listen-btn');
  const copyBtn = messageContainer.querySelector('.copy-btn');

  if (copyBtn) {
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(rawText);
      showToast('Wisdom copied to clipboard!');
    };
  }

  if (listenBtn) {
    listenBtn.onclick = () => toggleSpeech(rawText, listenBtn);
  }

  // Parse sections
  const sections = parseGitaSections(rawText);

  if (sections && Object.keys(sections).length >= 3) {
    let html = '';

    if (sections.situation) {
      html += `
        <div class="gita-section-card p-4 rounded-xl bg-amber-950/20 border-l-4 border-amber-500/80 border border-amber-500/20">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400 mb-1.5">
            <span>🌼</span> Situation
          </div>
          <div class="text-gray-200 text-sm md:text-base">${formatMarkdownText(sections.situation)}</div>
        </div>
      `;
    }

    if (sections.krishnaTeaching) {
      html += `
        <div class="gita-section-card p-4 rounded-xl bg-orange-950/25 border-l-4 border-orange-500 border border-orange-500/20 shadow-md">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-orange-300 mb-1.5 font-cinzel">
            <span>🕉</span> Krishna's Teaching
          </div>
          <div class="text-amber-100 text-sm md:text-base leading-relaxed font-normal">${formatMarkdownText(sections.krishnaTeaching)}</div>
        </div>
      `;
    }

    if (sections.gitaPrinciple) {
      html += `
        <div class="gita-section-card p-4 rounded-xl bg-yellow-950/20 border-l-4 border-yellow-500 border border-yellow-500/20">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-yellow-300 mb-1.5">
            <span>📖</span> Gita Principle & Verse
          </div>
          <div class="text-gray-200 text-sm md:text-base">${formatMarkdownText(sections.gitaPrinciple)}</div>
        </div>
      `;
    }

    if (sections.modernExample) {
      html += `
        <div class="gita-section-card p-4 rounded-xl bg-teal-950/20 border-l-4 border-teal-500 border border-teal-500/20">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-300 mb-1.5">
            <span>🌍</span> Modern-Life Example
          </div>
          <div class="text-gray-200 text-sm md:text-base">${formatMarkdownText(sections.modernExample)}</div>
        </div>
      `;
    }

    if (sections.practicalActions) {
      const actionsList = sections.practicalActions
        .split('\n')
        .map(s => s.trim())
        .filter(s => s.length > 0);

      let actionItemsHtml = '';
      actionsList.forEach((item) => {
        const cleanItem = item.replace(/^[-*•\d.]+\s*/, '');
        if (cleanItem) {
          actionItemsHtml += `
            <li class="flex items-start gap-2.5 py-1 text-sm md:text-base text-gray-200">
              <span class="text-amber-400 font-bold shrink-0 mt-0.5">✦</span>
              <span>${formatMarkdownText(cleanItem)}</span>
            </li>
          `;
        }
      });

      html += `
        <div class="gita-section-card p-4 rounded-xl bg-blue-950/20 border-l-4 border-blue-500 border border-blue-500/20">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-300 mb-2">
            <span>💡</span> Practical Actions
          </div>
          <ul class="space-y-1.5">${actionItemsHtml || formatMarkdownText(sections.practicalActions)}</ul>
        </div>
      `;
    }

    if (sections.reflection) {
      html += `
        <div class="gita-section-card p-4 rounded-xl bg-emerald-950/25 border-l-4 border-emerald-500 border border-emerald-500/20 italic">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-300 mb-1.5 not-italic">
            <span>🌿</span> Reflection
          </div>
          <div class="text-emerald-100 text-sm md:text-base">"${formatMarkdownText(sections.reflection)}"</div>
        </div>
      `;
    }

    contentArea.innerHTML = html;
  } else {
    contentArea.innerHTML = formatMarkdownText(rawText);
  }
}

// Parse Section Helper
function parseGitaSections(text) {
  const sections = {};
  const cleaned = text.replace(/━+/g, '').trim();

  const patterns = [
    { key: 'situation', regex: /🌼\s*(?:\*{1,2})?(?:Situation)?(?:\*{1,2})?:?\s*([\s\S]*?)(?=🕉|📖|🌍|💡|🌿|$)/i },
    { key: 'krishnaTeaching', regex: /🕉\s*(?:\*{1,2})?(?:Krishna's Teaching|Teaching)?(?:\*{1,2})?:?\s*([\s\S]*?)(?=🌼|📖|🌍|💡|🌿|$)/i },
    { key: 'gitaPrinciple', regex: /📖\s*(?:\*{1,2})?(?:Gita Principle|Principle)?(?:\*{1,2})?:?\s*([\s\S]*?)(?=🌼|🕉|🌍|💡|🌿|$)/i },
    { key: 'modernExample', regex: /🌍\s*(?:\*{1,2})?(?:Modern-Life Example|Modern Example|Example)?(?:\*{1,2})?:?\s*([\s\S]*?)(?=🌼|🕉|📖|💡|🌿|$)/i },
    { key: 'practicalActions', regex: /💡\s*(?:\*{1,2})?(?:Practical Actions|Actions)?(?:\*{1,2})?:?\s*([\s\S]*?)(?=🌼|🕉|📖|🌍|🌿|$)/i },
    { key: 'reflection', regex: /🌿\s*(?:\*{1,2})?(?:Reflection)?(?:\*{1,2})?:?\s*([\s\S]*?)(?=🌼|🕉|📖|🌍|💡|$)/i }
  ];

  let matchedAny = false;
  patterns.forEach(({ key, regex }) => {
    const match = cleaned.match(regex);
    if (match && match[1] && match[1].trim()) {
      sections[key] = match[1].trim();
      matchedAny = true;
    }
  });

  return matchedAny ? sections : null;
}

// Markdown formatting helper
function formatMarkdownText(str) {
  if (!str) return '';
  let formatted = escapeHtml(str);
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="text-amber-300 font-semibold">$1</strong>');
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  return formatted.replace(/\n\n+/g, '</p><p class="mt-2">').replace(/\n/g, '<br/>');
}

// Speech synthesis
function toggleSpeech(text, btn) {
  if (!('speechSynthesis' in window)) {
    showToast('Speech synthesis not supported in this browser.', 'warning');
    return;
  }

  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    btn.innerHTML = `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" /></svg>`;
    return;
  }

  const speechText = text
    .replace(/━+/g, '')
    .replace(/[🌼🕉📖🌍💡🌿*#]/g, '')
    .trim();

  const utterance = new SpeechSynthesisUtterance(speechText);
  utterance.rate = 0.95;
  utterance.pitch = 1.0;

  btn.innerHTML = `<svg class="w-4 h-4 text-amber-400 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" /></svg>`;

  utterance.onend = () => {
    btn.innerHTML = `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" /></svg>`;
  };

  utterance.onerror = () => {
    btn.innerHTML = `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" /></svg>`;
  };

  window.speechSynthesis.speak(utterance);
}

// Utilities
function scrollToBottom() {
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setControlsDisabled(disabled) {
  sendBtn.disabled = disabled;
  userInput.disabled = disabled;
  if (disabled) {
    sendBtn.classList.add('opacity-50', 'cursor-not-allowed');
  } else {
    sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    userInput.focus();
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.innerText = str;
  return div.innerHTML;
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2.5 rounded-xl shadow-2xl text-sm font-medium z-50 transition-all transform duration-300 ease-out flex items-center gap-2 ${
    type === 'warning'
      ? 'bg-amber-900 border border-amber-600 text-amber-100'
      : 'bg-gray-900 border border-amber-500/40 text-white'
  }`;
  toast.innerHTML = `<span>${type === 'warning' ? '⚠️' : '✨'}</span> ${escapeHtml(message)}`;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
