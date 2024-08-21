import os
import requests

def get_weather_data(
    lat: float,
    lon: float,
    date: str,
    startTime: str,
    endTime: str,
):
    try:
        response = requests.get(f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{lat},{lon}/{date}?key={os.getenv('VISUAL_CROSSING_API_KEY')}")
        hourly_data = response.json()["days"][0]["hours"]
        weather_data_list = []
        for item in hourly_data:
            if startTime <= item["datetime"] <= endTime:
                weather_data_list.append({
                    "time": item["datetime"],
                    "temp": item["temp"],
                    "feelslike": item["feelslike"],
                    "precipprob": item["precip"],
                    "conditions": item["conditions"],
                    "cloudcover": item["cloudcover"],
                    "uvindex": item["uvindex"],
                })
        return weather_data_list
    except Exception as e:
        print(e)
        return []

def summarize_weather_data(weather_data_list):
    if not weather_data_list:
        return ""

    avg_temp = sum(item['temp'] for item in weather_data_list) / len(weather_data_list)
    avg_feelslike = sum(item['feelslike'] for item in weather_data_list) / len(weather_data_list)
    avg_precipprob = sum(item['precipprob'] for item in weather_data_list) / len(weather_data_list)
    max_precipprob = max(item['precipprob'] for item in weather_data_list)
    predominant_conditions = max(set(item['conditions'] for item in weather_data_list), key=lambda c: sum(1 for item in weather_data_list if item['conditions'] == c))
    avg_cloudcover = sum(item['cloudcover'] for item in weather_data_list) / len(weather_data_list)
    max_uvindex = max(item['uvindex'] for item in weather_data_list)

    weather_summary = f"Average temperature: {avg_temp:.1f}°F (feels like {avg_feelslike:.1f}°F). "
    weather_summary += f"Average precipitation probability: {avg_precipprob:.1f}%, with a maximum of {max_precipprob}%. "
    weather_summary += f"Predominant conditions: {predominant_conditions}. "
    weather_summary += f"Average cloud cover: {avg_cloudcover:.1f}%. "
    weather_summary += f"Maximum UV index: {max_uvindex}."

    return weather_summary