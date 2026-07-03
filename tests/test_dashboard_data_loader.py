from fpl_intelligence.dashboard import data_loader as dl


def test_dashboard_key_csv_files_load_without_error():
    assert not dl.load_players_ranked().empty
    assert not dl.load_step6_predictions().empty
    assert not dl.load_raw_accuracy().empty
    assert not dl.load_adjusted_accuracy().empty
    assert not dl.load_top10_metrics().empty
    assert not dl.load_captaincy_backtest().empty
    assert dl.load_step7_summary().strip()
