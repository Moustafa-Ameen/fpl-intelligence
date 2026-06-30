import pandas as pd

from fpl_intelligence.step4_models import split_train_test


def test_split_train_test_uses_2025_26_as_test_only():
    players = pd.DataFrame(
        {
            "season": ["2023-24", "2024-25", "2025-26"],
            "next_gameweek_points": [1, 2, 3],
        }
    )

    train, test = split_train_test(players)

    assert set(train["season"]) == {"2023-24", "2024-25"}
    assert set(test["season"]) == {"2025-26"}
