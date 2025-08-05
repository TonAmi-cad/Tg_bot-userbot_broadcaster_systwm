def format_user_info(user_info, phone_number, first_name):
    common_info = (
        f"User: {user_info.id} ({first_name})\n"
        "-----------------------------\n"
        f"Phone Number: {phone_number}\n"
        "-----------------------------\n"
    )

    if user_info.operation == "продаж":
        return (
            common_info +
            f"Operation: {getattr(user_info, 'operation', 'N/A')}\n"
            "-----------------------------\n"
        )
    if user_info.operation == "купівля" and user_info.model == "Інше":
        return (
            common_info +
            f"Operation: {getattr(user_info, 'operation', 'N/A')}\n"
            "-----------------------------\n"
            f"Model: {getattr(user_info, 'model', 'N/A')}\n"
            "-----------------------------\n"
        )
    else:
        return (
            common_info +
            f"Operation: {getattr(user_info, 'operation', 'N/A')}\n"
            "-----------------------------\n"
            f"Model: {getattr(user_info, 'model', 'N/A')}\n"
            "-----------------------------\n"
            f"Price: {getattr(user_info, 'price', 'N/A')}\n"
            "-----------------------------\n"
            f"First Deposit: {getattr(user_info, 'first_deposit', 'N/A')}\n"
            "-----------------------------\n"
            f"Period: {getattr(user_info, 'period', 'N/A')}\n"
            "-----------------------------\n"
            f"Region: {getattr(user_info, 'region', 'N/A')}\n"
            "-----------------------------\n"
            f"Work As: {getattr(user_info, 'work_as', 'N/A')}\n"
            "-----------------------------\n"
        )