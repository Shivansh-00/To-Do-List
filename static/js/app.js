/* ══════════════════════════════════════════════════════════════
   AI Productivity OS — Frontend Application
   Full-featured SPA with JWT Auth, Real-time Updates, Dark Mode
   ══════════════════════════════════════════════════════════════ */

// ── Constants & State ─────────────────────────────────────────
const API = '';  // Same origin
let authToken = localStorage.getItem('token') || null;
let currentUser = null;
let tasks = [];
let currentFilter = 'all';
let searchQuery = '';
let currentPage = 'dashboard';
let ws = null;

// ── API Helpers ───────────────────────────────────────────────
async function apiRequest(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    try {
        const res = await fetch(`${API}${endpoint}`, { ...options, headers });
        if (res.status === 401) {
            handleLogout();
            throw new Error('Session expired');
        }
        if (res.status === 204) return null;
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Request failed');
        }
        return data;
    } catch (err) {
        if (err.message !== 'Session expired') {
            console.error('API Error:', err);
        }
        throw err;
    }
}

// ── Theme Management ──────────────────────────────────────────
function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeUI(saved);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeUI(next);
}

function updateThemeUI(theme) {
    const btn = document.getElementById('themeToggle');
    const toggle = document.getElementById('darkModeToggle');
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    if (toggle) {
        if (theme === 'dark') {
            toggle.classList.add('active');
        } else {
            toggle.classList.remove('active');
        }
    }
}

// ── Auth ──────────────────────────────────────────────────────
function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    document.getElementById('loginForm').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('signupForm').style.display = tab === 'signup' ? 'block' : 'none';
    hideAuthError();
}

function showAuthError(msg) {
    const el = document.getElementById('authError');
    el.textContent = msg;
    el.classList.add('visible');
}

function hideAuthError() {
    document.getElementById('authError').classList.remove('visible');
}

async function handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    btn.innerHTML = '<span class="spinner"></span> Signing in...';
    btn.disabled = true;
    
    try {
        const data = await apiRequest('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('loginUsername').value.trim(),
                password: document.getElementById('loginPassword').value,
            }),
        });
        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('token', authToken);
        localStorage.setItem('user', JSON.stringify(currentUser));
        showToast('Welcome back, ' + (currentUser.full_name || currentUser.username) + '!', 'success');
        enterApp();
    } catch (err) {
        showAuthError(err.message || 'Invalid credentials');
    } finally {
        btn.innerHTML = 'Sign In';
        btn.disabled = false;
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const btn = document.getElementById('signupBtn');
    btn.innerHTML = '<span class="spinner"></span> Creating...';
    btn.disabled = true;

    try {
        const data = await apiRequest('/api/auth/signup', {
            method: 'POST',
            body: JSON.stringify({
                full_name: document.getElementById('signupFullName').value.trim(),
                username: document.getElementById('signupUsername').value.trim(),
                email: document.getElementById('signupEmail').value.trim(),
                password: document.getElementById('signupPassword').value,
            }),
        });
        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('token', authToken);
        localStorage.setItem('user', JSON.stringify(currentUser));
        showToast('Account created! Welcome, ' + (currentUser.full_name || currentUser.username) + '!', 'success');
        enterApp();
    } catch (err) {
        showAuthError(err.message || 'Signup failed');
    } finally {
        btn.innerHTML = 'Create Account';
        btn.disabled = false;
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    tasks = [];
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    if (ws) { ws.close(); ws = null; }
    document.getElementById('authPage').style.display = 'flex';
    document.getElementById('appContainer').classList.remove('active');
    showToast('Signed out successfully', 'info');
}

// ── App Entry ─────────────────────────────────────────────────
async function enterApp() {
    document.getElementById('authPage').style.display = 'none';
    document.getElementById('appContainer').classList.add('active');
    updateUserUI();
    await loadTasks();
    connectWebSocket();
    navigateTo('dashboard');
}

function updateUserUI() {
    if (!currentUser) return;
    const initials = (currentUser.full_name || currentUser.username || 'U')
        .split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
    
    document.getElementById('userAvatar').textContent = initials;
    document.getElementById('userDisplayName').textContent = currentUser.full_name || currentUser.username;
    document.getElementById('userDisplayEmail').textContent = currentUser.email;
    document.getElementById('settingsUsername').textContent = currentUser.username;
    document.getElementById('settingsEmail').textContent = currentUser.email;
    if (currentUser.created_at) {
        document.getElementById('settingsCreatedAt').textContent = 
            new Date(currentUser.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    }
}

// ── WebSocket Real-time ───────────────────────────────────────
function connectWebSocket() {
    if (ws) ws.close();
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    try {
        ws = new WebSocket(`${protocol}//${location.host}/v1/realtime`);
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'task.created' || msg.type === 'task.updated' || msg.type === 'task.deleted') {
                loadTasks();  // Refresh on real-time event
            }
        };
        ws.onclose = () => {
            setTimeout(connectWebSocket, 3000);  // Auto-reconnect
        };
    } catch (e) {
        console.log('WebSocket not available');
    }
}

