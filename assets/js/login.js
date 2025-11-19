const LOGIN_ENDPOINT = '/api/login';
const PROFILE_ENDPOINT = '/api/candidates';
const PROFILE_STORAGE_KEY = 'idealTalentProfile';
const LOGIN_STORAGE_KEY = 'idealTalentLoginEmail';
const AUTH_STATE_KEY = 'idealTalentAuthState';
const SESSION_USER_KEY = 'idealSessionUser';
const ALLOWED_RESUME_EXTENSIONS = ['pdf', 'doc', 'docx', 'odt', 'rtf'];

const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const loginFeedback = document.querySelector('.login__feedback');
const registerFeedback = document.querySelector('.register__feedback');
const registerAlertsToggle = document.getElementById('register-alertas');
const registerResumeInput = document.getElementById('register-curriculo');
const registerFileDisplay = document.querySelector('[data-register-file]');
const authToggleButtons = document.querySelectorAll('[data-auth-view]');
const authPanes = document.querySelectorAll('[data-auth-pane]');
const authTriggers = document.querySelectorAll('[data-auth-trigger]');
const footerYear = document.getElementById('login-footer-year');
const registerFileDefaultText = registerFileDisplay?.textContent?.trim() ||
    'Selecione um arquivo nos formatos permitidos.';

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

function setSessionUser(candidateLike) {
    try {
        if (!candidateLike || !candidateLike.email) {
            sessionStorage.removeItem(SESSION_USER_KEY);
            return;
        }

        const payload = {
            email: candidateLike.email ?? '',
            nome: candidateLike.nome ?? '',
            areaInteresse: candidateLike.areaInteresse ?? candidateLike.area ?? '',
        };

        sessionStorage.setItem(SESSION_USER_KEY, JSON.stringify(payload));
    } catch (error) {
        console.warn('Não foi possível atualizar o usuário da sessão.', error);
    }
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
        area: candidate.areaInteresse ?? candidate.area ?? '',
        desejaAlertas: Boolean(candidate.recebeAlertas ?? candidate.desejaAlertas),
        curriculo: candidate.curriculoPath ?? candidate.curriculo ?? '',
        atualizadoEm: candidate.atualizadoEm ?? new Date().toISOString(),
    };
}

