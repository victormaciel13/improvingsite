const navToggle = document.querySelector('.main-nav__toggle');
const navMenu = document.querySelector('.main-nav ul');
const backToTop = document.querySelector('.back-to-top');
const jobCards = document.querySelectorAll('.job-card');
const filtroArea = document.getElementById('filtro-area');
const filtroModalidade = document.getElementById('filtro-modalidade');
const newsletterForm = document.querySelector('.newsletter__form');
const newsletterFeedback = document.querySelector('.newsletter__feedback');
const talentForm = document.getElementById('talent-form');
const talentFeedback = document.querySelector('.talent__feedback');
const contactForm = document.querySelector('.contact__form');
const formFeedback = document.querySelector('.form__feedback');
const favoritoButtons = document.querySelectorAll('[data-action="favorito"]');
const candidatarButtons = document.querySelectorAll('[data-action="candidatar"]');
const profileForm = document.getElementById('profile-form');
const profileFeedback = document.querySelector('.profile__feedback');
const profileFields = {
    nome: document.querySelector('[data-profile-field="nome"]'),
    email: document.querySelector('[data-profile-field="email"]'),
    telefone: document.querySelector('[data-profile-field="telefone"]'),
    area: document.querySelector('[data-profile-field="area"]'),
    alertas: document.querySelector('[data-profile-field="alertas"]'),
    atualizado: document.querySelector('[data-profile-field="atualizado"]')
};
const profileFileDisplay = document.querySelector('[data-profile-file]');
const profileAlertsToggle = document.getElementById('profile-alertas');
const profileAreaSelect = document.getElementById('profile-area');
const profileResumeInput = document.getElementById('profile-curriculo');
const talentAlertsToggle = document.getElementById('talent-alertas');

const API_ENDPOINT = '/api/candidates';
const PROFILE_STORAGE_KEY = 'idealTalentProfile';
const LOGIN_STORAGE_KEY = 'idealTalentLoginEmail';
const AUTH_STATE_KEY = 'idealTalentAuthState';
const APPLIED_JOBS_KEY = 'idealAppliedJobs';
const ALLOWED_RESUME_EXTENSIONS = ['pdf', 'doc', 'docx', 'odt', 'rtf'];

