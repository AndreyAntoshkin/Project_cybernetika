#!/usr/bin/env python3
# 📊 create_dashboard.py
# Создание HTML дашборда для анализа данных умного здания

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import base64
from io import BytesIO
import os
import sys


def load_data():
    """Загрузка всех необходимых данных"""
    print("📂 Загрузка данных...")

    data = {}

    try:
        # Основные данные
        data['sensors'] = pd.read_csv('C:/Users/andre/Project_cybernetika/src/data/sensors_data.csv', parse_dates=['timestamp'])
        data['energy'] = pd.read_csv('C:/Users/andre/Project_cybernetika/src/data/energy_data.csv', parse_dates=['timestamp'])
        print("✅ Основные данные загружены")
    except FileNotFoundError as e:
        print(f"❌ Ошибка: {e}")
        print("   Сначала запустите генерацию данных")
        return None

    # ML результаты (если есть)
    try:
        data['anomalies'] = pd.read_csv('C:/Users/andre/Project_cybernetika/reports/temperature_anomalies.csv')
        print("✅ Аномалии загружены")
    except:
        data['anomalies'] = pd.DataFrame()
        print("⚠️  Аномалии не найдены")

    try:
        data['recommendations'] = pd.read_csv('C:/Users/andre/Project_cybernetika/reports/system_recommendations.csv')
        print("✅ Рекомендации загружены")
    except:
        data['recommendations'] = pd.DataFrame()
        print("⚠️  Рекомендации не найдены")

    return data


def calculate_metrics(sensors):
    """Расчет ключевых метрики"""
    if len(sensors) == 0:
        return {}

    avg_temp = sensors['temperature'].mean()
    avg_humidity = sensors['humidity'].mean()
    avg_co2 = sensors['co2'].mean()
    avg_light = sensors['light_level'].mean()

    # Определяем статусы
    def get_status_and_color(value, good_range, warning_range=None):
        """Определяет статус и цвет на основе диапазона"""
        if good_range[0] <= value <= good_range[1]:
            return "✅ Норма", "success"
        elif warning_range and warning_range[0] <= value <= warning_range[1]:
            return "⚠️ Внимание", "warning"
        elif value < good_range[0]:
            return "❌ Низкий", "danger"
        else:
            return "❌ Высокий", "danger"

    temp_status, temp_color = get_status_and_color(avg_temp, (20, 24), (18, 26))
    humidity_status, humidity_color = get_status_and_color(avg_humidity, (40, 60), (30, 70))

    # CO2 особый случай
    if avg_co2 <= 600:
        co2_status, co2_color = "✅ Хорошо", "success"
    elif avg_co2 <= 800:
        co2_status, co2_color = "⚠️ Повышен", "warning"
    else:
        co2_status, co2_color = "❌ Высокий", "danger"

    # Освещение
    if avg_light >= 300:
        light_status, light_color = "✅ Норма", "success"
    elif avg_light >= 200:
        light_status, light_color = "⚠️ Темно", "warning"
    else:
        light_status, light_color = "❌ Очень темно", "danger"

    return {
        'temperature': {'value': avg_temp, 'status': temp_status, 'color': temp_color},
        'humidity': {'value': avg_humidity, 'status': humidity_status, 'color': humidity_color},
        'co2': {'value': avg_co2, 'status': co2_status, 'color': co2_color},
        'light': {'value': avg_light, 'status': light_status, 'color': light_color}
    }


def create_temperature_chart(sensors):
    """Создает график температуры"""
    if len(sensors) == 0:
        return ""

    fig, ax = plt.subplots(figsize=(10, 4))

    # Берем последние 200 записей
    temp_data = sensors.tail(200)
    ax.plot(temp_data['timestamp'], temp_data['temperature'],
            color='red', linewidth=1.5, alpha=0.7)

    # Линии нормы
    ax.axhline(y=20, color='green', linestyle='--', alpha=0.5, label='Нижняя норма (20°C)')
    ax.axhline(y=24, color='green', linestyle='--', alpha=0.5, label='Верхняя норма (24°C)')

    ax.set_title('Температура в помещении (последние 200 измерений)', fontsize=12)
    ax.set_xlabel('Время')
    ax.set_ylabel('Температура (°C)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    # Конвертируем в base64
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    chart_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)

    return chart_base64


