
def predict_energy_usage(hour, is_weekend=0):
    """
    Прогнозирует потребление энергии для заданного часа
    
    Параметры:
    -----------
    hour : int
        Час дня (0-23)
    is_weekend : int
        Выходной день (1) или рабочий (0)
    
    Возвращает:
    -----------
    float: Прогнозируемое потребление в кВт·ч
    """
    import numpy as np
    
    # Рассчитываем тригонометрические признаки
    day_sin = np.sin(2 * np.pi * hour / 24)
    day_cos = np.cos(2 * np.pi * hour / 24)
    is_night = 1 if (hour >= 22 or hour <= 6) else 0
    is_peak = 1 if ((8 <= hour <= 10) or (18 <= hour <= 20)) else 0
    
    # Признаки для модели
    features = [[hour, day_sin, day_cos, is_weekend, is_night, is_peak]]
    
    # Загружаем модель
    import pickle
    with open('models/energy_forecast_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    # Делаем прогноз
    prediction = model.predict(features)[0]
    
    return round(prediction, 2)
