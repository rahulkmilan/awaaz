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
  // Store tracking ID for PDF/WhatsApp actions
  currentTrackingId = data.tracking_id;
  
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


// ─── PDF Download ─────────────────────────────────────────────────────────────

let currentTrackingId = null;

function downloadPDF() {
  if (!currentTrackingId) {
    showToast('No complaint to download.', 'error');
    return;
  }
  
  const btn = document.getElementById('btn-download-pdf');
  const originalText = btn.textContent;
  btn.textContent = '⏳ Generating...';
  btn.disabled = true;
  
  fetch(`${API_BASE}/api/complaints/${currentTrackingId}/pdf`)
    .then(res => {
      if (!res.ok) throw new Error('PDF generation failed');
      return res.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Awaaz_Complaint_${currentTrackingId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast('PDF downloaded successfully!');
    })
    .catch(err => {
      showToast('Failed to generate PDF. Please try again.', 'error');
      console.error(err);
    })
    .finally(() => {
      btn.textContent = originalText;
      btn.disabled = false;
    });
}


// ─── WhatsApp Share ───────────────────────────────────────────────────────────

function shareWhatsApp() {
  if (!currentTrackingId) {
    showToast('No complaint to share.', 'error');
    return;
  }
  
  fetch(`${API_BASE}/api/complaints/${currentTrackingId}/whatsapp`)
    .then(res => res.json())
    .then(data => {
      window.open(data.whatsapp_url, '_blank');
      showToast('Opening WhatsApp...');
    })
    .catch(err => {
      showToast('Failed to generate share link.', 'error');
      console.error(err);
    });
}


// ─── Dashboard ────────────────────────────────────────────────────────────────

async function loadDashboard() {
  const listEl = document.getElementById('dashboard-list');
  
  try {
    const response = await fetch(`${API_BASE}/api/complaints`);
    const data = await response.json();
    const complaints = data.complaints || [];
    
    // Update stats
    document.getElementById('stat-total').textContent = complaints.length;
    document.getElementById('stat-ready').textContent = complaints.filter(c => c.status === 'ready').length;
    document.getElementById('stat-filed').textContent = complaints.filter(c => c.status === 'filed').length;
    
    if (complaints.length === 0) {
      listEl.innerHTML = `
        <div class="form-card" style="text-align: center; padding: 60px 20px;">
          <p style="font-size: 3rem; margin-bottom: 12px;">📭</p>
          <p style="font-size: 1.1rem; color: var(--text-secondary);">No complaints filed yet.</p>
          <button class="btn btn-primary" style="margin-top: 16px;" onclick="showView('form-view')">File Your First Complaint →</button>
        </div>
      `;
      return;
    }
    
    const categoryEmojis = {
      cybercrime: '🛡️', consumer: '🛒', municipal: '🏛️', rti: '📋',
      police: '🚔', rera: '🏠', railways: '🚂', tax: '💰', labour: '👷',
    };
    
    const statusColors = {
      draft: '#6b7280', ready: '#10b981', filed: '#3b82f6',
      acknowledged: '#8b5cf6', in_progress: '#f59e0b',
      resolved: '#10b981', escalated: '#ef4444', closed: '#6b7280',
    };
    
    listEl.innerHTML = complaints.map(c => `
      <div class="result-card" style="margin-bottom: 16px; cursor: default;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
          <div style="flex: 1; min-width: 200px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
              <span style="font-size: 1.3rem;">${categoryEmojis[c.category] || '📝'}</span>
              <span style="font-family: monospace; font-size: 0.85rem; color: var(--accent); font-weight: 700;">${c.tracking_id}</span>
              <span style="font-size: 0.7rem; padding: 2px 8px; border-radius: 20px; font-weight: 600; color: #fff; background: ${statusColors[c.status] || '#6b7280'};">${c.status.toUpperCase()}</span>
            </div>
            <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5; margin: 0;">${c.summary || 'No summary'}</p>
            <p style="color: var(--text-muted); font-size: 0.75rem; margin-top: 6px;">
              ${c.authority || ''} · ${c.created_at ? new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''}
            </p>
          </div>
          <div style="display: flex; gap: 8px; flex-shrink: 0;">
            <button class="btn btn-secondary btn-sm" onclick="window.open('/api/complaints/${c.tracking_id}/pdf')" style="font-size: 0.75rem; padding: 6px 12px;">📄 PDF</button>
            <button class="btn btn-secondary btn-sm" onclick="shareDashboardWhatsApp('${c.tracking_id}')" style="font-size: 0.75rem; padding: 6px 12px; background: #25D366; border-color: #25D366; color: #fff;">💬</button>
          </div>
        </div>
      </div>
    `).join('');
    
  } catch (err) {
    listEl.innerHTML = `
      <div class="form-card" style="text-align: center; padding: 40px 20px;">
        <p style="color: var(--text-muted);">Failed to load complaints. Please try again.</p>
      </div>
    `;
    console.error(err);
  }
}

function shareDashboardWhatsApp(trackingId) {
  fetch(`${API_BASE}/api/complaints/${trackingId}/whatsapp`)
    .then(res => res.json())
    .then(data => window.open(data.whatsapp_url, '_blank'))
    .catch(err => showToast('Failed to generate share link.', 'error'));
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

