from app.tools.city_image import get_city_image

result = get_city_image.invoke({
    "city": "Chennai"
})

print(result)