def create_energy_chart(energy):
    """Создает график энергопотребления"""
    if len(energy) == 0:
        return ""

    fig, ax = plt.subplots(figsize=(10, 4))

    energy['hour'] = energy['timestamp'].dt.hour
    energy_by_hour = energy.groupby('hour')['electricity_kwh'].mean()

    bars = ax.bar(energy_by_hour.index, energy_by_hour.values,
                  color='green', alpha=0.7, edgecolor='black')

    # Находим пиковый час
    peak_hour = energy_by_hour.idxmax()
    peak_value = energy_by_hour.max()

    # Выделяем пиковый час
    if peak_hour < len(bars):
        bars[peak_hour].set_color('red')

    # Добавляем значения
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + 0.5,
                f'{height:.1f}', ha='center', va='bottom', fontsize=8)

    ax.set_title(f'Потребление энергии по часам (Пик: {peak_hour}:00)', fontsize=12)
    ax.set_xlabel('Час дня (0-23)')
    ax.set_ylabel('кВт·ч')
    ax.set_xticks(range(0, 24, 3))
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Конвертируем в base64
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    chart_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)

    return chart_base64


def generate_anomalies_table(anomalies):
    """Генерирует HTML таблицу аномалий"""
    if len(anomalies) == 0:
        return '''
        <div class="alert alert-success">
            ✅ Аномалий не обнаружено
        </div>
        '''

    # Берем последние 5 аномалий
    recent_anomalies = anomalies.tail(5).copy()
    recent_anomalies['timestamp'] = pd.to_datetime(recent_anomalies['timestamp'])

    table_html = '''
    <div class="table-responsive">
        <table class="table table-sm table-hover">
            <thead class="table-dark">
                <tr>
                    <th>Дата</th>
                    <th>Время</th>
                    <th>Температура</th>
                    <th>Тип</th>
                    <th>Отклонение</th>
                </tr>
            </thead>
            <tbody>
    '''

    for _, row in recent_anomalies.iterrows():
        anomaly_type = row.get('anomaly_type', 'Неизвестно')
        deviation = row.get('deviation', 0)
        temp = row.get('temperature', 0)

        # Определяем иконку
        if 'холодно' in str(anomaly_type).lower():
            icon = '❄️'
            badge_class = 'bg-primary'
        else:
            icon = '🔥'
            badge_class = 'bg-danger'

        table_html += f'''
                <tr>
                    <td>{row['timestamp'].strftime('%d.%m.%Y')}</td>
                    <td>{row['timestamp'].strftime('%H:%M')}</td>
                    <td><strong>{temp:.1f}°C</strong></td>
                    <td><span class="badge {badge_class}">{icon} {anomaly_type}</span></td>
                    <td>{deviation:.1f}°C</td>
                </tr>
        '''

    table_html += '''
            </tbody>
        </table>
    </div>
    '''

    return table_html


def generate_recommendations_list(recommendations):
    """Генерирует HTML список рекомендаций"""
    if len(recommendations) == 0:
        return '''
        <div class="alert alert-info">
            ℹ️ Рекомендации не найдены. Запустите анализ данных.
        </div>
        '''

    list_html = '<div class="list-group">'

    for _, row in recommendations.iterrows():
        priority = row.get('Приоритет', 'Средний')
        parameter = row.get('Параметр', 'Неизвестно')
        recommendation = row.get('Рекомендация', 'Нет рекомендации')
        status = row.get('Статус', 'Неизвестно')

        # Определяем стиль по приоритету
        if priority == 'Высокий':
            border_class = 'border-danger'
            badge_class = 'bg-danger'
            text_class = 'text-danger'
        elif priority == 'Средний':
            border_class = 'border-warning'
            badge_class = 'bg-warning'
            text_class = 'text-warning'
        else:
            border_class = 'border-success'
            badge_class = 'bg-success'
            text_class = 'text-success'

        list_html += f'''
        <div class="list-group-item {border_class} {text_class}">
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">{parameter}</h6>
                <span class="badge {badge_class}">{priority}</span>
            </div>
            <p class="mb-1">{recommendation}</p>
            <small>Статус: {status}</small>
        </div>
        '''

    list_html += '</div>'

    return list_html


