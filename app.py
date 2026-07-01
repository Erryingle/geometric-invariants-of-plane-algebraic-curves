"""
app.py - веб-сервер для проекта "Геометрические инварианты кривых"

Запускает Flask-приложение, принимает запросы от браузера,
вызывает математическое ядро и визуализатор, возвращает результаты.
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import time
import json
from math_core import parse_equation, find_singular_points, classify_singular_point, find_connected_components_binary, \
    compute_euler_characteristic
from visualizer import draw_curve

app = Flask(__name__)

# Создаём папку для картинок, если её нет
os.makedirs('plots', exist_ok=True)

# Максимальный размер загружаемого файла (на всякий случай)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


@app.route('/')
def index():
    """Главная страница с формой ввода"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Принимает уравнение, выполняет анализ и возвращает результаты в JSON.

    Ожидает: POST с полем 'equation'
    Возвращает: JSON с:
        - success: True/False
        - plot_url: путь к картинке
        - singular_points: список координат
        - classifications: список типов
        - euler_characteristic: число
        - num_components: число связных компонент
        - error: текст ошибки (если есть)
    """
    equation = request.form.get('equation', '').strip()

    # Проверка: уравнение не пустое
    if not equation:
        return jsonify({
            'success': False,
            'error': 'Пожалуйста, введите уравнение.'
        })

    # Границы по умолчанию
    bounds = (-5, 5, -5, 5)

    try:
        # Шаг 1: парсим уравнение
        derivatives = parse_equation(equation)

        # Шаг 2: ищем особые точки
        singular_points = find_singular_points(derivatives, bounds)

        # Шаг 3: классифицируем каждую точку
        classifications = []
        for point in singular_points:
            cls = classify_singular_point(point, derivatives)
            classifications.append(cls)

        # Шаг 4: считаем компоненты связности
        try:
            num_components = find_connected_components_binary(derivatives, bounds)
        except Exception as e:
            # Если не получилось посчитать компоненты, ставим значение по умолчанию
            print(f"Ошибка при подсчёте компонент: {e}")
            num_components = len(singular_points) + 1  # грубая оценка

        # Шаг 5: вычисляем эйлерову характеристику
        euler = compute_euler_characteristic(singular_points, classifications, num_components)

        # Шаг 6: рисуем график
        plot_filename = f"curve_{int(time.time())}_{hash(equation) % 10000}.png"
        plot_path = os.path.join('plots', plot_filename)

        draw_curve(
            equation,
            bounds=bounds,
            save_path=plot_path,
            resolution=300,
            show_legend=True
        )

        # Шаг 7: формируем ответ
        return jsonify({
            'success': True,
            'plot_url': f'/plots/{plot_filename}',
            'singular_points': [(round(p[0], 4), round(p[1], 4)) for p in singular_points],
            'classifications': classifications,
            'num_components': num_components,
            'euler_characteristic': euler,
            'equation': equation
        })

    except Exception as e:
        # Любая ошибка — возвращаем сообщение
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/plots/<filename>')
def serve_plot(filename):
    """Отдаёт сохранённый график"""
    return send_file(os.path.join('plots', filename))


@app.route('/examples')
def get_examples():
    """Возвращает список примеров для быстрого заполнения"""
    examples = [
        {'name': 'Окружность', 'equation': 'x**2 + y**2 - 1'},
        {'name': 'Узел (самопересечение)', 'equation': 'x**2 - y**2'},
        {'name': 'Касп (остриё)', 'equation': 'y**2 - x**3'},
        {'name': 'Изолированная точка', 'equation': 'x**2 + y**2'},
        {'name': 'Декартов лист', 'equation': 'x**3 + y**3 - 3*x*y'},
        {'name': 'Лемниската', 'equation': '(x**2 + y**2)**2 - (x**2 - y**2)'},
        {'name': 'Эллиптическая кривая', 'equation': 'y**2 - x**3 + x'},
        {'name': 'Астроида', 'equation': 'x**(2/3) + y**(2/3) - 1'},
        {'name': 'Ньютонов локон', 'equation': 'y**2 - x*(x**2 - 1)'},
        {'name': 'Трилистник', 'equation': '(x**2 + y**2)**2 - x*(x**2 - 3*y**2)'},
    ]
    return jsonify(examples)


@app.route('/about')
def about():
    """Страница с описанием проекта"""
    return jsonify({
        'name': 'Геометрические инварианты алгебраических кривых',
        'version': '1.0.0',
        'description': 'Инструмент для анализа особых точек и топологических инвариантов кривых F(x,y)=0',
        'authors': ['Студенты группы ...'],
        'features': [
            'Парсинг уравнений кривых',
            'Поиск особых точек (узлов, каспов, изолированных)',
            'Классификация особых точек по гессиану',
            'Вычисление эйлеровой характеристики',
            'Визуализация кривых с маркировкой особых точек'
        ]
    })


if __name__ == '__main__':
    print("=== Запуск сервера ===")
    print("Открой в браузере: http://127.0.0.1:5000")
    print("Нажми Ctrl+C для остановки")
    app.run(debug=True, host='0.0.0.0', port=5000)