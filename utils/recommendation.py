def recommend_foods(foods, preference, max_price=None):

    recommendations = []

    preference = preference.lower()

    for food in foods:

        tags = [tag.lower() for tag in food.get("tags", [])]

        if preference in tags:

            if max_price is None or food["price"] <= max_price:
                recommendations.append(food)

    return recommendations