function safeParseJSON(value, fallback) {
    try {
        return value ? JSON.parse(value) : fallback;
    } catch (error) {
        console.warn('Não foi possível interpretar os dados salvos.', error);
        return fallback;
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
    return ALLOWED_RESUME_EXTENSIONS.some((ext) => fileName.toLowerCase().endsWith(ext));
}

function getStoredProfile() {
    const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
    return safeParseJSON(stored, null);
}

function saveProfile(profile) {
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
}

function getAppliedJobs() {
    try {
        const stored = localStorage.getItem(APPLIED_JOBS_KEY);
        const parsed = safeParseJSON(stored, []);
        return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
        console.warn('Não foi possível recuperar as vagas candidatas.', error);
        return [];
    }
}

function saveAppliedJobs(jobIds) {
    try {
        const unique = Array.from(new Set(jobIds));
        localStorage.setItem(APPLIED_JOBS_KEY, JSON.stringify(unique));
    } catch (error) {
        console.warn('Não foi possível registrar as vagas candidatas.', error);
    }
}

function rememberLoginEmail(email) {
    if (email) {
        localStorage.setItem(LOGIN_STORAGE_KEY, email);
    }
}

function isSessionAuthenticated() {
    try {
        return sessionStorage.getItem(AUTH_STATE_KEY) === 'authenticated';
    } catch (error) {
        console.warn('Não foi possível verificar o estado de autenticação da sessão.', error);
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

function formatProfileDate(dateString) {
    if (!dateString) {
        return 'Nenhum cadastro encontrado';
    }

    const parsed = new Date(dateString);
    if (Number.isNaN(parsed.getTime())) {
        return 'Nenhum cadastro encontrado';
    }

    return parsed.toLocaleString('pt-BR', {
        dateStyle: 'long',
        timeStyle: 'short'
    });
}

function clearJobHighlights() {
    jobCards.forEach((card) => card.classList.remove('job-card--highlight'));
}

function applyAreaRecommendations(area) {
    clearJobHighlights();

    if (!area) {
        return;
    }

    const normalizedArea = String(area).trim();
    const matches = Array.from(jobCards).filter((card) => card.dataset.area === normalizedArea);
    matches.forEach((card) => card.classList.add('job-card--highlight'));
}

function getAreaLabel(value) {
    if (!value) {
        return '—';
    }
    const option = profileAreaSelect?.querySelector(`option[value="${value}"]`);
    return option ? option.textContent : value;
}

function getJobFeedbackElement(jobId) {
    if (!jobId) {
        return null;
    }
    return document.querySelector(`[data-job-feedback="${jobId}"]`);
}

function updateJobApplicationUI(jobCard, jobId, jobTitle, alreadyApplied) {
    if (!jobId) {
        return;
    }

    const feedback = getJobFeedbackElement(jobId);
    if (feedback) {
        const normalizedTitle = jobTitle || 'esta vaga';
        feedback.textContent = alreadyApplied
            ? `Você já se inscreveu para ${normalizedTitle}. Seu currículo está em análise.`
            : `Inscrição registrada para ${normalizedTitle}. Seu currículo está em análise.`;
        feedback.hidden = false;
    }

    if (jobCard) {
        jobCard.classList.add('job-card--applied');
    }

    const applyButton = jobCard?.querySelector('[data-action="candidatar"]');
    if (applyButton) {
        applyButton.classList.add('is-applied');
        applyButton.textContent = 'Currículo em análise';
    }
}

function restoreAppliedJobs() {
    const appliedJobs = getAppliedJobs();
    appliedJobs.forEach((jobId) => {
        const jobCard = document.getElementById(jobId);
        if (!jobCard) {
            return;
        }
        const jobTitle = jobCard.querySelector('h3')?.textContent?.trim();
        updateJobApplicationUI(jobCard, jobId, jobTitle, true);
    });
}

function updateProfileUI(profile) {
    const hasProfile = Boolean(profile);
    profileFields.nome && (profileFields.nome.textContent = hasProfile ? profile.nome : 'Cadastre-se para preencher seu perfil.');
    profileFields.email && (profileFields.email.textContent = hasProfile && profile.email ? profile.email : '—');
    profileFields.telefone && (profileFields.telefone.textContent = hasProfile && profile.telefone ? profile.telefone : '—');
    profileFields.area && (profileFields.area.textContent = hasProfile ? getAreaLabel(profile.area) : '—');
    profileFields.alertas &&
        (profileFields.alertas.textContent = hasProfile ? (profile.desejaAlertas ? 'Ativados' : 'Desativados') : '—');
    profileFields.atualizado &&
        (profileFields.atualizado.textContent = hasProfile ? formatProfileDate(profile.atualizadoEm) : 'Nenhum cadastro encontrado');

    if (profileForm) {
        const formElements = profileForm.elements;
        const nomeInput = formElements.namedItem ? formElements.namedItem('nome') : null;
        const emailInput = formElements.namedItem ? formElements.namedItem('email') : null;
        const telefoneInput = formElements.namedItem ? formElements.namedItem('telefone') : null;

        if (nomeInput) {
            nomeInput.value = hasProfile && profile.nome ? profile.nome : '';
        }
        if (emailInput) {
            emailInput.value = hasProfile && profile.email ? profile.email : '';
        }
        if (telefoneInput) {
            telefoneInput.value = hasProfile && profile.telefone ? profile.telefone : '';
        }
        if (profileAreaSelect) {
            profileAreaSelect.value = hasProfile && profile.area ? profile.area : '';
        }
        if (profileAlertsToggle) {
            profileAlertsToggle.checked = Boolean(hasProfile && profile.desejaAlertas);
        }
    }

    if (profileFileDisplay) {
        profileFileDisplay.textContent = hasProfile && profile.curriculo ? profile.curriculo : 'Nenhum arquivo cadastrado';
    }

    if (profileResumeInput) {
        profileResumeInput.value = '';
    }

    applyAreaRecommendations(profile?.area);
}

function syncProfileFromCandidate(candidate) {
    const profileData = candidateToProfile(candidate);
    if (profileData) {
        rememberLoginEmail(profileData.email);
        saveProfile(profileData);
        updateProfileUI(profileData);
    }
    return profileData;
}

function initializeProfile() {
    const storedProfile = getStoredProfile();
    updateProfileUI(storedProfile);
    if (storedProfile?.email) {
        fetchCandidateByEmail(storedProfile.email)
            .then((candidate) => {
                if (candidate) {
                    syncProfileFromCandidate(candidate);
                }
            })
            .catch((error) => {
                console.warn('Não foi possível sincronizar o cadastro salvo.', error);
            });
    }
}

if (!isSessionAuthenticated()) {
    window.location.replace('index.html');
} else {
    initializeProfile();
    restoreAppliedJobs();
}

async function sendCandidateData(formData) {
    if (formData.get('alertas') == null) {
        formData.set('alertas', 'nao');
    }

    const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        body: formData
    });

    let payload = null;
    try {
        payload = await response.json();
    } catch (error) {
        console.warn('Não foi possível interpretar a resposta do servidor.', error);
    }

    if (!response.ok) {
        const message = payload?.message ?? 'Não foi possível salvar seu cadastro. Tente novamente mais tarde.';
        throw new Error(message);
    }

    return payload?.candidate ?? null;
}

async function fetchCandidateByEmail(email) {
    if (!email) {
        return null;
    }

    const response = await fetch(`${API_ENDPOINT}/${encodeURIComponent(email)}`);
    if (!response.ok) {
        return null;
    }

    const payload = await response.json();
    return payload?.candidate ?? null;
}

function toggleMenu() {
    const expanded = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!expanded));
    navMenu.classList.toggle('is-open');
}