// ── Navigation ────────────────────────────────────────────────
function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    const pageEl = document.getElementById(`page-${page}`);
    const navEl = document.querySelector(`[data-page="${page}"]`);
    
    if (pageEl) pageEl.classList.add('active');
    if (navEl) navEl.classList.add('active');
    
    const titles = {
        dashboard: 'Dashboard',
        tasks: 'All Tasks',
        insights: 'AI Insights',
        settings: 'Settings'
    };
    document.getElementById('pageTitle').textContent = titles[page] || 'Dashboard';
    
    if (page === 'insights') loadInsights();
    
    // Close sidebar on mobile
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('active');
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebarOverlay').classList.toggle('active');
}

// ── Tasks CRUD ────────────────────────────────────────────────
async function loadTasks() {
    try {
        tasks = await apiRequest('/v1/tasks');
        renderTasks();
        updateStats();
    } catch (err) {
        if (err.message !== 'Session expired') {
            showToast('Failed to load tasks', 'error');
        }
    }
}

function renderTasks() {
    const filtered = getFilteredTasks();
    
    // Recent tasks (max 5) for dashboard
    renderTaskList('recentTaskList', tasks.slice(0, 8));
    
    // All tasks page
    renderTaskList('allTaskList', filtered);
    
    // Update badge
    const badge = document.getElementById('taskCountBadge');
    if (badge) badge.textContent = tasks.length;
}

function getFilteredTasks() {
    let filtered = [...tasks];
    
    if (currentFilter !== 'all') {
        filtered = filtered.filter(t => t.status === currentFilter);
    }
    
    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        filtered = filtered.filter(t => 
            t.title.toLowerCase().includes(q) ||
            (t.description && t.description.toLowerCase().includes(q)) ||
            (t.tags && t.tags.some(tag => tag.toLowerCase().includes(q)))
        );
    }
    
    return filtered;
}

function renderTaskList(containerId, taskList) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (taskList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📝</div>
                <h3>${searchQuery ? 'No matching tasks' : 'No tasks yet'}</h3>
                <p>${searchQuery ? 'Try a different search term' : 'Create your first task to get started!'}</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = taskList.map(task => {
        const isDone = task.status === 'done';
        const priority = task.priority_score >= 70 ? 'high' : task.priority_score >= 40 ? 'medium' : 'low';
        const statusEmoji = { todo: '📋', in_progress: '🔄', done: '✅', blocked: '🚫' };
        const tags = (task.tags || []).map(t => {
            const cls = t.toLowerCase().includes('urgent') ? 'tag-urgent' : 
                        t.toLowerCase().includes('work') ? 'tag-work' : '';
            return `<span class="tag ${cls}">${escapeHtml(t)}</span>`;
        }).join('');
        
        return `
            <div class="task-card ${isDone ? 'done' : ''}" data-id="${task.id}">
                <div class="priority-bar priority-${priority}"></div>
                <div class="task-checkbox ${isDone ? 'checked' : ''}" 
                     onclick="event.stopPropagation(); toggleTaskDone('${task.id}', ${isDone})">
                    ${isDone ? '✓' : ''}
                </div>
                <div class="task-info" onclick="openEditModal('${task.id}')">
                    <div class="task-title">${escapeHtml(task.title)}</div>
                    <div class="task-meta">
                        <span class="task-meta-item">${statusEmoji[task.status] || '📋'} ${formatStatus(task.status)}</span>
                        ${task.estimated_minutes ? `<span class="task-meta-item">⏱️ ${task.estimated_minutes}min</span>` : ''}
                        ${task.due_at ? `<span class="task-meta-item">📅 ${formatDate(task.due_at)}</span>` : ''}
                    </div>
                    ${tags ? `<div class="task-tags" style="margin-top:6px">${tags}</div>` : ''}
                </div>
                <div class="task-actions">
                    <button class="task-action-btn" onclick="event.stopPropagation(); openEditModal('${task.id}')" title="Edit">✏️</button>
                    <button class="task-action-btn" onclick="event.stopPropagation(); aiBreakdown('${task.id}')" title="AI Breakdown">🤖</button>
                    <button class="task-action-btn delete" onclick="event.stopPropagation(); deleteTask('${task.id}')" title="Delete">🗑️</button>
                </div>
            </div>
        `;
    }).join('');
}

