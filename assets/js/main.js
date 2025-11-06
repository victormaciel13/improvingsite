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

    const arquivoValido =
        arquivo instanceof File &&
        arquivo.name &&
        ["pdf", "doc", "docx", "odt", "rtf"].some((extensao) => arquivo.name.toLowerCase().endsWith(extensao));

    if (!nome || !email || !area || !arquivoValido) {
        talentFeedback.textContent = 'Preencha nome, e-mail, área de interesse e anexe um currículo válido (PDF, DOC ou similar).';
        talentFeedback.style.color = '#dc2626';
        return;
    }

    const cadastroAnterior = localStorage.getItem('idealTalents');
    const talentPool = cadastroAnterior ? JSON.parse(cadastroAnterior) : [];
    talentPool.push({
        nome,
        email,
        telefone,
        area,
        desejaAlertas,
        curriculo: arquivo.name,
        criadoEm: new Date().toISOString()
    });
    localStorage.setItem('idealTalents', JSON.stringify(talentPool));

    talentFeedback.textContent = desejaAlertas
        ? 'Cadastro concluído! Você receberá alertas de novas vagas e um consultor entrará em contato em breve.'
        : 'Cadastro concluído! Entraremos em contato quando houver oportunidades compatíveis.';
    talentFeedback.style.color = '#16a34a';
    talentForm.reset();
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