if (navToggle) {
    navToggle.addEventListener('click', toggleMenu);
}

navMenu?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
        if (window.innerWidth <= 768 && navMenu.classList.contains('is-open')) {
            toggleMenu();
        }
    });
});

function handleScroll() {
    if (window.scrollY > 600) {
        backToTop.classList.add('is-visible');
        backToTop.style.opacity = '1';
    } else {
        backToTop.classList.remove('is-visible');
        backToTop.style.opacity = '0';
    }
}

window.addEventListener('scroll', handleScroll);

backToTop?.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

function filtrarVagas() {
    const area = filtroArea?.value ?? 'todos';
    const modalidade = filtroModalidade?.value ?? 'todas';

    jobCards.forEach((card) => {
        const cardArea = card.dataset.area;
        const cardModalidade = card.dataset.modalidade;
        const matchesArea = area === 'todos' || cardArea === area;
        const matchesModalidade = modalidade === 'todas' || cardModalidade === modalidade;
        card.style.display = matchesArea && matchesModalidade ? 'grid' : 'none';
    });
}

[filtroArea, filtroModalidade].forEach((select) => {
    select?.addEventListener('change', filtrarVagas);
});

favoritoButtons.forEach((button) => {
    button.addEventListener('click', () => {
        const isPressed = button.getAttribute('aria-pressed') === 'true';
        button.setAttribute('aria-pressed', String(!isPressed));
        button.textContent = isPressed ? 'Salvar vaga' : 'Vaga salva';
        button.classList.toggle('is-active');
    });
});

candidatarButtons.forEach((button) => {
    button.addEventListener('click', (event) => {
        event.preventDefault();
        const jobCard = button.closest('.job-card');
        const jobId = jobCard?.id || button.dataset.jobTarget?.replace('#', '');
        const jobTitle = button.dataset.jobTitle || jobCard?.querySelector('h3')?.textContent?.trim();
        const appliedJobs = getAppliedJobs();
        const alreadyApplied = jobId ? appliedJobs.includes(jobId) : false;

        if (jobId && !alreadyApplied) {
            appliedJobs.push(jobId);
            saveAppliedJobs(appliedJobs);
        }

        updateJobApplicationUI(jobCard, jobId, jobTitle, alreadyApplied);
        if (typeof button.blur === 'function') {
            button.blur();
        }
    });
});

newsletterForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const formData = new FormData(newsletterForm);
    const nome = formData.get('nome');
    const email = formData.get('email');

    if (!nome || !email) {
        newsletterFeedback.textContent = 'Por favor, preencha nome e e-mail para continuar.';
        newsletterFeedback.style.color = '#dc2626';
        return;
    }

    newsletterFeedback.textContent = 'Inscrição realizada com sucesso! Você receberá nossas novidades em breve.';
    newsletterFeedback.style.color = '#16a34a';
    newsletterForm.reset();
});

talentForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!talentFeedback) {
        return;
    }

    const formData = new FormData(talentForm);
    const nome = formData.get('nome')?.toString().trim();
    const email = formData.get('email')?.toString().trim();
    const senha = formData.get('senha')?.toString().trim();
    const area = formData.get('area')?.toString();
    const arquivo = formData.get('curriculo');

    if (!nome || !email || !area || !isValidResumeFile(arquivo)) {
        talentFeedback.textContent = 'Preencha nome, e-mail, área de interesse e anexe um currículo válido (PDF, DOC, DOCX, ODT ou RTF).';
        talentFeedback.style.color = '#dc2626';
        return;
    }

    if (!senha || senha.length < 6) {
        talentFeedback.textContent = 'Crie uma senha com pelo menos 6 caracteres para acessar suas recomendações.';
        talentFeedback.style.color = '#dc2626';
        return;
    }

    talentFeedback.textContent = 'Enviando seu cadastro...';
    talentFeedback.style.color = '#2563eb';

    try {
        formData.set('nome', nome);
        formData.set('email', email);
        formData.set('senha', senha);
        if (talentAlertsToggle && !talentAlertsToggle.checked) {
            formData.delete('alertas');
        }

        const candidate = await sendCandidateData(formData);
        const profileData = syncProfileFromCandidate(candidate);

        const desejaAlertas = profileData?.desejaAlertas;
        talentFeedback.textContent = desejaAlertas
            ? 'Cadastro concluído! Você receberá alertas de novas vagas e um consultor entrará em contato em breve.'
            : 'Cadastro concluído! Entraremos em contato quando houver oportunidades compatíveis.';
        talentFeedback.style.color = '#16a34a';
        talentForm.reset();
    } catch (error) {
        talentFeedback.textContent = error instanceof Error ? error.message : 'Não foi possível enviar seu cadastro agora. Tente novamente mais tarde.';
        talentFeedback.style.color = '#dc2626';
    }
});

profileForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!profileFeedback) {
        return;
    }

    const formData = new FormData(profileForm);
    const nome = formData.get('nome')?.toString().trim();
    const email = formData.get('email')?.toString().trim();
    const senha = formData.get('senha')?.toString().trim();
    const area = formData.get('area')?.toString();
    const arquivo = formData.get('curriculo');

    if (!nome || !email || !area) {
        profileFeedback.textContent = 'Informe nome, e-mail e área de interesse para atualizar seu cadastro.';
        profileFeedback.style.color = '#dc2626';
        return;
    }

    if (senha && senha.length < 6) {
        profileFeedback.textContent = 'A nova senha precisa ter pelo menos 6 caracteres.';
        profileFeedback.style.color = '#dc2626';
        return;
    }

    const hasNewFile = arquivo && typeof arquivo === 'object' && typeof arquivo.name === 'string' && arquivo.name !== '';

    if (hasNewFile && !isValidResumeFile(arquivo)) {
        profileFeedback.textContent = 'Selecione um currículo válido (PDF, DOC, DOCX, ODT ou RTF).';
        profileFeedback.style.color = '#dc2626';
        return;
    }

    if (!hasNewFile) {
        formData.delete('curriculo');
    }

    formData.set('nome', nome);
    formData.set('email', email);
    if (senha) {
        formData.set('senha', senha);
    } else {
        formData.delete('senha');
    }

    if (profileAlertsToggle && !profileAlertsToggle.checked) {
        formData.delete('alertas');
    }

    profileFeedback.textContent = 'Salvando seu perfil...';
    profileFeedback.style.color = '#2563eb';

    try {
        const candidate = await sendCandidateData(formData);
        syncProfileFromCandidate(candidate);
        profileFeedback.textContent = 'Perfil atualizado com sucesso! Suas preferências foram salvas.';
        profileFeedback.style.color = '#16a34a';
    } catch (error) {
        profileFeedback.textContent = error instanceof Error ? error.message : 'Não foi possível atualizar seu perfil agora.';
        profileFeedback.style.color = '#dc2626';
    }
});

