const LOGIN_ENDPOINT = '/api/login';
const ADMIN_APPLICATIONS_ENDPOINT = '/api/admin/applications';
const ADMIN_SESSION_KEY = 'idealAdminSession';

const adminLoginForm = document.getElementById('admin-login-form');
const adminFeedback = document.querySelector('.admin__feedback');
const adminDashboard = document.querySelector('[data-admin-dashboard]');
const adminAuthPane = document.querySelector('[data-admin-auth]');
const adminName = document.querySelector('[data-admin-name]');
const adminMetrics = document.querySelector('[data-admin-metrics]');
const adminRows = document.querySelector('[data-admin-rows]');

function saveAdminSession(session) {
  if (!session) return;
  sessionStorage.setItem(ADMIN_SESSION_KEY, JSON.stringify(session));
}

function getAdminSession() {
  const stored = sessionStorage.getItem(ADMIN_SESSION_KEY);
  try {
    return stored ? JSON.parse(stored) : null;
  } catch (error) {
    console.warn('Não foi possível recuperar a sessão do admin.', error);
    return null;
  }
}

function clearAdminSession() {
  sessionStorage.removeItem(ADMIN_SESSION_KEY);
}

function badgeForStatus(status) {
  if (status === 'aceito') return '<span class="badge badge--success">Aceito</span>';
  if (status === 'recusado') return '<span class="badge badge--danger">Recusado</span>';
  return '<span class="badge badge--info">Em análise</span>';
}

function buildMetricChip(summary) {
  const title = summary.jobTitle || summary.jobId || 'Vaga';
  return `
    <div class="chip">
      <div class="chip__title">${title}</div>
      <p class="chip__meta">${summary.total} inscritos · ${summary.emAnalise} em análise</p>
      <p class="chip__meta chip__meta--success">${summary.aceitos} aceitos</p>
      <p class="chip__meta chip__meta--danger">${summary.recusados} recusados</p>
    </div>
  `;
}

function renderMetrics(list = []) {
  if (!adminMetrics) return;
  if (!list.length) {
    adminMetrics.innerHTML = '<p class="muted">Nenhuma candidatura registrada ainda.</p>';
    return;
  }
  adminMetrics.innerHTML = list.map(buildMetricChip).join('');
}

function renderApplications(applications = []) {
  if (!adminRows) return;
  if (!applications.length) {
    adminRows.innerHTML = '<tr><td colspan="5" class="muted">Nenhuma candidatura encontrada.</td></tr>';
    return;
  }

  adminRows.innerHTML = applications
    .map((application) => {
      const candidate = application.candidate || {};
      const statusMarkup = badgeForStatus(application.status);
      return `
        <tr data-app-id="${application.id}">
          <td>
            <p class="strong">${application.jobTitle || application.jobId}</p>
            <p class="muted">${application.jobId}</p>
          </td>
          <td>${candidate.areaInteresse || '—'}</td>
          <td>
            <p class="strong">${candidate.nome || '—'}</p>
            <p class="muted">${candidate.email || ''}</p>
          </td>
          <td>${statusMarkup}</td>
          <td class="align-right admin__actions">
            <button class="btn btn--ghost" data-status="aceito">Aceitar</button>
            <button class="btn btn--danger" data-status="recusado">Recusar</button>
          </td>
        </tr>
      `;
    })
    .join('');
}

async function fetchAdminData(token) {
  const response = await fetch(ADMIN_APPLICATIONS_ENDPOINT, {
    headers: {
      'X-Admin-Token': token,
    },
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.message || 'Não foi possível carregar as candidaturas.';
    throw new Error(message);
  }
  return payload;
}

async function updateApplicationStatus(token, applicationId, status) {
  const response = await fetch(`${ADMIN_APPLICATIONS_ENDPOINT}/${applicationId}/status`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Token': token,
    },
    body: JSON.stringify({ status }),
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.message || 'Não foi possível atualizar a candidatura.';
    throw new Error(message);
  }
  return payload;
}

async function authenticateAdmin(email, senha) {
  const response = await fetch(LOGIN_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, senha }),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.message || 'Não foi possível validar as credenciais agora.';
    throw new Error(message);
  }
  if (!payload?.candidate?.isAdmin || !payload?.adminToken) {
    throw new Error('Apenas administradores têm acesso a este painel.');
  }
  return payload;
}

function showDashboard({ adminToken, candidate, summary, applications }) {
  if (adminAuthPane) {
    adminAuthPane.hidden = true;
  }
  if (adminDashboard) {
    adminDashboard.hidden = false;
  }
  if (adminName) {
    adminName.textContent = candidate?.nome || candidate?.email || 'Administrador';
  }
  renderMetrics(summary || []);
  renderApplications(applications || []);
  saveAdminSession({ token: adminToken, email: candidate?.email || '' });
}

async function hydrateDashboard() {
  const session = getAdminSession();
  if (!session?.token) return;
  try {
    const payload = await fetchAdminData(session.token);
    showDashboard({
      adminToken: session.token,
      candidate: { email: payload.admin },
      summary: payload.summary,
      applications: payload.applications,
    });
  } catch (error) {
    clearAdminSession();
  }
}

adminLoginForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!adminFeedback) return;

  const formData = new FormData(adminLoginForm);
  const email = formData.get('email')?.toString().trim();
  const senha = formData.get('senha')?.toString().trim();

  if (!email || !senha) {
    adminFeedback.textContent = 'Informe seu e-mail corporativo e senha.';
    adminFeedback.style.color = '#dc2626';
    return;
  }

  adminFeedback.textContent = 'Validando credenciais...';
  adminFeedback.style.color = '#2563eb';

  try {
    const payload = await authenticateAdmin(email, senha);
    const dashboardData = await fetchAdminData(payload.adminToken);
    adminFeedback.textContent = 'Login realizado com sucesso.';
    adminFeedback.style.color = '#16a34a';
    showDashboard({
      adminToken: payload.adminToken,
      candidate: payload.candidate,
      summary: dashboardData.summary,
      applications: dashboardData.applications,
    });
  } catch (error) {
    adminFeedback.textContent = error instanceof Error ? error.message : 'Não foi possível acessar o painel agora.';
    adminFeedback.style.color = '#dc2626';
  }
});

document.addEventListener('click', async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  const status = target.dataset.status;
  if (!status) return;

  const row = target.closest('tr[data-app-id]');
  const appId = row?.dataset.appId;
  const session = getAdminSession();
  if (!row || !appId || !session?.token) return;

  target.setAttribute('disabled', 'true');

  try {
    const payload = await updateApplicationStatus(session.token, Number(appId), status);
    await hydrateDashboard();
    adminFeedback.textContent = payload?.message || 'Status atualizado.';
    adminFeedback.style.color = '#16a34a';
  } catch (error) {
    adminFeedback.textContent = error instanceof Error ? error.message : 'Não foi possível atualizar a candidatura.';
    adminFeedback.style.color = '#dc2626';
  } finally {
    target.removeAttribute('disabled');
  }
});

hydrateDashboard();
