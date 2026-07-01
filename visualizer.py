"""
visualizer.py - модуль визуализации для проекта "Геометрические инварианты кривых"

Отрисовывает:
- неявную кривую F(x,y)=0 (методом contour)
- особые точки с цветовой маркировкой по типу
- подписи типов точек
- легенду и сетку
- сохраняет результат в PNG (и опционально SVG)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import List, Tuple, Dict, Optional
import os

# Импортируем наше математическое ядро
from math_core import parse_equation, find_singular_points, classify_singular_point

# ========== НАСТРОЙКИ СТИЛЕЙ ==========
# Цвета для разных типов особых точек
COLORS = {
    'node': '#e63946',  # ярко-красный (узел)
    'cusp': '#f39c12',  # оранжевый (касп)
    'isolated': '#9b59b6',  # фиолетовый (изолированная)
    'degenerate': '#95a5a6'  # серый (вырожденная)
}

# Маркеры для разных типов (разные формы для наглядности)
MARKERS = {
    'node': 'o',  # круг
    'cusp': '^',  # треугольник
    'isolated': 's',  # квадрат
    'degenerate': 'd'  # ромб
}

# Размеры маркеров
MARKER_SIZE = 120

# Настройки шрифтов (поддержка кириллицы)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11


# ========== ОСНОВНАЯ ФУНКЦИЯ ОТРИСОВКИ ==========

def draw_curve(
        equation_str: str,
        bounds: Tuple[float, float, float, float] = (-5, 5, -5, 5),
        resolution: int = 300,
        show_legend: bool = True,
        save_path: Optional[str] = None,
        return_figure: bool = False,
        find_points: bool = True
) -> Optional[str]:
    """
    Главная функция: рисует кривую и её особые точки.

    Параметры:
        equation_str: уравнение кривой (строка)
        bounds: (x_min, x_max, y_min, y_max)
        resolution: разрешение сетки (чем выше, тем плавнее кривая)
        show_legend: показывать легенду
        save_path: если указан, сохраняет в файл (например, 'plots/curve.png')
        return_figure: если True, возвращает объект figure (для интерактива)
        find_points: если False, не ищет особые точки (только кривую)

    Возвращает:
        если save_path указан — путь к сохранённому файлу
        если return_figure=True — объект figure
        иначе — None (просто показывает окно)
    """
    x_min, x_max, y_min, y_max = bounds

    # Шаг 1: парсим уравнение и получаем производные
    try:
        derivatives = parse_equation(equation_str)
    except Exception as e:
        print(f"Ошибка парсинга уравнения: {e}")
        return None

    # Шаг 2: создаём сетку для contour plot
    x = np.linspace(x_min, x_max, resolution)
    y = np.linspace(y_min, y_max, resolution)
    X, Y = np.meshgrid(x, y)

    # Вычисляем значения F(x,y) на сетке
    try:
        Z = derivatives['F'](X, Y)
    except Exception as e:
        print(f"Ошибка вычисления F на сетке: {e}")
        return None

    # Шаг 3: создаём фигуру и оси
    fig, ax = plt.subplots(figsize=(12, 10), dpi=120)

    # Рисуем кривую (линия уровня F=0)
    contour = ax.contour(
        X, Y, Z,
        levels=[0],  # только F=0
        colors='#2c3e50',  # тёмно-синий (почти чёрный)
        linewidths=2.5,
        linestyles='solid'
    )

    # Добавляем цветную заливку для областей F>0 и F<0 (опционально, красиво)
    # Закомментировано, так как может замедлять — раскомментируй если хочешь
    # ax.contourf(X, Y, Z, levels=[-1, 0, 1], colors=['#e8f4f8', '#fdf0e6'], alpha=0.3)

    # Шаг 4: находим и отрисовываем особые точки
    if find_points:
        # Ищем особые точки
        singular_points = find_singular_points(derivatives, bounds)

        # Классифицируем каждую
        classifications = []
        classified_points = []

        for point in singular_points:
            cls = classify_singular_point(point, derivatives)
            classifications.append(cls)
            classified_points.append(point)

            # Отрисовываем точку с цветом и маркером по типу
            ax.scatter(
                point[0], point[1],
                color=COLORS.get(cls, '#95a5a6'),
                marker=MARKERS.get(cls, 'o'),
                s=MARKER_SIZE,
                edgecolors='white',
                linewidth=1.5,
                zorder=5  # выше кривой
            )

            # Добавляем подпись типа рядом с точкой
            offset = 0.15  # смещение подписи
            label_text = {
                'node': 'узел',
                'cusp': 'касп',
                'isolated': 'изолир.',
                'degenerate': 'вырожд.'
            }.get(cls, cls)

            ax.annotate(
                label_text,
                xy=(point[0], point[1]),
                xytext=(point[0] + offset, point[1] + offset),
                fontsize=9,
                color=COLORS.get(cls, '#333'),
                backgroundcolor='white',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color='gray', lw=0.5, alpha=0.5)
            )

        # Создаём легенду
        if show_legend and classified_points:
            legend_handles = []
            unique_types = set(classifications)
            for cls in unique_types:
                label_ru = {
                    'node': 'Узел (самопересечение)',
                    'cusp': 'Касп (остриё)',
                    'isolated': 'Изолированная точка',
                    'degenerate': 'Вырожденная'
                }.get(cls, cls)
                handle = mpatches.Patch(
                    color=COLORS.get(cls, '#95a5a6'),
                    label=label_ru,
                    alpha=0.8
                )
                legend_handles.append(handle)
            ax.legend(handles=legend_handles, loc='upper right', fontsize=10)

    # Шаг 5: настройка внешнего вида
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel('x', fontsize=12)
    ax.set_ylabel('y', fontsize=12)
    ax.set_title(f'Кривая: {equation_str}', fontsize=14, pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal')  # одинаковый масштаб по x и y

    # Добавляем оси (жирные линии)
    ax.axhline(y=0, color='black', linewidth=0.8, alpha=0.5)
    ax.axvline(x=0, color='black', linewidth=0.8, alpha=0.5)

    # Шаг 6: сохранение или показ
    if save_path:
        # Создаём директорию, если её нет
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"График сохранён: {save_path}")

    if return_figure:
        return fig
    elif not save_path:
        plt.show()
    else:
        plt.close(fig)
        return save_path

    return None


# ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ==========

def draw_multiple_curves(
        equations: List[str],
        bounds: Tuple[float, float, float, float] = (-5, 5, -5, 5),
        save_path: Optional[str] = None
) -> None:
    """
    Рисует несколько кривых на одном графике (для сравнения).

    Параметры:
        equations: список строк уравнений
        bounds: границы
        save_path: путь для сохранения (опционально)
    """
    x_min, x_max, y_min, y_max = bounds
    x = np.linspace(x_min, x_max, 300)
    y = np.linspace(y_min, y_max, 300)
    X, Y = np.meshgrid(x, y)

    fig, ax = plt.subplots(figsize=(12, 10), dpi=120)

    colours = ['#2c3e50', '#e74c3c', '#27ae60', '#8e44ad', '#f39c12']

    for i, eq in enumerate(equations):
        try:
            derivatives = parse_equation(eq)
            Z = derivatives['F'](X, Y)
            colour = colours[i % len(colours)]
            ax.contour(X, Y, Z, levels=[0], colors=colour, linewidths=2, label=eq)
        except Exception as e:
            print(f"Ошибка для уравнения '{eq}': {e}")

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('Несколько кривых на одном графике')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    ax.legend(equations, loc='upper right')

    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Сохранено: {save_path}")
    else:
        plt.show()

    plt.close(fig)


def create_animation_frames(
        equation_str: str,
        param_name: str,
        param_values: List[float],
        bounds: Tuple[float, float, float, float] = (-5, 5, -5, 5),
        output_dir: str = 'animation_frames'
) -> List[str]:
    """
    Создаёт серию кадров для анимации (например, меняется параметр a).
    Во втором семестре можно собрать в GIF.

    Параметры:
        equation_str: уравнение с параметром, например 'x**2 + y**2 - a'
        param_name: имя параметра (например 'a')
        param_values: список значений параметра
        bounds: границы
        output_dir: папка для сохранения кадров

    Возвращает:
        список путей к сохранённым кадрам
    """
    os.makedirs(output_dir, exist_ok=True)
    frames = []

    for i, val in enumerate(param_values):
        # Заменяем параметр в уравнении
        eq_with_value = equation_str.replace(param_name, str(val))

        save_path = os.path.join(output_dir, f'frame_{i:03d}.png')
        draw_curve(eq_with_value, bounds=bounds, save_path=save_path)
        frames.append(save_path)
        print(f"Кадр {i + 1}/{len(param_values)}: {save_path}")

    return frames


# ========== ТЕСТЫ (запускаются при прямом выполнении) ==========

if __name__ == "__main__":
    print("=== Тестирование визуализатора ===\n")

    # Создаём папку для графиков
    os.makedirs('test_plots', exist_ok=True)

    # Тест 1: окружность (без особых точек)
    print("1. Окружность x² + y² = 1")
    draw_curve(
        "x**2 + y**2 - 1",
        save_path="test_plots/1_circle.png"
    )

    # Тест 2: узел (самопересечение)
    print("\n2. Узел x² - y² = 0")
    draw_curve(
        "x**2 - y**2",
        save_path="test_plots/2_node.png"
    )

    # Тест 3: касп
    print("\n3. Касп y² - x³ = 0")
    draw_curve(
        "y**2 - x**3",
        save_path="test_plots/3_cusp.png"
    )

    # Тест 4: изолированная точка
    print("\n4. Изолированная точка x² + y² = 0")
    draw_curve(
        "x**2 + y**2",
        save_path="test_plots/4_isolated.png"
    )

    # Тест 5: декартов лист
    print("\n5. Декартов лист x³ + y³ = 3xy")
    draw_curve(
        "x**3 + y**3 - 3*x*y",
        save_path="test_plots/5_folium.png"
    )

    # Тест 6: эллиптическая кривая
    print("\n6. Эллиптическая кривая y² = x³ - x")
    draw_curve(
        "y**2 - x**3 + x",
        save_path="test_plots/6_elliptic.png"
    )

    # Тест 7: лемниската Бернулли
    print("\n7. Лемниската (x² + y²)² = x² - y²")
    draw_curve(
        "(x**2 + y**2)**2 - (x**2 - y**2)",
        save_path="test_plots/7_lemniscate.png"
    )

    print("\n=== Все тестовые графики сохранены в папку 'test_plots' ===")
    print("Открой её и проверь результат.")

    # Бонус: несколько кривых на одном графике
    print("\n8. Несколько кривых на одном графике")
    draw_multiple_curves(
        ["x**2 + y**2 - 1", "x**2 - y**2", "y**2 - x**3"],
        save_path="test_plots/multiple_curves.png"
    )