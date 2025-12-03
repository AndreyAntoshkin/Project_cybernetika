"""
Модуль генерации синтетических данных для BMS
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Dict, Tuple


class BMSDataGenerator:
    """Генератор данных для системы управления зданием"""
    
    def __init__(self, seed: int = 42):
        """
        Инициализация генератора данных
        
        Args:
            seed: Seed для воспроизводимости
        """
        np.random.seed(seed)
        random.seed(seed)
        self.sensor_points = 100  # Количество точек сбора данных
        
    def generate_timestamps(self, start_date: str, days: int, freq: str) -> pd.DatetimeIndex:
        """
        Генерация временных меток
        
        Args:
            start_date: Дата начала
            days: Количество дней
            freq: Частота ('2T' = 2 минуты)
            
        Returns:
            Массив временных меток
        """
        start = pd.Timestamp(start_date)
        end = start + pd.Timedelta(days=days)
        return pd.date_range(start=start, end=end, freq=freq, inclusive='left')
    
    def add_seasonal_pattern(self, base_value: float, timestamp: pd.Timestamp, 
                            amplitude: float = 1.0) -> float:
        """
        Добавление сезонного паттерна
        
        Args:
            base_value: Базовое значение
            timestamp: Временная метка
            amplitude: Амплитуда колебаний
            
        Returns:
            Значение с сезонностью
        """
        hour = timestamp.hour
        day_of_week = timestamp.dayofweek
        day_of_year = timestamp.dayofyear
        
        # Суточные колебания
        daily = amplitude * np.sin(2 * np.pi * hour / 24)
        
        # Недельные колебания (выходные/рабочие дни)
        weekly = 0.5 if day_of_week >= 5 else 0
        
        # Годовые колебания (зима/лето)
        seasonal = 0.3 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        
        return base_value + daily + weekly + seasonal
    
    def generate_sensor_data(self, start_date: str = '2024-01-01', 
                           days: int = 30, freq: str = '2T') -> pd.DataFrame:
        """
        Генерация данных с датчиков
        
        Returns:
            DataFrame с данными датчиков
        """
        print(f"Генерация данных датчиков за {days} дней с частотой {freq}...")
        
        timestamps = self.generate_timestamps(start_date, days, freq)
        n_records = len(timestamps)
        
        data = []
        for i, ts in enumerate(timestamps):
            if i % 1000 == 0:
                print(f"Обработано {i}/{n_records} записей...", end='\r')
            
            # Базовые значения
            base_temp = 22.0
            base_humidity = 50.0
            base_co2 = 450.0
            base_light = 150.0
            
            # Добавляем паттерны
            temperature = self.add_seasonal_pattern(base_temp, ts, amplitude=4)
            humidity = self.add_seasonal_pattern(base_humidity, ts, amplitude=15)
            
            # CO2 зависит от времени дня и дня недели
            if ts.hour >= 8 and ts.hour <= 18 and ts.dayofweek < 5:
                co2 = base_co2 + 200 + random.uniform(0, 100)
            else:
                co2 = base_co2 + random.uniform(0, 50)
            
            # Освещение
            if ts.hour >= 8 and ts.hour <= 18:
                light = base_light + 200 + random.uniform(0, 300)
            else:
                light = base_light + random.uniform(0, 50)
            
            # Добавляем немного шума
            temperature += random.uniform(-0.5, 0.5)
            humidity += random.uniform(-2, 2)
            co2 += random.uniform(-20, 20)
            light += random.uniform(-10, 10)
            
            # Ограничиваем диапазоны
            temperature = max(18, min(28, temperature))
            humidity = max(30, min(70, humidity))
            co2 = max(350, min(1500, co2))
            light = max(0, min(800, light))
            
            data.append({
                'timestamp': ts,
                'sensor_id': f"sensor_{i % 10:03d}",  # 10 различных датчиков
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1),
                'co2': int(co2),
                'light_level': int(light),
                'zone': f"zone_{(i % 5) + 1}"  # 5 зон
            })
        
        print(f"\n✅ Сгенерировано {len(data)} записей")
        return pd.DataFrame(data)
    
    def add_missing_values(self, df: pd.DataFrame, missing_percent: float = 0.02) -> pd.DataFrame:
        """
        Добавление пропущенных значений для реалистичности
        
        Args:
            df: Исходный DataFrame
            missing_percent: Процент пропусков
            
        Returns:
            DataFrame с пропусками
        """
        df_modified = df.copy()
        
        # Для числовых колонок добавляем пропуски
        numeric_cols = ['temperature', 'humidity', 'co2', 'light_level']
        
        for col in numeric_cols:
            mask = np.random.random(len(df)) < missing_percent
            df_modified.loc[mask, col] = np.nan
        
        print(f"Добавлено пропусков: {df_modified.isnull().sum().sum()} значений")
        return df_modified
    
    def add_anomalies(self, df: pd.DataFrame, anomaly_percent: float = 0.01) -> pd.DataFrame:
        """
        Добавление аномалий в данные
        
        Args:
            df: Исходный DataFrame
            anomaly_percent: Процент аномалий
            
        Returns:
            DataFrame с аномалиями
        """
        df_modified = df.copy()
        n_anomalies = int(len(df) * anomaly_percent)
        
        if n_anomalies > 0:
            anomaly_indices = np.random.choice(len(df), n_anomalies, replace=False)
            
            for idx in anomaly_indices:
                # Выбираем случайную колонку для аномалии
                col = np.random.choice(['temperature', 'co2'])
                
                if col == 'temperature':
                    # Аномальная температура (+- 5-10 градусов)
                    change = np.random.choice([-8, -5, 7, 10])
                    df_modified.loc[idx, col] += change
                elif col == 'co2':
                    # Аномальный CO2 (в 2-3 раза выше)
                    multiplier = np.random.uniform(2.0, 3.0)
                    df_modified.loc[idx, col] *= multiplier
        
        print(f"Добавлено аномалий: {n_anomalies}")
        return df_modified
    
    def generate_all_data(self, start_date: str = '2024-01-01', 
                         days: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Генерация всех типов данных
        
        Returns:
            Словарь с тремя DataFrame
        """
        print("="*60)
        print("ГЕНЕРАЦИЯ ВСЕХ ТИПОВ ДАННЫХ ДЛЯ BMS")
        print("="*60)
        
        # 1. Данные с датчиков
        sensors_df = self.generate_sensor_data(start_date, days, freq='2T')
        sensors_df = self.add_missing_values(sensors_df)
        sensors_df = self.add_anomalies(sensors_df)
        
        # 2. Данные по энергии (на основе датчиков)
        print("\nГенерация данных по энергии...")
        energy_df = self._generate_energy_data(sensors_df)
        
        # 3. Данные оборудования
        print("\nГенерация данных оборудования...")
        equipment_df = self._generate_equipment_data(sensors_df)
        
        print("\n" + "="*60)
        print("ГЕНЕРАЦИЯ ЗАВЕРШЕНА")
        print("="*60)
        
        return {
            'sensors': sensors_df,
            'energy': energy_df,
            'equipment': equipment_df
        }
    
    def _generate_energy_data(self, sensors_df: pd.DataFrame) -> pd.DataFrame:
        """
        Генерация данных по энергопотреблению
        """
        # Группируем по 30-минутным интервалам
        sensors_df = sensors_df.copy()
        sensors_df.set_index('timestamp', inplace=True)
        
        # Ресемплируем для энергетических данных
        energy_df = sensors_df.resample('30T').agg({
            'temperature': 'mean',
            'light_level': 'mean',
            'co2': 'mean'
        }).reset_index()
        
        # Рассчитываем потребление
        energy_data = []
        for idx, row in energy_df.iterrows():
            ts = row['timestamp']
            temp = row['temperature']
            light = row['light_level']
            co2 = row['co2']
            
            # Базовая нагрузка
            base_load = 50.0
            
            # Влияние температуры
            if pd.notna(temp):
                if temp > 24:
                    temp_effect = (temp - 24) * 12  # Охлаждение
                elif temp < 20:
                    temp_effect = (20 - temp) * 8   # Обогрев
                else:
                    temp_effect = 0
            else:
                temp_effect = 0
            
            # Влияние освещения
            light_effect = (light / 1000) * 80 if pd.notna(light) else 0
            
            # Влияние времени суток
            hour = ts.hour
            if 8 <= hour <= 10:
                time_factor = 1.8  # Утренний пик
            elif 18 <= hour <= 20:
                time_factor = 1.6  # Вечерний пик
            elif hour <= 6 or hour >= 22:
                time_factor = 0.4  # Ночью
            else:
                time_factor = 1.0
            
            # Итоговое потребление
            electricity = (base_load + temp_effect + light_effect) * time_factor
            electricity += np.random.normal(0, 5)  # Случайный шум
            
            # Отопление (только зимой)
            month = ts.month
            if month in [1, 2, 11, 12]:
                heating = max(0, (18 - (temp if pd.notna(temp) else 20)) * 0.3)
            else:
                heating = 0
            
            energy_data.append({
                'timestamp': ts,
                'electricity_kwh': max(0, round(electricity, 2)),
                'heating_gcal': max(0, round(heating, 3)),
                'total_power_kw': round(electricity / 0.5, 2)  # кВт за 30 мин
            })
        
        return pd.DataFrame(energy_data)
    
    def _generate_equipment_data(self, sensors_df: pd.DataFrame) -> pd.DataFrame:
        """
        Генерация данных о состоянии оборудования
        """
        # Группируем по минутным интервалам
        sensors_df = sensors_df.copy()
        sensors_df.set_index('timestamp', inplace=True)
        
        equipment_df = sensors_df.resample('1T').agg({
            'temperature': 'mean',
            'light_level': 'mean'
        }).reset_index()
        
        equipment_data = []
        for idx, row in equipment_df.iterrows():
            ts = row['timestamp']
            temp = row['temperature']
            light = row['light_level']
            
            # Статус HVAC
            if pd.notna(temp):
                if temp > 24:
                    hvac_status = 'cooling'
                elif temp < 20:
                    hvac_status = 'heating'
                else:
                    hvac_status = 'idle'
            else:
                hvac_status = 'off'
            
            # Статус освещения
            if pd.notna(light):
                lighting_status = 'on' if light > 100 else 'off'
            else:
                lighting_status = 'off'
            
            # Статус вентиляции (на основе CO2)
            co2_avg = sensors_df.loc[ts - pd.Timedelta(minutes=5):ts, 'co2'].mean() if not sensors_df.loc[ts - pd.Timedelta(minutes=5):ts].empty else 500
            
            if pd.notna(co2_avg):
                ventilation_status = 'high' if co2_avg > 800 else 'medium' if co2_avg > 600 else 'low'
            else:
                ventilation_status = 'off'
            
            equipment_data.append({
                'timestamp': ts,
                'hvac_status': hvac_status,
                'lighting_status': lighting_status,
                'ventilation_status': ventilation_status,
                'equipment_load': np.random.uniform(0.3, 0.9)  # Загрузка оборудования
            })
        
        return pd.DataFrame(equipment_data)


# Функция для быстрой генерации и сохранения
def generate_and_save_data(output_dir: str = 'data', days: int = 30):
    """
    Генерация и сохранение всех данных
    
    Args:
        output_dir: Папка для сохранения
        days: Количество дней данных
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    generator = BMSDataGenerator(seed=42)
    all_data = generator.generate_all_data(days=days)
    
    # Сохраняем каждый датасет
    for name, df in all_data.items():
        filename = os.path.join(output_dir, f'{name}_data.csv')
        df.to_csv(filename, index=False)
        print(f"Сохранено: {filename} ({len(df)} записей)")
    
    # Сохраняем небольшой sample для демонстрации
    sample_size = min(1000, len(all_data['sensors']))
    all_data['sensors'].head(sample_size).to_csv(
        os.path.join(output_dir, 'sample_sensors_data.csv'), index=False
    )
    
    print("\n✅ Все данные сохранены!")
    return all_data


if __name__ == "__main__":
    # При запуске скрипта напрямую
    data = generate_and_save_data(days=7)  # 7 дней для теста
    print("\nПример данных:")
    for name, df in data.items():
        print(f"\n{name}: {df.shape}")
        print(df.head(2))