/**
 * Awaaz — Frontend Application Logic
 */

const API_BASE = '';

// ─── View Management ──────────────────────────────────────────────────────────

function showView(viewId) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const view = document.getElementById(viewId);
  if (view) {
    view.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  // Update nav
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  const navLink = document.querySelector(`[data-view="${viewId}"]`);
  if (navLink) navLink.classList.add('active');
}

// ─── Complaint Filing ─────────────────────────────────────────────────────────

async function submitComplaint(e) {
  e.preventDefault();

  const description = document.getElementById('complaint-text').value.trim();
  if (description.length < 10) {
    showToast('Please describe your problem in more detail.', 'error');
    return;
  }

  // Show loading
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.add('active');

  // Animate loading messages
  const loadingMessages = [
    'Analyzing your complaint...',
    'Identifying the right authority...',
    'Drafting your formal complaint...',
    'Preparing filing guide...',
    'Checking your legal rights...',
  ];
  let msgIndex = 0;
  const msgEl = document.getElementById('loading-msg');
  const msgInterval = setInterval(() => {
    msgIndex = (msgIndex + 1) % loadingMessages.length;
    msgEl.textContent = loadingMessages[msgIndex];
  }, 1500);

  try {
    const response = await fetch(`${API_BASE}/api/complaints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description: description,
        user_name: document.getElementById('user-name')?.value || null,
        user_email: document.getElementById('user-email')?.value || null,
        user_city: 'Kochi',
      }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Something went wrong');
    }

    const data = await response.json();
    clearInterval(msgInterval);
    overlay.classList.remove('active');

    renderResults(data);
    showView('results-view');
  } catch (err) {
    clearInterval(msgInterval);
    overlay.classList.remove('active');
    showToast(err.message || 'Failed to process complaint. Please try again.', 'error');
  }
}

// ─── Render Results ───────────────────────────────────────────────────────────

function renderResults(data) {
  // Tracking ID
  document.getElementById('result-tracking-id').textContent = data.tracking_id;

  // Category badge
  const categoryEmojis = {
    cybercrime: '🛡️', consumer: '🛒', municipal: '🏛️', rti: '📋',
    police: '🚔', rera: '🏠', railways: '🚂', tax: '💰', labour: '👷',
  };
  document.getElementById('result-category').textContent =
    `${categoryEmojis[data.category] || '📝'} ${data.category.replace('_', ' ').toUpperCase()}`;

  // Summary
  document.getElementById('result-summary').textContent = data.summary;

  // Authority info
  document.getElementById('authority-name').textContent = data.authority;
  document.getElementById('authority-portal').textContent = data.authority_portal;
  document.getElementById('authority-portal').href = data.authority_portal;
  if (data.authority_helpline) {
    document.getElementById('authority-helpline').textContent = `📞 Helpline: ${data.authority_helpline}`;
  }

  // Draft
  document.getElementById('draft-content').textContent = data.draft;

  // Filing guide
  const guideList = document.getElementById('filing-guide-list');
  guideList.innerHTML = '';
  (data.filing_guide || []).forEach(step => {
    const li = document.createElement('li');
    li.textContent = step;
    guideList.appendChild(li);
  });

  // Evidence checklist
  const evidenceList = document.getElementById('evidence-list');
  evidenceList.innerHTML = '';
  (data.evidence_checklist || []).forEach(item => {
    const li = document.createElement('li');
    li.textContent = item;
    evidenceList.appendChild(li);
  });

  // Legal rights
  const rightsList = document.getElementById('rights-list');
  rightsList.innerHTML = '';
  (data.legal_rights || []).forEach(right => {
    const li = document.createElement('li');
    li.textContent = right;
    rightsList.appendChild(li);
  });

  // Mode indicator
  const modeEl = document.getElementById('ai-mode');
  if (modeEl) {
    modeEl.textContent = data.mode === 'ai' ? '🤖 AI-Powered Analysis' : '⚡ Smart Analysis';
  }

  // Animate results cards
  setTimeout(() => {
    document.querySelectorAll('.result-card').forEach((card, i) => {
      setTimeout(() => card.classList.add('visible'), i * 150);
    });
  }, 100);
}

// ─── Copy Draft ───────────────────────────────────────────────────────────────

function copyDraft() {
  const draft = document.getElementById('draft-content').textContent;
  navigator.clipboard.writeText(draft).then(() => {
    showToast('Complaint draft copied to clipboard!');
    const btn = document.querySelector('.copy-btn');
    btn.textContent = '✓ Copied!';
    setTimeout(() => (btn.textContent = 'Copy'), 2000);
  });
}

// ─── Toast Notifications ──────────────────────────────────────────────────────

function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.style.borderColor = type === 'error' ? 'var(--danger)' : 'var(--success)';
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ─── Scroll Animations ───────────────────────────────────────────────────────

function initScrollAnimations() {
  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
}

// ─── Example Complaints ──────────────────────────────────────────────────────

const examples = [
  "I received a call from someone claiming to be from SBI bank. They asked for my OTP and transferred ₹25,000 from my account through UPI.",
  "I ordered a laptop from Flipkart but received an empty box. The seller is not responding and Flipkart refuses to refund.",
  "There's a massive pothole on MG Road near Ernakulam junction that has caused 3 accidents this week. Nobody is fixing it.",
  "My builder promised flat possession by March 2025 but it's still not ready. They stopped responding to calls.",
  "Someone created a fake Instagram profile using my photos and is messaging my friends asking for money.",
];

function fillExample() {
  const textarea = document.getElementById('complaint-text');
  const randomExample = examples[Math.floor(Math.random() * examples.length)];
  textarea.value = '';
  // Typewriter effect
  let i = 0;
  const type = () => {
    if (i < randomExample.length) {
      textarea.value += randomExample[i];
      i++;
      setTimeout(type, 15);
    }
  };
  type();
  textarea.focus();
}

// ─── New Complaint ────────────────────────────────────────────────────────────

function newComplaint() {
  document.getElementById('complaint-text').value = '';
  if (document.getElementById('user-name')) document.getElementById('user-name').value = '';
  if (document.getElementById('user-email')) document.getElementById('user-email').value = '';
  showView('form-view');
}

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initScrollAnimations();

  const form = document.getElementById('complaint-form');
  if (form) form.addEventListener('submit', submitComplaint);
});
