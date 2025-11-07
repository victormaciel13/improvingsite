const LOGIN_ENDPOINT = '/api/login';
const PROFILE_ENDPOINT = '/api/candidates';
const PROFILE_STORAGE_KEY = 'idealTalentProfile';
const LOGIN_STORAGE_KEY = 'idealTalentLoginEmail';
const AUTH_STATE_KEY = 'idealTalentAuthState';

const loginForm = document.getElementById('login-form');
const loginFeedback = document.querySelector('.login__feedback');
const footerYear = document.getElementById('login-footer-year');

function safeParseJSON(value, fallback = null) {
    try {
        return value ? JSON.parse(value) : fallback;
    } catch (error) {
        console.warn('Não foi possível interpretar os dados salvos.', error);
        return fallback;
    }
}

function rememberLoginEmail(email) {
    if (email) {
        localStorage.setItem(LOGIN_STORAGE_KEY, email);
    }
}

function getStoredLoginEmail() {
    return localStorage.getItem(LOGIN_STORAGE_KEY) ?? '';
}

function saveProfile(profile) {
    if (profile) {
        localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
    }
}

function getStoredProfile() {
    return safeParseJSON(localStorage.getItem(PROFILE_STORAGE_KEY));
}

function setSessionAuthState(isAuthenticated) {
    try {
        if (isAuthenticated) {
            sessionStorage.setItem(AUTH_STATE_KEY, 'authenticated');
        } else {
            sessionStorage.removeItem(AUTH_STATE_KEY);
        }
    } catch (error) {
        console.warn('Não foi possível atualizar o estado de autenticação da sessão.', error);
    }
}

function isSessionAuthenticated() {
    try {
        return sessionStorage.getItem(AUTH_STATE_KEY) === 'authenticated';
    } catch (error) {
        console.warn('Não foi possível verificar o estado de autenticação.', error);
        return false;
    }
}

function candidateToProfile(candidate) {
    if (!candidate) {
        return null;
    }
    return {
        nome: candidate.nome,
        email: candidate.email,
        telefone: candidate.telefone ?? '',
        area: candidate.area ?? '',
        desejaAlertas: Boolean(candidate.desejaAlertas),
        curriculo: candidate.curriculo ?? '',
        atualizadoEm: candidate.atualizadoEm ?? new Date().toISOString(),
    };
}

async function authenticateCandidate(email, senha) {
    const response = await fetch(LOGIN_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, senha }),
    });

    let payload = null;
    try {
        payload = await response.json();
    } catch (error) {
        console.warn('Não foi possível interpretar a resposta de login.', error);
    }

    if (!response.ok) {
        const message = payload?.message ?? 'Não foi possível validar suas credenciais no momento.';
        throw new Error(message);
    }

    return payload?.candidate ?? null;
}

async function fetchCandidateByEmail(email) {
    if (!email) {
        return null;
    }

    const response = await fetch(`${PROFILE_ENDPOINT}/${encodeURIComponent(email)}`);
    if (!response.ok) {
        return null;
    }

    try {
        const payload = await response.json();
        return payload?.candidate ?? null;
    } catch (error) {
        console.warn('Não foi possível interpretar os dados do candidato.', error);
        return null;
    }
}

function syncProfile(candidate) {
    const profile = candidateToProfile(candidate);
    if (profile) {
        saveProfile(profile);
    }
    return profile;
}

function prefillEmailField() {
    const storedProfile = getStoredProfile();
    const storedEmail = storedProfile?.email ?? getStoredLoginEmail();
    if (storedEmail && loginForm) {
        const emailField = loginForm.elements.namedItem ? loginForm.elements.namedItem('email') : loginForm.querySelector('[name="email"]');
        if (emailField) {
            emailField.value = storedEmail;
        }
    }
}

function updateFooterYear() {
    if (footerYear) {
        footerYear.textContent = new Date().getFullYear();
    }
}

if (isSessionAuthenticated()) {
    window.location.replace('home.html');
}

prefillEmailField();
updateFooterYear();

loginForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!loginFeedback) {
        return;
    }

    const formData = new FormData(loginForm);
    const email = formData.get('email')?.toString().trim();
    const senha = formData.get('senha')?.toString().trim();

    if (!email || !senha) {
        loginFeedback.textContent = 'Informe seu e-mail e senha para continuar.';
        loginFeedback.style.color = '#dc2626';
        return;
    }

    loginFeedback.textContent = 'Validando credenciais...';
    loginFeedback.style.color = '#2563eb';

    try {
        const candidate = await authenticateCandidate(email, senha);
        const profile = syncProfile(candidate);
        rememberLoginEmail(email);
        if (!profile && candidate?.email) {
            const refreshed = await fetchCandidateByEmail(candidate.email);
            if (refreshed) {
                syncProfile(refreshed);
            }
        }

        setSessionAuthState(true);
        loginFeedback.textContent = 'Login realizado com sucesso! Redirecionando...';
        loginFeedback.style.color = '#16a34a';
        setTimeout(() => {
            window.location.href = 'home.html';
        }, 400);
    } catch (error) {
        setSessionAuthState(false);
        loginFeedback.textContent = error instanceof Error ? error.message : 'Não foi possível fazer login agora. Tente novamente em instantes.';
        loginFeedback.style.color = '#dc2626';
    }
});
