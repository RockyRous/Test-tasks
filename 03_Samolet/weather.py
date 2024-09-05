import traceback

import requests
from datetime import datetime, timedelta


class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, latitude = 55.7558, longitude = 37.6176):
        """
        :param latitude: широта местоположения
        :param longitude: долгота местоположения
        Default - MSK
        """
        self.latitude = latitude
        self.longitude = longitude

    def get_past_week_weather(self):
        """Получить данные о погоде за последние 7 дней"""
        today = datetime.now().date()
        start_date = today - timedelta(days=6)  # Начало диапазона - 6 дней назад
        end_date = today

        params = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'hourly': 'temperature_2m',
            'timezone': 'auto'
        }

        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()

    def get_temperature_by_weekday(self, weekday):
        """
        Получить среднюю температуру за указанный день недели.

        :param weekday: Название дня недели на английском (например, 'Monday')
        :return: Средняя температура за указанный день
        """
        try:
            weather_data = self.get_past_week_weather()
            today = datetime.now().date()

            # Словарь для преобразования дня недели в индекс
            weekday_to_index = {
                'Понедельник': 0, 'Вторник': 1, 'Среда': 2,
                'Четверг': 3, 'Пятница': 4, 'Суббота': 5, 'Воскресенье': 6
            }

            current_weekday_index = today.weekday()  # Индекс текущего дня недели
            requested_weekday_index = weekday_to_index.get(weekday)

            if requested_weekday_index is None:
                raise ValueError(f"Некорректный ввод дня недели - '{weekday}'.")

            # Рассчитываем на сколько дней назад искать данные
            if requested_weekday_index <= current_weekday_index:
                days_ago = current_weekday_index - requested_weekday_index
            else:
                days_ago = 7 - (requested_weekday_index - current_weekday_index)

            # Дата нужного дня
            target_date = today - timedelta(days=days_ago)
            target_date_str = target_date.isoformat()

            # Извлекаем температуры за этот день
            temperatures = []
            for date, temp_values in zip(weather_data['hourly']['time'], weather_data['hourly']['temperature_2m']):
                if date.startswith(target_date_str):
                    temperatures.append(temp_values)

            if not temperatures:
                raise ValueError(f"Данные о температуре отсутствуют | {weekday}.")

            # Рассчитываем среднюю температуру
            avg_temperature = sum(temperatures) / len(temperatures)
            return round(avg_temperature, 1)
        except Exception as Ex:
            print(f"Error: {Ex}\n{traceback.format_exc()}")
            return None


if __name__ == "__main__":
    weather_service = WeatherService()

    avg_temp = weather_service.get_temperature_by_weekday("Понедельник")
    print(f"Средняя температура в Понедельник: {avg_temp} °C")

    avg_temp = weather_service.get_temperature_by_weekday('Вторник')
    print(f"Средняя температура в Вторник: {avg_temp} °C")

