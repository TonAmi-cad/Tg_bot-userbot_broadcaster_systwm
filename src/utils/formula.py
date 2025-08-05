def calc_credit(car_price, deposit, payment_period):
    # Define the variable percentages based on the leasing term
    if payment_period == 12:
        variable_percentage = 0.29
    elif payment_period == 18:
        variable_percentage = 0.435
    elif payment_period == 24:
        variable_percentage = 0.58
    elif payment_period == 36:
        variable_percentage = 0.87
    else:
        raise ValueError("Invalid payment period. Choose 12, 18, 24, or 36 months.")

    deposit_amount = car_price * (deposit / 100)
    formula = ((car_price - deposit_amount) + (car_price - deposit_amount) * variable_percentage) / payment_period
    return f"{formula:.2f}"