profileResumeInput?.addEventListener('change', () => {
    if (!profileFileDisplay) {
        return;
    }
    const file = profileResumeInput.files?.[0];
    if (file) {
        profileFileDisplay.textContent = file.name;
    } else {
        const storedProfile = getStoredProfile();
        profileFileDisplay.textContent = storedProfile?.curriculo ?? 'Nenhum arquivo cadastrado';
    }
});

contactForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const formData = new FormData(contactForm);
    const nome = formData.get('nome');
    const email = formData.get('email');
    const mensagem = formData.get('mensagem');

    if (!nome || !email || !mensagem) {
        formFeedback.textContent = 'Preencha nome, e-mail e mensagem para que possamos responder rapidamente.';
        formFeedback.style.color = '#dc2626';
        return;
    }

    formFeedback.textContent = 'Recebemos sua mensagem! Nosso time retornará em até 1 dia útil.';
    formFeedback.style.color = '#16a34a';
    contactForm.reset();
});

const observerOptions = {
    threshold: 0.1
};

const revealElements = document.querySelectorAll('section, .card, .job-card, .service-card');

const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

revealElements.forEach((element) => {
    element.classList.add('will-animate');
    observer.observe(element);
});

const assistantChat = document.querySelector('[data-assistant-chat]');
const assistantLauncher = assistantChat?.querySelector('[data-assistant-launcher]');
const assistantWindow = assistantChat?.querySelector('[data-assistant-window]');
const assistantClose = assistantChat?.querySelector('[data-assistant-close]');
const assistantMessages = assistantChat?.querySelector('[data-assistant-messages]');
const assistantForm = assistantChat?.querySelector('[data-assistant-form]');
const assistantInput = assistantChat?.querySelector('[data-assistant-input]');
const assistantQuickActions = assistantChat?.querySelectorAll('[data-assistant-question]');
let assistantHasWelcomed = false;

const assistantAnswers = [
    {
        triggers: ['cadastro', 'registrar', 'inscrever', 'conta'],
        response:
            'Para se cadastrar, acesse a seção “Cadastre seu currículo”, preencha seus dados, anexe o currículo e escolha se deseja receber alertas. Assim que salvar, você poderá acompanhar tudo na área "Meu perfil".',
    },
    {
        triggers: ['recomendacoes', 'recomendação', 'recomendado', 'alerta', 'novas vagas', 'newsletter'],
        response:
            'Depois de fazer login, destacamos vagas alinhadas ao seu perfil e enviamos alertas por e-mail quando você ativa essa opção no cadastro.',
    },
    {
        triggers: ['curriculo', 'currículo', 'atualizar', 'documento'],
        response:
            'Você pode atualizar currículo, dados pessoais e preferências acessando a seção "Meu perfil". Basta enviar o novo arquivo e salvar para manter tudo em dia.',
    },
    {
        triggers: ['login', 'senha', 'acesso'],
        response:
            'Se esqueceu a senha, refaça o cadastro usando o mesmo e-mail com uma nova senha. Continuamos protegendo seus dados com criptografia e você recupera o acesso imediatamente.',
    },
    {
        triggers: ['contato', 'whatsapp', 'telefone'],
        response:
            'Nosso time está disponível pelo WhatsApp (11) 3539-1330 e pelo formulário de contato. Envie sua mensagem e retornaremos rapidamente.',
    },
];