function updateStats() {
    const total = tasks.length;
    const done = tasks.filter(t => t.status === 'done').length;
    const progress = tasks.filter(t => t.status === 'in_progress').length;
    const todo = tasks.filter(t => t.status === 'todo').length;
    
    animateCounter('statTotal', total);
    animateCounter('statDone', done);
    animateCounter('statProgress', progress);
    animateCounter('statTodo', todo);
}

function animateCounter(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const current = parseInt(el.textContent) || 0;
    if (current === target) return;
    
    const increment = target > current ? 1 : -1;
    const steps = Math.abs(target - current);
    const duration = Math.min(500, steps * 50);
    const stepTime = duration / steps;
    
    let val = current;
    const timer = setInterval(() => {
        val += increment;
        el.textContent = val;
        if (val === target) clearInterval(timer);
    }, stepTime);
}

async function toggleTaskDone(taskId, isDone) {
    try {
        const newStatus = isDone ? 'todo' : 'done';
        await apiRequest(`/v1/tasks/${taskId}`, {
            method: 'PATCH',
            body: JSON.stringify({ status: newStatus }),
        });
        showToast(isDone ? 'Task reopened' : 'Task completed! 🎉', 'success');
        await loadTasks();
    } catch (err) {
        showToast('Failed to update task', 'error');
    }
}

function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'New Task';
    document.getElementById('editTaskId').value = '';
    document.getElementById('taskForm').reset();
    document.getElementById('taskModal').classList.add('active');
}

function openEditModal(taskId) {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    document.getElementById('modalTitle').textContent = 'Edit Task';
    document.getElementById('editTaskId').value = taskId;
    document.getElementById('taskTitle').value = task.title;
    document.getElementById('taskDescription').value = task.description || '';
    document.getElementById('taskDueDate').value = task.due_at ? task.due_at.slice(0, 16) : '';
    document.getElementById('taskPriority').value = 
        task.priority_score >= 70 ? '80' : task.priority_score >= 40 ? '50' : '30';
    document.getElementById('taskTags').value = (task.tags || []).join(', ');
    document.getElementById('taskModal').classList.add('active');
}

function closeModal() {
    document.getElementById('taskModal').classList.remove('active');
}

async function handleTaskSubmit(e) {
    e.preventDefault();
    const taskId = document.getElementById('editTaskId').value;
    const tags = document.getElementById('taskTags').value
        .split(',').map(t => t.trim()).filter(Boolean);
    
    const body = {
        title: document.getElementById('taskTitle').value.trim(),
        description: document.getElementById('taskDescription').value.trim() || null,
        due_at: document.getElementById('taskDueDate').value || null,
        tags,
        priority_score: parseFloat(document.getElementById('taskPriority').value),
    };
    
    try {
        if (taskId) {
            await apiRequest(`/v1/tasks/${taskId}`, {
                method: 'PATCH',
                body: JSON.stringify(body),
            });
            showToast('Task updated!', 'success');
        } else {
            await apiRequest('/v1/tasks', {
                method: 'POST',
                body: JSON.stringify(body),
            });
            showToast('Task created! 🎉', 'success');
        }
        closeModal();
        await loadTasks();
    } catch (err) {
        showToast(err.message || 'Failed to save task', 'error');
    }
}

async function deleteTask(taskId) {
    if (!confirm('Delete this task? This cannot be undone.')) return;
    try {
        await apiRequest(`/v1/tasks/${taskId}`, { method: 'DELETE' });
        showToast('Task deleted', 'info');
        await loadTasks();
    } catch (err) {
        showToast('Failed to delete task', 'error');
    }
}

async function aiBreakdown(taskId) {
    try {
        showToast('Generating AI breakdown...', 'info');
        const data = await apiRequest(`/v1/tasks/${taskId}/ai-breakdown`, { method: 'POST' });
        const subtasks = data.generated_subtasks;
        alert('AI Suggested Subtasks:\n\n' + subtasks.map((s, i) => `${i + 1}. ${s}`).join('\n'));
    } catch (err) {
        showToast('AI breakdown failed', 'error');
    }
}

