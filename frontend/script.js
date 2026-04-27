// ═══════════════════════════════════════════
//  Stay — Script.js
//  Light Purple / Meetio-style theme
// ═══════════════════════════════════════════

// Backend API URL (change this to your deployed backend URL)
// const API_BASE_URL = 'http://localhost:8000';
const API_BASE_URL = 'https://medical-alzhiemer.onrender.com';

// ── Authentication ──────────────────────────────────────
let selectedGender = null;
let authMode = 'signup'; // 'signup' or 'login'
let userData = {
  email: '',
  name: '',
  gender: ''
};

function selectGender(gender) {
  console.log('selectGender called with:', gender);
  selectedGender = gender;
  userData.gender = gender;

  document.querySelectorAll('.gender-btn').forEach(btn => {
    btn.classList.remove('selected');
  });

  const selectedBtn = document.querySelector(`.gender-btn[data-gender="${gender}"]`);
  if (selectedBtn) {
    selectedBtn.classList.add('selected');
  }
}

function toggleAuthMode(mode) {
  authMode = mode;
  const signupToggle = document.getElementById('signup-toggle');
  const loginToggle = document.getElementById('login-toggle');
  const nameGroup = document.getElementById('name-group');
  const genderGroup = document.getElementById('gender-group');
  const sendOtpBtn = document.getElementById('send-otp-btn');

  if (mode === 'signup') {
    signupToggle.classList.add('active');
    loginToggle.classList.remove('active');
    nameGroup.style.display = 'block';
    genderGroup.style.display = 'block';
    sendOtpBtn.textContent = 'Send OTP';
  } else {
    loginToggle.classList.add('active');
    signupToggle.classList.remove('active');
    nameGroup.style.display = 'none';
    genderGroup.style.display = 'none';
    sendOtpBtn.textContent = 'Login';
  }
}