function syncProfile(candidate) {
    const profile = candidateToProfile(candidate);
    if (profile) {
        saveProfile(profile);
    }
    return profile;
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

async function sendCandidateData(formData) {
    const response = await fetch(PROFILE_ENDPOINT, {
        method: 'POST',
        body: formData,
    });

    let payload = null;
    try {
        payload = await response.json();
    } catch (error) {
        console.warn('Não foi possível interpretar a resposta do cadastro.', error);
    }

    if (!response.ok) {
        const message = payload?.message ?? 'Não foi possível concluir o cadastro agora.';
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

async function syncCandidateAfterResponse(candidate, fallbackEmail) {
    const profile = syncProfile(candidate);
    const email = candidate?.email ?? fallbackEmail ?? '';
    const areaInteresse = candidate?.areaInteresse ?? candidate?.area ?? profile?.area ?? '';

    if (email) {
        rememberLoginEmail(email);
        setSessionUser({
            email,
            nome: candidate?.nome ?? profile?.nome ?? '',
            areaInteresse,
        });
    }

    if (!profile && email) {
        const refreshed = await fetchCandidateByEmail(email);
        if (refreshed) {
            setSessionUser({
                email: refreshed.email,
                nome: refreshed.nome,
                areaInteresse: refreshed.areaInteresse ?? refreshed.area ?? '',
            });
            return syncProfile(refreshed);
        }
    }

    return profile;
}

function prefillEmailFields() {
    const storedProfile = getStoredProfile();
    const storedEmail = storedProfile?.email ?? getStoredLoginEmail();

    if (storedEmail) {
        const loginEmailField = loginForm?.elements.namedItem
            ? loginForm.elements.namedItem('email')
            : loginForm?.querySelector('[name="email"]');
        if (loginEmailField) {
            loginEmailField.value = storedEmail;
        }

        const registerEmailField = registerForm?.elements.namedItem
            ? registerForm.elements.namedItem('email')
            : registerForm?.querySelector('[name="email"]');
        if (registerEmailField) {
            registerEmailField.value = storedEmail;
        }
    }
}

function updateFooterYear() {
    if (footerYear) {
        footerYear.textContent = new Date().getFullYear();
    }
}

function isValidResumeFile(file) {
    if (!file || typeof file !== 'object') {
        return false;
    }

    const fileName = typeof file.name === 'string' ? file.name : '';
    if (!fileName) {
        return false;
    }

    return ALLOWED_RESUME_EXTENSIONS.some((extension) =>
        fileName.toLowerCase().endsWith(extension)
    );
}

function updateRegisterFileDisplay(fileName) {
    if (!registerFileDisplay) {
        return;
    }

    registerFileDisplay.textContent = fileName ? fileName : registerFileDefaultText;
}

function showAuthPane(view, shouldFocus = true) {
    const normalizedView = view === 'register' ? 'register' : 'login';

    authToggleButtons.forEach((button) => {
        const target = button.dataset.authView;
        const isActive = target === normalizedView;
        button.classList.toggle('is-active', isActive);
        button.setAttribute('aria-selected', String(isActive));
    });

    authPanes.forEach((pane) => {
        const target = pane.dataset.authPane;
        const isActive = target === normalizedView;
        pane.classList.toggle('is-active', isActive);
        if (isActive) {
            pane.removeAttribute('hidden');
        } else {
            pane.setAttribute('hidden', '');
        }
    });

    if (!shouldFocus) {
        return;
    }

    if (normalizedView === 'register') {
        const firstField = registerForm?.querySelector('input, select');
        firstField?.focus();
    } else {
        const firstField = loginForm?.querySelector('input');
        firstField?.focus();
    }
}

if (isSessionAuthenticated()) {
    window.location.replace('home.html');
}

prefillEmailFields();
updateRegisterFileDisplay('');
updateFooterYear();

const initialView = window.location.hash.replace('#', '') === 'cadastro' ? 'register' : 'login';
showAuthPane(initialView, false);

authToggleButtons.forEach((button) => {
    button.addEventListener('click', () => {
        const targetView = button.dataset.authView ?? 'login';
        showAuthPane(targetView);
    });
});

authTriggers.forEach((trigger) => {
    trigger.addEventListener('click', (event) => {
        event.preventDefault();
        const targetView = trigger.dataset.authTrigger ?? 'login';
        showAuthPane(targetView);
    });
});

window.addEventListener('hashchange', () => {
    if (window.location.hash.replace('#', '') === 'cadastro') {
        showAuthPane('register', false);
    }
});

registerResumeInput?.addEventListener('change', () => {
    const file = registerResumeInput.files?.[0];
    updateRegisterFileDisplay(file?.name ?? '');
});

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
        await syncCandidateAfterResponse(candidate, email);
        setSessionAuthState(true);
        loginFeedback.textContent = 'Login realizado com sucesso! Redirecionando...';
        loginFeedback.style.color = '#16a34a';
        setTimeout(() => {
            window.location.href = 'home.html';
        }, 400);
    } catch (error) {
        setSessionAuthState(false);
        setSessionUser(null);
        loginFeedback.textContent = error instanceof Error
            ? error.message
            : 'Não foi possível fazer login agora. Tente novamente em instantes.';
        loginFeedback.style.color = '#dc2626';
    }
});

registerForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!registerFeedback) {
        return;
    }

    const formData = new FormData(registerForm);
    const nome = formData.get('nome')?.toString().trim();
    const email = formData.get('email')?.toString().trim();
    const senha = formData.get('senha')?.toString().trim();
    const area = formData.get('area')?.toString();
    const arquivo = formData.get('curriculo');

    if (!nome || !email || !area) {
        registerFeedback.textContent = 'Preencha nome, e-mail e área de interesse para continuar.';
        registerFeedback.style.color = '#dc2626';
        return;
    }

    if (!senha || senha.length < 6) {
        registerFeedback.textContent = 'Crie uma senha com pelo menos 6 caracteres.';
        registerFeedback.style.color = '#dc2626';
        return;
    }

    if (!isValidResumeFile(arquivo)) {
        registerFeedback.textContent = 'Anexe um currículo válido nos formatos PDF, DOC, DOCX, ODT ou RTF.';
        registerFeedback.style.color = '#dc2626';
        return;
    }

    registerFeedback.textContent = 'Criando sua conta...';
    registerFeedback.style.color = '#2563eb';

    try {
        formData.set('nome', nome);
        formData.set('email', email);
        formData.set('senha', senha);
        if (registerAlertsToggle && !registerAlertsToggle.checked) {
            formData.delete('alertas');
        }

        const candidate = await sendCandidateData(formData);
        await syncCandidateAfterResponse(candidate, email);
        setSessionAuthState(true);
        registerFeedback.textContent = 'Cadastro concluído! Redirecionando para a plataforma...';
        registerFeedback.style.color = '#16a34a';
        registerForm.reset();
        updateRegisterFileDisplay('');
        setTimeout(() => {
            window.location.href = 'home.html';
        }, 500);
    } catch (error) {
        setSessionAuthState(false);
        setSessionUser(null);
        registerFeedback.textContent = error instanceof Error
            ? error.message
            : 'Não foi possível concluir o cadastro agora. Tente novamente em instantes.';
        registerFeedback.style.color = '#dc2626';
    }
});