// ── Filters & Search ──────────────────────────────────────────
function filterTasks(filter) {
    currentFilter = filter;
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
    renderTasks();
}

function handleSearch(query) {
    searchQuery = query;
    renderTasks();
}

// ── Insights ──────────────────────────────────────────────────
async function loadInsights() {
    try {
        const data = await apiRequest('/v1/insights/behavior');
        
        // Productivity score (based on completion)
        const total = tasks.length || 1;
        const done = tasks.filter(t => t.status === 'done').length;
        const score = Math.round((done / total) * 100);
        document.getElementById('productivityScore').textContent = score + '%';
        const circle = document.getElementById('scoreCircle');
        if (circle) {
            const offset = 327 - (327 * score / 100);
            circle.style.strokeDashoffset = offset;
        }
        
        // Peak hours
        const peakEl = document.getElementById('peakHours');
        if (peakEl) {
            peakEl.innerHTML = data.peak_hours.map(h => {
                const hour = h > 12 ? `${h - 12} PM` : `${h} AM`;
                return `<div class="peak-hour-chip">${hour}</div>`;
            }).join('');
        }
        
        // Procrastination risk
        const procPct = Math.round(data.procrastination_risk * 100);
        document.getElementById('procrastinationValue').textContent = procPct + '%';
        const procBar = document.getElementById('procrastinationBar');
        procBar.style.width = procPct + '%';
        procBar.className = 'risk-meter-fill ' + (procPct > 60 ? 'risk-high' : procPct > 30 ? 'risk-medium' : 'risk-low');
        
        // Burnout risk
        const burnPct = Math.round(data.burnout_risk * 100);
        document.getElementById('burnoutValue').textContent = burnPct + '%';
        const burnBar = document.getElementById('burnoutBar');
        burnBar.style.width = burnPct + '%';
        burnBar.className = 'risk-meter-fill ' + (burnPct > 60 ? 'risk-high' : burnPct > 30 ? 'risk-medium' : 'risk-low');
        
        // Weekly forecast
        const forecastEl = document.getElementById('weeklyForecast');
        if (forecastEl && data.weekly_productivity_forecast) {
            const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            const maxVal = Math.max(...data.weekly_productivity_forecast, 1);
            forecastEl.innerHTML = data.weekly_productivity_forecast.map((val, i) => {
                const height = Math.max(20, (val / maxVal) * 100);
                return `
                    <div style="flex:1;text-align:center">
                        <div style="background:var(--gradient-primary);height:${height}px;border-radius:6px 6px 0 0;transition:height 1s ease;min-width:30px"></div>
                        <div style="font-size:11px;color:var(--text-muted);margin-top:6px">${days[i]}</div>
                        <div style="font-size:12px;font-weight:700;color:var(--text-secondary)">${Math.round(val)}</div>
                    </div>
                `;
            }).join('');
        }
    } catch (err) {
        showToast('Failed to load insights', 'error');
    }
}

// ── Utilities ─────────────────────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatStatus(status) {
    const map = { todo: 'To Do', in_progress: 'In Progress', done: 'Done', blocked: 'Blocked' };
    return map[status] || status;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date - now;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    
    if (days < 0) return `${Math.abs(days)}d overdue`;
    if (days === 0) return 'Today';
    if (days === 1) return 'Tomorrow';
    if (days < 7) return `${days}d left`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ── Keyboard Shortcuts ────────────────────────────────────────
document.addEventListener('keydown', (e) => {
    // Escape to close modal
    if (e.key === 'Escape') {
        closeModal();
    }
    // Ctrl+K to focus search
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchInput')?.focus();
    }
    // N for new task (when not in input)
    if (e.key === 'n' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        e.preventDefault();
        openCreateModal();
    }
});

// Close modal on overlay click
document.getElementById('taskModal')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
});

// ── Init ──────────────────────────────────────────────────────
(async function init() {
    initTheme();
    
    // Check for stored session
    const storedUser = localStorage.getItem('user');
    if (authToken && storedUser) {
        try {
            currentUser = JSON.parse(storedUser);
            // Verify token is still valid
            const verifiedUser = await apiRequest(`/api/auth/me?token=${authToken}`);
            currentUser = verifiedUser;
            localStorage.setItem('user', JSON.stringify(currentUser));
            enterApp();
        } catch (err) {
            // Token expired, show login
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            authToken = null;
            currentUser = null;
        }
    }
})();