def generate_dashboard(data):
    """Генерирует полный HTML дашборд"""
    print("🎨 Генерация HTML дашборда...")

    # Подготовка данных
    sensors = data['sensors']
    energy = data['energy']
    anomalies = data['anomalies']
    recommendations = data['recommendations']

    # Рассчитываем метрики
    metrics = calculate_metrics(sensors)

    # Создаем графики
    temp_chart = create_temperature_chart(sensors)
    energy_chart = create_energy_chart(energy)

    # Генерируем таблицы и списки
    anomalies_table = generate_anomalies_table(anomalies)
    recommendations_list = generate_recommendations_list(recommendations)

    # Получаем значения метрик с проверками
    temp_metrics = metrics.get('temperature', {})
    humidity_metrics = metrics.get('humidity', {})
    co2_metrics = metrics.get('co2', {})
    light_metrics = metrics.get('light', {})

    temp_color = temp_metrics.get('color', 'light')
    humidity_color = humidity_metrics.get('color', 'light')
    co2_color = co2_metrics.get('color', 'light')
    light_color = light_metrics.get('color', 'light')

    temp_value = temp_metrics.get('value', 0)
    humidity_value = humidity_metrics.get('value', 0)
    co2_value = co2_metrics.get('value', 0)
    light_value = light_metrics.get('value', 0)

    temp_status = temp_metrics.get('status', 'Нет данных')
    humidity_status = humidity_metrics.get('status', 'Нет данных')
    co2_status = co2_metrics.get('status', 'Нет данных')
    light_status = light_metrics.get('status', 'Нет данных')

    # Генерируем HTML
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏢 Дашборд умного здания</title>

    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">

    <style>
        :root {{
            --primary-color: #4361ee;
            --secondary-color: #3a0ca3;
            --success-color: #4cc9f0;
            --warning-color: #f72585;
            --danger-color: #7209b7;
        }}

        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background-attachment: fixed;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            padding: 20px 0;
        }}

        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            margin-bottom: 30px;
            overflow: hidden;
        }}

        .header-gradient {{
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .metric-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: none;
            position: relative;
            overflow: hidden;
        }}

        .metric-card:hover {{
            transform: translateY(-10px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
        }}

        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
        }}

        .metric-card.bg-success::before {{ background: var(--success-color); }}
        .metric-card.bg-warning::before {{ background: var(--warning-color); }}
        .metric-card.bg-danger::before {{ background: var(--danger-color); }}

        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}

        .section-title {{
            color: var(--secondary-color);
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-weight: 600;
        }}

        .status-badge {{
            font-size: 0.8em;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 500;
        }}

        .value-large {{
            font-size: 2.5rem;
            font-weight: 700;
            margin: 10px 0;
        }}

        .update-time {{
            font-size: 0.9em;
            color: #6c757d;
            background: rgba(255, 255, 255, 0.1);
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
        }}

        .anomaly-row {{
            border-left: 4px solid;
            transition: all 0.3s;
        }}

        .anomaly-row:hover {{
            background-color: rgba(255, 0, 0, 0.05);
            transform: translateX(5px);
        }}

        .recommendation-item {{
            border-left: 4px solid;
            margin-bottom: 10px;
            transition: all 0.3s;
        }}

        .recommendation-item:hover {{
            transform: translateX(10px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}

        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
        }}

        .pulse {{
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Шапка -->
        <div class="header-card">
            <div class="header-gradient">
                <h1 class="display-4"><i class="bi bi-building"></i> Дашборд умного здания</h1>
                <p class="lead">Интеллектуальный мониторинг и анализ энергоэффективности</p>
                <div class="update-time">
                    <i class="bi bi-clock"></i> Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
                </div>
            </div>
        </div>

        <!-- Карточки с метриками -->
        <div class="row">
            <div class="col-lg-3 col-md-6">
                <div class="metric-card bg-{temp_color}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5><i class="bi bi-thermometer-half"></i> Температура</h5>
                            <div class="value-large">{temp_value:.1f}°C</div>
                            <small class="text-muted">Норма: 20-24°C</small>
                        </div>
                        <span class="status-badge bg-{temp_color}">
                            {temp_status}
                        </span>
                    </div>
                </div>
            </div>

            <div class="col-lg-3 col-md-6">
                <div class="metric-card bg-{humidity_color}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5><i class="bi bi-droplet"></i> Влажность</h5>
                            <div class="value-large">{humidity_value:.1f}%</div>
                            <small class="text-muted">Норма: 40-60%</small>
                        </div>
                        <span class="status-badge bg-{humidity_color}">
                            {humidity_status}
                        </span>
                    </div>
                </div>
            </div>

            <div class="col-lg-3 col-md-6">
                <div class="metric-card bg-{co2_color}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5><i class="bi bi-cloud"></i> Уровень CO₂</h5>
                            <div class="value-large">{co2_value:.0f} ppm</div>
                            <small class="text-muted">Хорошо: ≤600 ppm</small>
                        </div>
                        <span class="status-badge bg-{co2_color}">
                            {co2_status}
                        </span>
                    </div>
                </div>
            </div>

            <div class="col-lg-3 col-md-6">
                <div class="metric-card bg-{light_color}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5><i class="bi bi-brightness-high"></i> Освещение</h5>
                            <div class="value-large">{light_value:.0f} lux</div>
                            <small class="text-muted">Норма: ≥300 lux</small>
                        </div>
                        <span class="status-badge bg-{light_color}">
                            {light_status}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Графики -->
        <div class="row">
            <div class="col-lg-6">
                <div class="chart-container">
                    <h3 class="section-title"><i class="bi bi-graph-up"></i> Температура в реальном времени</h3>
                    <img src="data:image/png;base64,{temp_chart}" class="img-fluid rounded" alt="График температуры">
                    <div class="mt-3 text-center">
                        <small class="text-muted">Последние 200 измерений | Зеленые линии - нормативные значения</small>
                    </div>
                </div>
            </div>

            <div class="col-lg-6">
                <div class="chart-container">
                    <h3 class="section-title"><i class="bi bi-lightning-charge"></i> Потребление энергии</h3>
                    <img src="data:image/png;base64,{energy_chart}" class="img-fluid rounded" alt="График энергопотребления">
                    <div class="mt-3 text-center">
                        <small class="text-muted">Среднее потребление по часам | Красный столбец - пиковый час</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Аномалии и рекомендации -->
        <div class="row">
            <div class="col-lg-6">
                <div class="chart-container">
                    <h3 class="section-title"><i class="bi bi-exclamation-triangle"></i> Обнаруженные аномалии</h3>
                    {anomalies_table}
                </div>
            </div>

            <div class="col-lg-6">
                <div class="chart-container">
                    <h3 class="section-title"><i class="bi bi-lightbulb"></i> Рекомендации системы</h3>
                    {recommendations_list}
                </div>
            </div>
        </div>

        <!-- Статистика системы -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="chart-container">
                    <h3 class="section-title"><i class="bi bi-bar-chart"></i> Статистика системы</h3>
                    <div class="row text-center">
                        <div class="col-md-3">
                            <div class="p-3 bg-light rounded">
                                <h2>{len(sensors):,}</h2>
                                <p class="mb-0"><i class="bi bi-cpu"></i> Записей с датчиков</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="p-3 bg-light rounded">
                                <h2>{len(energy):,}</h2>
                                <p class="mb-0"><i class="bi bi-lightning"></i> Записей энергии</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="p-3 bg-light rounded">
                                <h2>{len(anomalies)}</h2>
                                <p class="mb-0"><i class="bi bi-exclamation-circle"></i> Обнаруженных аномалий</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="p-3 bg-light rounded">
                                <h2>{len(recommendations)}</h2>
                                <p class="mb-0"><i class="bi bi-check-circle"></i> Рекомендаций</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Футер -->
        <div class="footer">
            <h5><i class="bi bi-code-slash"></i> Аналитическая система управления зданием</h5>
            <p class="mb-2">Курсовой проект | Автоматический мониторинг и оптимизация</p>
            <p class="mb-0">
                <small>
                    <span class="pulse"><i class="bi bi-circle-fill text-success"></i> Система активна</span> | 
                    Ожидаемая экономия: 15-20% | Повышение комфорта: 25-30%
                </small>
            </p>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // Автоматическое обновление
        let refreshTimer = 300; // 5 минут в секундах
        const timerElement = document.createElement('div');
        timerElement.className = 'update-time mt-2';
        timerElement.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Автообновление через: <span id="countdown">' + refreshTimer + '</span> сек';
        document.querySelector('.update-time').parentNode.appendChild(timerElement);

        function updateCountdown() {{
            refreshTimer--;
            document.getElementById('countdown').textContent = refreshTimer;

            if (refreshTimer <= 0) {{
                location.reload();
            }}
        }}

        setInterval(updateCountdown, 1000);

        // Анимация при наведении на метрики
        document.querySelectorAll('.metric-card').forEach(card => {{
            card.addEventListener('mouseenter', function() {{
                this.style.transform = 'translateY(-10px) scale(1.02)';
            }});

            card.addEventListener('mouseleave', function() {{
                this.style.transform = 'translateY(0) scale(1)';
            }});
        }});

        // Подсветка активных элементов
        document.querySelectorAll('.anomaly-row, .recommendation-item').forEach(el => {{
            el.addEventListener('click', function() {{
                this.classList.toggle('bg-light');
            }});
        }});

        // Уведомление о новом обновлении
        setTimeout(() => {{
            const alert = document.createElement('div');
            alert.className = 'alert alert-info alert-dismissible fade show position-fixed bottom-0 end-0 m-3';
            alert.style.zIndex = '1000';
            alert.innerHTML = `
                <i class="bi bi-info-circle"></i> Система мониторинга активна. Данные обновляются автоматически.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(alert);
        }}, 3000);
    </script>
</body>
</html>'''

    return html


def main():
    """Основная функция"""
    print("=" * 60)
    print("🏢 СОЗДАНИЕ ДАШБОРДА УМНОГО ЗДАНИЯ")
    print("=" * 60)

    # Загружаем данные
    data = load_data()
    if data is None:
        sys.exit(1)

    # Генерируем дашборд
    html_content = generate_dashboard(data)

    # Сохраняем файл
    output_file = 'dashboard.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Дашборд успешно создан: {output_file}")
    print(f"📊 Размер файла: {len(html_content):,} байт")

    # Инструкция по использованию
    print("\n" + "=" * 60)
    print("🚀 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:")
    print("=" * 60)
    print("""
1. 📁 ОТКРЫТЬ ДАШБОРД:
   • Просто откройте файл 'dashboard.html' в любом браузере
   • Или запустите локальный сервер для лучшей производительности:

2. 🖥️ ЛОКАЛЬНЫЙ СЕРВЕР:
   В командной строке выполните:

   # Python 3
   python -m http.server 8000

   # Или используйте встроенный сервер браузера
   Затем откройте: http://localhost:8000/dashboard.html

3. 🔄 ОБНОВЛЕНИЕ ДАННЫХ:
   Дашборд автоматически обновляется каждые 5 минут
   Или обновите страницу вручную (F5)

4. 📱 ОСОБЕННОСТИ:
   • Адаптивный дизайн (работает на ПК, планшетах, телефонах)
   • Интерактивные элементы с анимациями
   • Автоматический подсчет времени до обновления
   • Цветовая индикация статусов параметров

5. 📊 ЧТО ПОКАЗЫВАЕТ:
   • Ключевые метрики комфорта (температура, влажность, CO2, свет)
   • Графики в реальном времени
   • Обнаруженные аномалии
   • Рекомендации по оптимизации
   • Статистику работы системы
    """)

    print(f"\n🎉 ГОТОВО! Откройте {output_file} в браузере")


if __name__ == "__main__":
    main()