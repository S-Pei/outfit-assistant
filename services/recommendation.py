MISSING_LOW = float("-inf")
MISSING_HIGH = float("inf")


def _as_number(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


RAIN_WIND_RULES = [
    (lambda pop, wind: pop >= 60 and wind >= 9, "Waterproof coat"),
    (lambda pop, wind: pop >= 60, "Umbrella"),
    (lambda pop, wind: pop >= 35, "Waterproof coat"),
    (lambda pop, wind: wind >= 9, "Windbreaker"),
]


TEMP_RULES = [
    (lambda low, high: low <= 8 and high >= 20, "Puffer + removable layer"),
    (lambda low, high: low <= 5, "Thick puffer"),
    (lambda low, high: low <= 10, "Puffer"),
    (lambda low, high: low <= 15, "Trench coat"),
    (lambda low, high: low <= 20, "Hoodie"),
]


HIGH_TEMP_RULES = [
    (lambda high: high >= 25, "T-shirt/singlet, shorts"),
    (lambda high: high >= 20, "Short sleeves"),
    (lambda high: high >= 15, "T-shirt"),
    (lambda high: True, "Heat-tech"),
]


NIGHT_TEMP_RULES = [
    (lambda night: night <= 8, "Night: Puffer"),
    (lambda night: night <= 15, "Night: Hoodie"),
    (lambda night: night <= 18, "Night: Jacket"),
]


def _first_match(rules, *values):
    for matches, recommendation in rules:
        if matches(*values):
            return recommendation
    return None


def _unique(items):
    unique_items = []
    for item in items:
        if item and item not in unique_items:
            unique_items.append(item)
    return unique_items


def make_daily_recommendation(max_pop, max_wind, low_temp, high_temp, night_temp=None):
    pop_value = _as_number(max_pop, MISSING_LOW)
    wind_value = _as_number(max_wind, MISSING_LOW)
    low_value = _as_number(low_temp, MISSING_HIGH)
    high_value = _as_number(high_temp, MISSING_LOW)
    night_value = _as_number(night_temp, MISSING_HIGH)
    effective_night_value = night_value if night_value < low_value else MISSING_HIGH

    advice = _unique([
        _first_match(RAIN_WIND_RULES, pop_value, wind_value),
        _first_match(TEMP_RULES, low_value, high_value),
        _first_match(HIGH_TEMP_RULES, high_value),
        _first_match(NIGHT_TEMP_RULES, effective_night_value),
    ])

    return " | ".join(advice) if advice else "Comfortable outfit weather"
