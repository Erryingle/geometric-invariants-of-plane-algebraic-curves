"""
math_core.py - математическое ядро проекта "Геометрические инварианты кривых"

Модуль предоставляет функции для:
- парсинга уравнения кривой F(x,y)=0
- вычисления частных производных (символьно)
- численного поиска особых точек
- классификации особых точек (узел/касп/изолированная)
- вычисления упрощённой эйлеровой характеристики
"""

import sympy as sp
import numpy as np
from scipy.optimize import fsolve
from typing import Dict, List, Tuple, Callable

# Тип для удобства: словарь с численными функциями производных
Derivatives = Dict[str, Callable[[float, float], float]]


def parse_equation(equation_str: str) -> Derivatives:
    """
    Преобразует строку уравнения в набор численных функций.

    Параметры:
        equation_str: строка вида 'x**2 + y**2 - 1' или 'x**3 + y**3 - 3*x*y'

    Возвращает:
        словарь с ключами: 'F', 'Fx', 'Fy', 'Fxx', 'Fxy', 'Fyy'
        каждый ключ содержит функцию f(x, y) -> float

    Исключения:
        ValueError, если уравнение не может быть распознано
    """
    # Определяем символьные переменные
    x, y = sp.symbols('x y', real=True)

    try:
        # Преобразуем строку в символьное выражение
        F_sym = sp.sympify(equation_str)
    except sp.SympifyError as e:
        raise ValueError(f"Не удалось распознать уравнение: {e}")

    # Вычисляем частные производные символьного выражения
    Fx_sym = sp.diff(F_sym, x)
    Fy_sym = sp.diff(F_sym, y)
    Fxx_sym = sp.diff(Fx_sym, x)
    Fxy_sym = sp.diff(Fx_sym, y)
    Fyy_sym = sp.diff(Fy_sym, y)

    # Преобразуем символьные выражения в численные функции (для скорости)
    # 'numpy' позволяет вычислять сразу над массивами
    F_num = sp.lambdify((x, y), F_sym, 'numpy')
    Fx_num = sp.lambdify((x, y), Fx_sym, 'numpy')
    Fy_num = sp.lambdify((x, y), Fy_sym, 'numpy')
    Fxx_num = sp.lambdify((x, y), Fxx_sym, 'numpy')
    Fxy_num = sp.lambdify((x, y), Fxy_sym, 'numpy')
    Fyy_num = sp.lambdify((x, y), Fyy_sym, 'numpy')

    # Проверка: если производные выродились в константу 0 — это нормально
    # (например, для кривой x = 0 производная Fy = 0)

    return {
        'F': F_num,
        'Fx': Fx_num,
        'Fy': Fy_num,
        'Fxx': Fxx_num,
        'Fxy': Fxy_num,
        'Fyy': Fyy_num
    }


def find_singular_points(
        derivatives: Derivatives,
        bounds: Tuple[float, float, float, float] = (-5, 5, -5, 5),
        grid_size: int = 20,
        tolerance: float = 1e-6
) -> List[Tuple[float, float]]:
    """
    Находит все особые точки кривой в заданной области.

    Особая точка: F=0, Fx=0, Fy=0 одновременно.

    Параметры:
        derivatives: словарь с функциями производных (из parse_equation)
        bounds: (x_min, x_max, y_min, y_max)
        grid_size: размер сетки (grid_size x grid_size ячеек)
        tolerance: точность проверки условий

    Возвращает:
        список особых точек в формате [(x1,y1), (x2,y2), ...]
    """
    x_min, x_max, y_min, y_max = bounds

    # Создаём точки старта для fsolve (центры ячеек сетки)
    x_starts = np.linspace(x_min, x_max, grid_size)
    y_starts = np.linspace(y_min, y_max, grid_size)

    candidates = []

    for x0 in x_starts:
        for y0 in y_starts:
            # Определяем систему уравнений для fsolve
            def system(p):
                x, y = p
                return [
                    float(derivatives['F'](x, y)),
                    float(derivatives['Fx'](x, y)),
                    float(derivatives['Fy'](x, y))
                ]

            try:
                # Пытаемся найти корень, начиная с (x0, y0)
                root, infodict, ier, mesg = fsolve(
                    system,
                    [x0, y0],
                    full_output=True,
                    xtol=tolerance
                )

                # ier = 1 означает успешное нахождение корня
                if ier != 1:
                    continue

                x_root, y_root = root

                # Проверяем, что точка действительно особая (с заданной точностью)
                F_val = abs(derivatives['F'](x_root, y_root))
                Fx_val = abs(derivatives['Fx'](x_root, y_root))
                Fy_val = abs(derivatives['Fy'](x_root, y_root))

                if F_val < tolerance and Fx_val < tolerance and Fy_val < tolerance:
                    # Проверяем, что точка внутри bounds
                    if (x_min - tolerance <= x_root <= x_max + tolerance and
                            y_min - tolerance <= y_root <= y_max + tolerance):
                        candidates.append((x_root, y_root))

            except Exception:
                # fsolve может выбросить исключение (не сходится), игнорируем
                continue

    # Удаляем дубликаты (точки, которые слишком близко)
    unique_points = []
    for point in candidates:
        is_duplicate = False
        for existing in unique_points:
            distance = np.linalg.norm(np.array(point) - np.array(existing))
            if distance < 0.01:  # 0.01 — порог схлопывания
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append(point)

    return unique_points


