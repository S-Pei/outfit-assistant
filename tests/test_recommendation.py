import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.recommendation import make_daily_recommendation


def test_heavy_rain_and_windy():
    assert make_daily_recommendation(80, 10, 11, 19) == "Waterproof coat | Trench coat | T-shirt"


def test_heavy_rain_and_calm():
    assert make_daily_recommendation(80, 3, 11, 19) == "Umbrella | Trench coat | T-shirt"


def test_windy_without_rain():
    assert make_daily_recommendation(10, 10, 11, 19) == "Windbreaker | Trench coat | T-shirt"


def test_cold_morning_warm_afternoon():
    assert make_daily_recommendation(10, 3, 5, 21) == "Puffer + removable layer | Short sleeves"


def test_mild_day():
    assert make_daily_recommendation(10, 3, 12, 18) == "Trench coat | T-shirt"


def test_hot_day():
    assert make_daily_recommendation(10, 3, 18, 26) == "Hoodie | T-shirt/singlet, shorts"


def test_cold_after_sunset():
    assert make_daily_recommendation(10, 3, 14, 21, 7) == "Trench coat | Short sleeves | Night: Puffer"


def test_night_advice_only_when_colder_than_low():
    assert make_daily_recommendation(10, 3, 7, 21, 9) == "Puffer + removable layer | Short sleeves"


def main():
    tests = [
        test_heavy_rain_and_windy,
        test_heavy_rain_and_calm,
        test_windy_without_rain,
        test_cold_morning_warm_afternoon,
        test_mild_day,
        test_hot_day,
        test_cold_after_sunset,
        test_night_advice_only_when_colder_than_low,
    ]

    for test in tests:
        test()

    print(f"{len(tests)} recommendation tests passed")


if __name__ == "__main__":
    main()
