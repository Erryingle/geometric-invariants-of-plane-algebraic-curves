/**
 * script.js - клиентская логика для проекта
 */

document.addEventListener('DOMContentLoaded', () => {
    // ===== DOM-элементы =====
    const form = document.getElementById('analysis-form');
    const equationInput = document.getElementById('equation');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsSection = document.getElementById('results');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const plotImage = document.getElementById('plot-image');
    const displayEquation = document.getElementById('display-equation');
    const pointsCount = document.getElementById('points-count');
    const pointsList = document.getElementById('points-list');
    const componentsCount = document.getElementById('components-count');
    const eulerValue = document.getElementById('euler-value');
    const downloadBtn = document.getElementById('download-btn');

    // ===== Загрузка примеров =====
    async function loadExamples() {
        try {
            const response = await fetch('/examples');
            const examples = await response.json();

            const container = document.getElementById('examples-list');
            container.innerHTML = '';

            examples.forEach(ex => {
                const tag = document.createElement('span');
                tag.className = 'example-tag';
                tag.textContent = ex.name;
                tag.dataset.equation = ex.equation;
                tag.addEventListener('click', () => {
                    equationInput.value = ex.equation;
                    // Автоматически отправляем форму
                    form.dispatchEvent(new Event('submit'));
                });
                container.appendChild(tag);
            });
        } catch (err) {
            console.warn('Не удалось загрузить примеры:', err);
        }
    }

    // ===== Отправка формы =====
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const equation = equationInput.value.trim();
        if (!equation) {
            showError('Введите уравнение кривой.');
            return;
        }

        // Показываем лоадер
        setLoading(true);
        hideError();
        hideResults();

        try {
            const formData = new FormData();
            formData.append('equation', equation);

            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showResults(data);
            } else {
                showError(data.error || 'Неизвестная ошибка.');
            }
        } catch (err) {
            showError('Ошибка соединения с сервером. Проверьте, запущен ли сервер.');
            console.error('Network error:', err);
        } finally {
            setLoading(false);
        }
    });

    // ===== Отображение результатов =====
    function showResults(data) {
        // График
        plotImage.src = data.plot_url + '?t=' + Date.now(); // кеш-бастер
        plotImage.alt = `График кривой ${data.equation}`;

        // Уравнение
        displayEquation.textContent = data.equation;

        // Особые точки
        const points = data.singular_points;
        const types = data.classifications;
        pointsCount.textContent = points.length;

        const typeLabels = {
            'node': 'Узел',
            'cusp': 'Касп',
            'isolated': 'Изолированная',
            'degenerate': 'Вырожденная'
        };

        const typeClasses = {
            'node': 'node',
            'cusp': 'cusp',
            'isolated': 'isolated',
            'degenerate': 'degenerate'
        };

        pointsList.innerHTML = '';
        if (points.length === 0) {
            pointsList.innerHTML = '<p style="color:#94a3b8;font-size:14px;">Особых точек не найдено</p>';
        } else {
            points.forEach((p, i) => {
                const li = document.createElement('li');
                li.className = 'point-item';
                const cls = types[i] || 'degenerate';
                li.innerHTML = `
                    <span class="coords">(${p[0]}, ${p[1]})</span>
                    <span class="type-badge ${typeClasses[cls] || 'degenerate'}">${typeLabels[cls] || cls}</span>
                `;
                pointsList.appendChild(li);
            });
        }

        // Компоненты связности
        componentsCount.textContent = data.num_components;

        // Эйлерова характеристика
        eulerValue.textContent = data.euler_characteristic;

        // Показываем секцию результатов
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    // ===== Ошибки =====
    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'flex';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    // ===== Лоадер =====
    function setLoading(loading) {
        const btnText = analyzeBtn.querySelector('.btn-text');
        const loader = analyzeBtn.querySelector('.loader');

        if (loading) {
            analyzeBtn.disabled = true;
            btnText.style.display = 'none';
            loader.style.display = 'inline-block';
        } else {
            analyzeBtn.disabled = false;
            btnText.style.display = 'inline';
            loader.style.display = 'none';
        }
    }

    // ===== Скачивание графика =====
    downloadBtn.addEventListener('click', () => {
        const imgSrc = plotImage.src;
        if (imgSrc && !imgSrc.includes('data:image')) {
            // Создаём ссылку для скачивания
            const link = document.createElement('a');
            link.href = imgSrc;
            link.download = `curve_${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    });

    // ===== Клавиша Enter на поле ввода =====
    equationInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });

    // ===== Загрузка примеров при старте =====
    loadExamples();

    // ===== Если есть уравнение в URL-параметрах =====
    const urlParams = new URLSearchParams(window.location.search);
    const eqParam = urlParams.get('eq');
    if (eqParam) {
        equationInput.value = decodeURIComponent(eqParam);
        form.dispatchEvent(new Event('submit'));
    }

    console.log('✅ Curve Invariants UI загружен');
});