async function sendOTP() {
  const email = document.getElementById('email-input').value;
  const name = document.getElementById('name-input').value;

  if (!email) {
    alert('Please enter your email');
    return;
  }

  if (authMode === 'signup' && (!name || !selectedGender)) {
    alert('Please fill in all fields and select a gender');
    return;
  }

  userData.email = email;
  if (authMode === 'signup') {
    userData.name = name;
    userData.gender = selectedGender;
  }

  // If login mode, call direct login endpoint
  if (authMode === 'login') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email })
      });

      const data = await response.json();

      if (data.success) {
        // Update user data from server
        userData.name = data.user.name;
        userData.gender = data.user.gender;
        userData.email = data.user.email;

        // Show welcome animation
        showWelcomeAnimation();
      } else {
        alert(data.message || 'Login failed. Please try again.');
      }
    } catch (error) {
      console.error('Error during login:', error);
      alert('Error during login. Please try again.');
    }
    return;
  }

  // Signup mode - send OTP
  try {
    const response = await fetch(`${API_BASE_URL}/api/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        name: name,
        gender: selectedGender
      })
    });

    const data = await response.json();

    if (data.success) {
      // Show OTP form
      document.getElementById('auth-form').style.display = 'none';
      document.getElementById('otp-form').style.display = 'block';

      // For demo: auto-fill the OTP (remove in production)
      document.getElementById('otp-input').value = data.otp;
    } else {
      alert('Failed to send OTP. Please try again.');
    }
  } catch (error) {
    console.error('Error sending OTP:', error);
    alert('Error sending OTP. Please try again.');
  }
}

async function verifyOTP() {
  const otp = document.getElementById('otp-input').value;
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: userData.email, otp })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Update user data from server
      userData.name = data.user.name;
      userData.gender = data.user.gender;
      userData.email = data.user.email;
      
      // Show welcome animation
      showWelcomeAnimation();
    } else {
      alert('Invalid or expired OTP. Please try again.');
    }
  } catch (error) {
    console.error('Error verifying OTP:', error);
    alert('Error verifying OTP. Please try again.');
  }
}

function backToAuth() {
  document.getElementById('auth-form').style.display = 'block';
  document.getElementById('otp-form').style.display = 'none';
}

function showWelcomeAnimation() {
  document.getElementById('auth-page').style.display = 'none';
  document.getElementById('welcome-overlay').style.display = 'flex';
  
  // Update welcome message with user name
  document.querySelector('.welcome-message').textContent = `Welcome back, ${userData.name}`;
  
  // Update user avatar in sidebar
  updateUserAvatar();
  
  // Hide welcome and show main app after animation
  setTimeout(() => {
    document.getElementById('welcome-overlay').style.display = 'none';
    document.getElementById('main-app').style.display = 'flex';
  }, 2500);
}

function updateUserAvatar() {
  const avatarEl = document.getElementById('user-avatar');
  if (avatarEl) {
    if (userData.gender === 'male') {
      avatarEl.textContent = '♂';
    } else if (userData.gender === 'female') {
      avatarEl.textContent = '♀';
    } else {
      // Use initials
      const initials = userData.name.split(' ').map(n => n[0]).join('').toUpperCase();
      avatarEl.textContent = initials;
    }
  }
  
  // Update user name
  const nameEl = document.getElementById('user-name');
  if (nameEl) {
    nameEl.textContent = userData.name;
  }
  
  // Update user email
  const emailEl = document.getElementById('user-email');
  if (emailEl) {
    emailEl.textContent = userData.email;
  }
}

// ── Page Navigation ──────────────────────────────────────
const PAGE_TITLES = {
  dashboard: 'Clinical <em>Query Agent</em>',
  chat:      'Query <em>Agent</em>',
  analysis:  'MRI Image <em>Analysis</em>',
};

function switchPage(id, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + id)?.classList.add('active');

  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');

  const titleEl = document.getElementById('topbar-title');
  if (titleEl) titleEl.innerHTML = PAGE_TITLES[id] || id;
}

function toggleFilter(btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

// ── Chat ─────────────────────────────────────────────────
const MOCK_RESPONSE = {
  sections: [
    {
      title: '1. Score / Symptom Analysis',
      body: 'An MMSE score of 19/30 places this patient in the <strong>Mild Alzheimer\'s Disease</strong> range (18–23). Deficits are typically observed in short-term recall, orientation to time and place, and visuospatial tasks, exceeding normal age-related variation.'
    },
    {
      title: '2. NIA-AA 2018 Criteria Match',
      body: 'Per NIA-AA 2018 guidelines, this profile satisfies the criteria for <em>Probable Alzheimer\'s Disease — Dementia Stage</em>. Biomarker confirmation (amyloid/tau) is required to move from probable to definitive classification.'
    },
    {
      title: '3. Risk & Functional Assessment',
      body: 'ADL performance is likely impacted at this threshold. A CDR score of 1 (Mild) is expected. Caregiver burden increases significantly beyond MMSE 20. Social and occupational functioning may be noticeably affected.'
    },
    {
      title: '4. Recommended Next Steps',
      body: 'Full neuropsychological battery · Amyloid PET or CSF biomarkers (tau/Aβ42) · MRI to rule out vascular contributions · OT assessment for ADL capacity · Caregiver support referral.'
    },
  ],
  sources: ['alzheimer_facts_2024.pdf · p.12', 'nia_aa_guidelines.pdf · p.7']
};

function buildBotHTML(data) {
  let html = `<div class="msg-bubble">`;
  data.sections.forEach(s => {
    html += `
      <div class="msg-section">
        <div class="msg-section-title">${s.title}</div>
        <div class="msg-section-body">${s.body}</div>
      </div>`;
  });
  html += `<div style="margin-top:12px;">`;
  data.sources.forEach(src => {
    html += `<span class="source-chip">📄 ${src}</span>`;
  });
  html += `</div>`;
  html += `<div style="margin-top:10px;font-size:11px;color:var(--red);opacity:0.75;font-weight:500;">⚠️ Clinical decision support only. Consult a licensed neurologist.</div>`;
  html += `</div>`;
  return html;
}

function appendMsg(avatar, name, contentHTML, isUser = false) {
  const msgs = document.getElementById('chat-messages');
  if (!msgs) return; // Handle case where chat messages element doesn't exist
  
  const div  = document.createElement('div');
  div.className = 'msg' + (isUser ? ' user' : '');
  div.innerHTML = `
    <div class="msg-avatar ${isUser ? 'user' : 'bot'}">${avatar}</div>
    <div class="msg-content">
      <div class="msg-name">${name}</div>
      ${contentHTML}
    </div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

function showTyping() {
  return appendMsg('🧠', 'NEURORAG AGENT · NOW',
    `<div class="msg-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`);
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const btn   = document.getElementById('send-btn');
  const q     = input.value.trim();
  if (!q) return;

  input.value   = '';
  btn.disabled  = true;

  const sug = document.getElementById('suggestion-row');
  if (sug) sug.style.display = 'none';

  // User msg
  appendMsg('👤', 'CLINICIAN · NOW',
    `<div class="msg-bubble">${q}</div>`, true);

  // Typing
  const typing = showTyping();

  try {
    // Call the FastAPI endpoint
    const response = await fetch(`${API_BASE_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: q }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    typing.remove();

    // Parse the response and display it
    // For now, display the raw response as formatted text
    const formattedResponse = formatRAGResponse(data.response);
    appendMsg('🧠', 'NEURORAG AGENT · NOW', formattedResponse);
    
  } catch (error) {
    typing.remove();
    console.error('Error:', error);
    appendMsg('🧠', 'NEURORAG AGENT · NOW',
      `<div class="msg-bubble" style="color:var(--red);">
        ⚠️ Error connecting to RAG system: ${error.message}
      </div>`);
  }

  btn.disabled = false;
}

function formatRAGResponse(response) {
  // Convert Markdown to HTML
  let formatted = response;
  
  // Bold: **text** -> <strong>text</strong>
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Italic: *text* -> <em>text</em>
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Format the RAG response as HTML
  const lines = formatted.split('\n');
  let html = '<div class="msg-bubble">';
  
  let inSection = false;
  let currentSection = '';
  
  for (let line of lines) {
    line = line.trim();
    if (!line) continue;
    
    // Check for numbered sections
    if (line.match(/^\d+\./) || line.match(/^[A-Z]+\s*:/)) {
      if (currentSection) {
        html += `<div class="msg-section-body">${currentSection}</div>`;
        currentSection = '';
      }
      html += `<div class="msg-section-title">${line}</div>`;
      inSection = true;
    } else if (line.toLowerCase().includes('sources used') || line.toLowerCase().includes('source:')) {
      if (currentSection) {
        html += `<div class="msg-section-body">${currentSection}</div>`;
        currentSection = '';
      }
      html += `<div style="margin-top:12px;"><strong>${line}</strong></div>`;
      inSection = false;
    } else if (line.startsWith('-') || line.startsWith('•')) {
      // Bullet points
      currentSection += `<div style="margin-left:20px;">• ${line.substring(1).trim()}</div>`;
    } else {
      currentSection += `<div>${line}</div>`;
    }
  }
  
  if (currentSection) {
    html += `<div class="msg-section-body">${currentSection}</div>`;
  }
  
  html += `<div style="margin-top:10px;font-size:11px;color:var(--red);opacity:0.75;font-weight:500;">⚠️ Clinical decision support only. Consult a licensed neurologist.</div>`;
  html += `</div>`;
  
  return html;
}

function fillSuggestion(btn) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = btn.textContent.trim();
    input.focus();
  }
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ── Analysis ─────────────────────────────────────────────
let uploadedImageData = null;

function handleImageUploadAuto(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
      uploadedImageData = e.target.result;
      const preview = document.getElementById('image-preview');
      const placeholder = document.getElementById('upload-placeholder');
      const img = document.getElementById('preview-img');
      
      img.src = uploadedImageData;
      placeholder.style.display = 'none';
      preview.style.display = 'block';
      
      // Automatically trigger analysis
      runImageAnalysis();
    };
    
    reader.readAsDataURL(file);
  }
}

function handleImageUpload(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
      uploadedImageData = e.target.result;
      const preview = document.getElementById('image-preview');
      const img = document.getElementById('preview-img');
      img.src = uploadedImageData;
      preview.style.display = 'block';
    };
    
    reader.readAsDataURL(file);
  }
}

function openCamera() {
  const input = document.getElementById('f-image');
  input.setAttribute('capture', 'environment');
  input.click();
}

function clearImage() {
  uploadedImageData = null;
  document.getElementById('f-image').value = '';
  document.getElementById('image-preview').style.display = 'none';
  document.getElementById('upload-placeholder').style.display = 'block';
  document.getElementById('preview-img').src = '';
  
  // Clear results
  const empty = document.getElementById('result-empty');
  const content = document.getElementById('result-content');
  if (empty) empty.style.display = 'block';
  if (content) content.style.display = 'none';
}

function getSeverity(mmse) {
  if (mmse >= 24) return { label: 'Possible MCI',  cls: 'sev-normal' };
  if (mmse >= 18) return { label: 'Mild AD',        cls: 'sev-mild' };
  if (mmse >= 10) return { label: 'Moderate AD',    cls: 'sev-moderate' };
  return               { label: 'Severe AD',        cls: 'sev-moderate' };
}

async function runImageAnalysis() {
  if (!uploadedImageData) {
    alert('Please upload an image first.');
    return;
  }

  // Get optional clinical data
  const age = document.getElementById('f-age')?.value;
  const mmse = document.getElementById('f-mmse')?.value;
  const symptoms = document.getElementById('f-symptoms')?.value;

  // Show loading state
  const empty = document.getElementById('result-empty');
  const content = document.getElementById('result-content');
  if (empty) empty.style.display = 'none';
  if (content) {
    content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-faint);">🔬 Analyzing brain scan...</div>';
    content.style.display = 'block';
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        age: age,
        mmse: mmse,
        symptoms: symptoms,
        image_data: uploadedImageData
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Format and display the response
    const formattedResponse = formatRAGResponse(data.response);
    
    if (content) {
      content.innerHTML = formattedResponse;
    }
    
  } catch (error) {
    console.error('Error:', error);
    if (content) {
      content.innerHTML = `
        <div style="text-align:center;padding:40px;color:var(--red);">
          ⚠️ Error: ${error.message}
        </div>
      `;
    }
  }
}

async function runAnalysis() {
  const age      = document.getElementById('f-age')?.value;
  const education = document.getElementById('f-edu')?.value;
  const mmse     = document.getElementById('f-mmse')?.value;
  const moca     = document.getElementById('f-moca')?.value;
  const cdr      = document.getElementById('f-cdr')?.value;
  const gds      = document.getElementById('f-gds')?.value;
  const symptoms = document.getElementById('f-symptoms')?.value;

  if (!age && !mmse && !moca && !uploadedImageData) {
    alert('Please enter at least age, a cognitive score, or upload an MRI image.');
    return;
  }

  // Update score position markers
  if (mmse) {
    const m = document.getElementById('mmse-marker');
    if (m) m.style.left = ((parseInt(mmse) / 30) * 96) + '%';
  }
  if (moca) {
    const m = document.getElementById('moca-marker');
    if (m) m.style.left = ((parseInt(moca) / 30) * 96) + '%';
  }

  // Show loading state
  const empty   = document.getElementById('result-empty');
  const content = document.getElementById('result-content');
  if (empty)   empty.style.display   = 'none';
  if (content) {
    content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-faint);">🔬 Analyzing patient data...</div>';
    content.style.display = 'block';
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        age: age,
        education: education,
        mmse: mmse,
        moca: moca,
        cdr: cdr,
        gds: gds,
        symptoms: symptoms,
        image_data: uploadedImageData
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Format and display the response
    const formattedResponse = formatRAGResponse(data.response);
    
    if (content) {
      content.innerHTML = formattedResponse;
    }
    
  } catch (error) {
    console.error('Error:', error);
    if (content) {
      content.innerHTML = `
        <div style="text-align:center;padding:40px;color:var(--red);">
          ⚠️ Error: ${error.message}
        </div>
      `;
    }
  }
}

// ── Animate scale bars on load ────────────────────────────
function animateScaleBars() {
  document.querySelectorAll('.scale-fill').forEach(el => {
    const target = el.style.width;
    el.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { el.style.width = target; }, 80);
    });
  });
}

// ── Init ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  animateScaleBars();
});
