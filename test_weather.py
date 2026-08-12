from app.tools.weather import get_weather


result = get_weather.invoke({
    "city": "Chennai"
})

print(result)