const quickPrompts = {
    cadastro: {
        question: 'Como faço meu cadastro?',
        response:
            'Para se cadastrar, clique na seção “Cadastre seu currículo”, informe seus dados, defina uma senha e anexe o currículo. Em seguida, você já pode acompanhar tudo em "Meu perfil".',
    },
    recomendacoes: {
        question: 'Receberei vagas recomendadas?',
        response:
            'Sim! Assim que entrar na plataforma autenticado, destacamos vagas alinhadas à sua área e enviamos alertas por e-mail quando essa opção está ativada.',
    },
    curriculo: {
        question: 'Posso atualizar meu currículo?',
        response:
            'Claro. Abra "Meu perfil", envie um novo currículo e salve as alterações. O arquivo anterior é substituído com segurança e você mantém o histórico atualizado.',
    },
};

function getAssistantReply(message) {
    if (!message) {
        return 'Posso ajudar com cadastro, vagas recomendadas, atualizações de currículo ou dúvidas sobre o contato da Ideal Empregos.';
    }

    const normalized = message.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
    const knowledge = assistantAnswers.find((entry) =>
        entry.triggers.some((trigger) => normalized.includes(trigger.normalize('NFD').replace(/\p{Diacritic}/gu, '')))
    );

    return (
        knowledge?.response ??
        'Ainda não entendi totalmente, mas nosso formulário de contato e o WhatsApp (11) 3539-1330 estão à disposição para qualquer dúvida específica.'
    );
}

function appendAssistantMessage(role, text) {
    if (!assistantMessages || !text) {
        return;
    }

    const item = document.createElement('li');
    const bubble = document.createElement('div');
    const bubbleRole = role === 'user' ? 'user' : 'assistant';
    item.classList.add('assistant-chat__message');
    bubble.classList.add('assistant-chat__bubble', `assistant-chat__bubble--${bubbleRole}`);
    bubble.textContent = text;
    item.appendChild(bubble);
    assistantMessages.appendChild(item);
    assistantMessages.scrollTop = assistantMessages.scrollHeight;
}

function setAssistantOpen(isOpen) {
    if (!assistantChat || !assistantWindow || !assistantLauncher) {
        return;
    }

    assistantChat.classList.toggle('assistant-chat--open', isOpen);
    assistantWindow.setAttribute('aria-hidden', String(!isOpen));

    if (isOpen) {
        assistantWindow.removeAttribute('hidden');
        assistantLauncher.setAttribute('aria-expanded', 'true');
        if (!assistantHasWelcomed) {
            appendAssistantMessage('assistant', 'Olá! Sou o assistente virtual da Ideal Empregos. Como posso ajudar hoje?');
            assistantHasWelcomed = true;
        }
        setTimeout(() => assistantInput?.focus(), 50);
    } else {
        assistantWindow.setAttribute('hidden', '');
        assistantLauncher.setAttribute('aria-expanded', 'false');
    }
}

assistantWindow?.setAttribute('hidden', '');

assistantLauncher?.addEventListener('click', () => {
    const isOpen = assistantChat?.classList.contains('assistant-chat--open');
    setAssistantOpen(!isOpen);
});

assistantClose?.addEventListener('click', () => setAssistantOpen(false));

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && assistantChat?.classList.contains('assistant-chat--open')) {
        setAssistantOpen(false);
        assistantLauncher?.focus();
    }
});

assistantForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const value = assistantInput?.value?.trim();

    if (!value) {
        return;
    }

    appendAssistantMessage('user', value);
    assistantInput.value = '';

    const reply = getAssistantReply(value);
    setTimeout(() => {
        appendAssistantMessage('assistant', reply);
    }, 200);
});

assistantQuickActions?.forEach((button) => {
    button.addEventListener('click', () => {
        const key = button.dataset.assistantQuestion;
        const prompt = key ? quickPrompts[key] : null;
        const question = prompt?.question ?? button.textContent ?? '';
        const response = prompt?.response ?? getAssistantReply(question);

        setAssistantOpen(true);
        if (question) {
            appendAssistantMessage('user', question);
        }

        setTimeout(() => {
            appendAssistantMessage('assistant', response);
        }, 150);
    });
});
