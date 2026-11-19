/* Utilidades JavaScript reutilizáveis do SoloSync (ES6+). */

function showFeedback(message, type = 'success') {
    const container = document.querySelector('.main-content');
    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    alert.setAttribute('role', 'alert');
    alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>`;
    container.prepend(alert);
}

function setupDeleteConfirmations() {
    document.querySelectorAll('[data-confirm-delete]').forEach((link) => {
        link.addEventListener('click', (event) => {
            const label = link.dataset.confirmDelete || 'este registro';
            if (!window.confirm(`Deseja realmente excluir ${label}? Esta ação não pode ser desfeita.`)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll('form.confirm-delete').forEach((form) => {
        form.addEventListener('submit', (event) => {
            if (!window.confirm('Deseja realmente excluir este registro? Esta ação não pode ser desfeita.')) {
                event.preventDefault();
            }
        });
    });
}

function setupFormValidation() {
    document.querySelectorAll('form[data-client-validation="true"]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                showFeedback('Corrija os campos destacados antes de salvar.', 'warning');
            }
            form.classList.add('was-validated');
        });

        form.querySelectorAll('[required]').forEach((field) => {
            field.addEventListener('input', () => {
                if (field.checkValidity()) field.classList.add('is-valid');
                else field.classList.remove('is-valid');
            });
        });
    });
}

function setupPlantioFields() {
    const status = document.getElementById('id_status');
    if (!status) return;

    const fields = ['id_cultura', 'id_variedade', 'id_data_plantio', 'id_ciclo_dias_estimado', 'id_ciclo_indeterminado']
        .map((id) => document.getElementById(id));

    const update = () => {
        const isPreparation = status.value === 'PREPARO';
        fields.forEach((field) => {
            if (!field) return;
            const container = field.closest('.mb-3');
            if (container) container.style.display = isPreparation ? 'none' : 'block';
        });
    };

    status.addEventListener('change', update);
    update();
}

function setupSimpleFilters() {
    document.querySelectorAll('[data-list-search]').forEach((input) => {
        const target = document.querySelector(input.dataset.listSearch);
        if (!target) return;
        const items = [...target.querySelectorAll('[data-searchable]')];

        input.addEventListener('input', () => {
            const term = input.value.trim().toLocaleLowerCase('pt-BR');
            let visible = 0;
            items.forEach((item) => {
                const match = (item.dataset.searchable || '').toLocaleLowerCase('pt-BR').includes(term);
                item.hidden = !match;
                if (match) visible += 1;
            });

            const counter = document.querySelector(input.dataset.searchCount);
            if (counter) counter.textContent = `${visible} registro(s) encontrado(s)`;
        });
    });
}

function setupFieldMasks() {
    const state = document.getElementById('id_estado');
    if (state) {
        state.addEventListener('input', () => {
            state.value = state.value.replace(/[^a-zA-Z]/g, '').toUpperCase().slice(0, 2);
        });
    }

    document.querySelectorAll('input[type="number"][step="0.01"], input[name="area_m2"]').forEach((field) => {
        field.addEventListener('blur', () => {
            if (field.value !== '' && field.valueAsNumber >= 0) {
                field.value = Number(field.value).toFixed(field.step === '0.01' ? 2 : 0);
            }
        });
    });
}

function setupCopyCoordinates() {
    document.querySelectorAll('[data-copy-coordinates]').forEach((button) => {
        button.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(button.dataset.copyCoordinates);
                showFeedback('Coordenadas copiadas.', 'success');
            } catch (_) {
                showFeedback('Não foi possível copiar as coordenadas.', 'warning');
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    setupDeleteConfirmations();
    setupFormValidation();
    setupPlantioFields();
    setupSimpleFilters();
    setupFieldMasks();
    setupCopyCoordinates();
});
