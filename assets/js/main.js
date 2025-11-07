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

const TALENT_STORAGE_KEY = 'idealTalents';
const PROFILE_STORAGE_KEY = 'idealTalentProfile';
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

function getAreaLabel(value) {
    if (!value) {
        return '—';
    }
    const option = profileAreaSelect?.querySelector(`option[value="${value}"]`);
    return option ? option.textContent : value;
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
}

function initializeProfile() {
    const storedProfile = getStoredProfile();
    updateProfileUI(storedProfile);
}

function syncProfileFromTalent(talentData) {
    const profileData = {
        ...talentData,
        atualizadoEm: new Date().toISOString()
    };
    saveProfile(profileData);
    updateProfileUI(profileData);
}

initializeProfile();

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

talentForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    if (!talentFeedback) {
        return;
    }
    const formData = new FormData(talentForm);
    const nome = formData.get('nome')?.toString().trim();
    const email = formData.get('email')?.toString().trim();
    const area = formData.get('area')?.toString();
    const telefone = formData.get('telefone')?.toString().trim();
    const desejaAlertas = formData.get('alertas') === 'sim';
    const arquivo = formData.get('curriculo');

    if (!nome || !email || !area || !isValidResumeFile(arquivo)) {
        talentFeedback.textContent = 'Preencha nome, e-mail, área de interesse e anexe um currículo válido (PDF, DOC, DOCX, ODT ou RTF).';
        talentFeedback.style.color = '#dc2626';
        return;
    }

    const talentPool = safeParseJSON(localStorage.getItem(TALENT_STORAGE_KEY), []);
    talentPool.push({
        nome,
        email,
        telefone,
        area,
        desejaAlertas,
        curriculo: arquivo.name,
        criadoEm: new Date().toISOString()
    });
    localStorage.setItem(TALENT_STORAGE_KEY, JSON.stringify(talentPool));

    syncProfileFromTalent({
        nome,
        email,
        telefone,
        area,
        desejaAlertas,
        curriculo: arquivo.name
    });

    talentFeedback.textContent = desejaAlertas
        ? 'Cadastro concluído! Você receberá alertas de novas vagas e um consultor entrará em contato em breve.'
        : 'Cadastro concluído! Entraremos em contato quando houver oportunidades compatíveis.';
    talentFeedback.style.color = '#16a34a';
    talentForm.reset();
});

profileForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    if (!profileFeedback) {
        return;
    }

    const formData = new FormData(profileForm);
    const nome = formData.get('nome')?.toString().trim();
    const email = formData.get('email')?.toString().trim();
    const telefone = formData.get('telefone')?.toString().trim();
    const area = formData.get('area')?.toString();
    const desejaAlertas = formData.get('alertas') === 'sim';
    const arquivo = formData.get('curriculo');
    const storedProfile = getStoredProfile();

    if (!nome || !email || !area) {
        profileFeedback.textContent = 'Informe nome, e-mail e área de interesse para atualizar seu cadastro.';
        profileFeedback.style.color = '#dc2626';
        return;
    }

    const hasNewFile = arquivo && typeof arquivo === 'object' && typeof arquivo.name === 'string' && arquivo.name !== '';

    if (hasNewFile && !isValidResumeFile(arquivo)) {
        profileFeedback.textContent = 'Selecione um currículo válido (PDF, DOC, DOCX, ODT ou RTF).';
        profileFeedback.style.color = '#dc2626';
        return;
    }

    const curriculoNome = hasNewFile ? arquivo.name : storedProfile?.curriculo ?? '';

    const profileData = {
        nome,
        email,
        telefone,
        area,
        desejaAlertas,
        curriculo: curriculoNome,
        atualizadoEm: new Date().toISOString()
    };

    saveProfile(profileData);
    updateProfileUI(profileData);
    profileFeedback.textContent = 'Perfil atualizado com sucesso! Suas preferências foram salvas.';
    profileFeedback.style.color = '#16a34a';
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
