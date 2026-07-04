def get_bot_response(message):

    msg = message.lower()

    if "hello" in msg or "hi" in msg:
        return "Hello! Welcome to AI Smart Canteen."

    elif "menu" in msg:
        return "Today's menu includes Veg Burger, Pizza, Dosa and Fried Rice."

    elif "price" in msg:
        return "Veg Burger ₹80, Pizza ₹150, Dosa ₹60, Fried Rice ₹120."

    elif "healthy" in msg:
        return "I recommend Dosa. It is healthy and costs only ₹60."

    elif "spicy" in msg:
        return "Fried Rice is our spicy recommendation."

    elif "fast food" in msg:
        return "Veg Burger and Pizza are available."

    elif "order" in msg:
        return "Go to Menu → Add to Cart → Place Order."

    elif "thanks" in msg:
        return "You're welcome! Enjoy your meal."

    else:
        return "Sorry, I didn't understand. Please ask about menu, prices, recommendations, or ordering."