def classify_singular_point(
        point: Tuple[float, float],
        derivatives: Derivatives,
        tolerance: float = 1e-6
) -> str:
    """
    Определяет тип особой точки по гессиану.

    Параметры:
        point: (x, y) координаты особой точки
        derivatives: словарь с функциями производных

    Возвращает:
        'node' — узел (самопересечение)
        'cusp' — касп/клюв (остриё)
        'isolated' — изолированная точка
        'degenerate' — вырожденная (если не удалось определить)
    """
    x, y = point

    # Вычисляем вторые производные в точке
    try:
        Fxx_val = derivatives['Fxx'](x, y)
        Fxy_val = derivatives['Fxy'](x, y)
        Fyy_val = derivatives['Fyy'](x, y)
    except Exception:
        return "degenerate"

    # Детерминант гессиана
    det = Fxx_val * Fyy_val - Fxy_val * Fxy_val

    # Классификация
    if det < -tolerance:
        return "node"  # узел: седловая точка гессиана
    elif det > tolerance:
        return "isolated"  # изолированная: экстремум
    else:
        # Детерминант близок к нулю — пробуем уточнить
        # Проверяем, не нулевые ли все вторые производные
        if (abs(Fxx_val) < tolerance and abs(Fxy_val) < tolerance and abs(Fyy_val) < tolerance):
            return "degenerate"  # слишком вырожденно, нужны высшие порядки
        else:
            return "cusp"  # скорее всего клюв


def find_connected_components_binary(
        derivatives: Derivatives,
        bounds: Tuple[float, float, float, float] = (-5, 5, -5, 5),
        resolution: int = 200
) -> int:
    """
    Находит число связных компонент кривой (упрощённый бинарный метод).

    Идея: растровая картинка, заливка из каждой найденной точки кривой.

    Возвращает:
        количество связных компонент (приближённое)
    """
    x_min, x_max, y_min, y_max = bounds

    # Создаём сетку
    x_vals = np.linspace(x_min, x_max, resolution)
    y_vals = np.linspace(y_min, y_max, resolution)
    X, Y = np.meshgrid(x_vals, y_vals)

    # Вычисляем F на сетке
    F_vals = derivatives['F'](X, Y)

    # Бинарная маска: где |F| < порог (приближение кривой)
    threshold = 0.05  # экспериментальный порог
    mask = np.abs(F_vals) < threshold

    # Простая связность (4-связность: вверх, вниз, влево, вправо)
    from scipy.ndimage import label
    labeled_mask, num_components = label(mask)

    return num_components


def compute_euler_characteristic(
        singular_points: List[Tuple[float, float]],
        classifications: List[str],
        num_components: int
) -> int:
    """
    Вычисляет эйлерову характеристику по упрощённой формуле.

    Формула: χ = (число компонент) - (число узлов) - (число каспов)

    Изолированные точки дают +1 каждая, но в нашей упрощённой модели
    они пока не учитываются (можно доработать во втором семестре).

    Параметры:
        singular_points: список особых точек
        classifications: список типов (соответствует порядку точек)
        num_components: число связных компонент

    Возвращает:
        целое число — эйлерова характеристика
    """
    nodes_count = classifications.count('node')
    cusps_count = classifications.count('cusp')
    isolated_count = classifications.count('isolated')

    # Базовая формула
    euler = num_components - nodes_count - cusps_count

    # Изолированные точки — сложный случай: они увеличивают χ?
    # Для простоты пока игнорируем, но можно добавить:
    # euler += isolated_count  # (спорно, требует проверки)

    return euler


# ========== БОНУС: функция для отладки и тестирования ==========

def analyze_curve(equation_str: str, verbose: bool = True) -> Dict:
    """
    Удобная функция для полного анализа кривой за один вызов.
    Используется для тестирования и из командной строки.

    Возвращает:
        словарь со всеми результатами анализа
    """
    result = {
        'equation': equation_str,
        'success': False,
        'singular_points': [],
        'classifications': [],
        'num_components': 0,
        'euler_characteristic': None,
        'error': None
    }

    try:
        # Шаг 1: парсинг
        derivatives = parse_equation(equation_str)

        # Шаг 2: поиск особых точек
        points = find_singular_points(derivatives)
        result['singular_points'] = points

        # Шаг 3: классификация
        classifications = [classify_singular_point(p, derivatives) for p in points]
        result['classifications'] = classifications

        # Шаг 4: компоненты связности
        num_comp = find_connected_components_binary(derivatives)
        result['num_components'] = num_comp

        # Шаг 5: эйлерова характеристика
        euler = compute_euler_characteristic(points, classifications, num_comp)
        result['euler_characteristic'] = euler

        result['success'] = True

        if verbose:
            print(f"\n=== Анализ кривой: {equation_str} ===")
            print(f"Особые точки: {len(points)}")
            for p, cls in zip(points, classifications):
                print(f"  ({p[0]:.4f}, {p[1]:.4f}) -> {cls}")
            print(f"Связных компонент: {num_comp}")
            print(f"Эйлерова характеристика χ = {euler}")

    except Exception as e:
        result['error'] = str(e)
        if verbose:
            print(f"Ошибка: {e}")

    return result


# ========== ТЕСТЫ (запускаются только при выполнении файла напрямую) ==========

if __name__ == "__main__":
    print("=== Тестирование математического ядра ===\n")

    # Тест 1: окружность (нет особых точек)
    analyze_curve("x**2 + y**2 - 1")

    # Тест 2: узел (самопересечение)
    analyze_curve("x**2 - y**2")

    # Тест 3: изолированная точка
    analyze_curve("x**2 + y**2")

    # Тест 4: касп (полукубическая парабола)
    analyze_curve("y**2 - x**3")

    # Тест 5: декартов лист
    analyze_curve("x**3 + y**3 - 3*x*y")

    # Тест 6: эллиптическая кривая (особые точки только в бесконечности)
    analyze_curve("y**2 - x**3 + x")

    print("\n=== Тестирование завершено ===")