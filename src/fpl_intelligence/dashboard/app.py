from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[3] / "src"))

from fpl_intelligence.dashboard import data_loader as dl

st._config.set_option("theme.base", "dark")
st._config.set_option("theme.backgroundColor", "#0B0E0D")
st._config.set_option("theme.secondaryBackgroundColor", "#0F1311")
st._config.set_option("theme.textColor", "#EDEDE8")
st._config.set_option("theme.primaryColor", "#1FD17A")

st.set_page_config(
    page_title="FPL Intelligence",
    page_icon="FI",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            background: #0B0E0D !important;
            color: #EDEDE8 !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        }
        :root {
            --bg: #0B0E0D;
            --surface: #0F1311;
            --border: #1F2422;
            --green: #1FD17A;
            --amber: #F0B90B;
            --red: #E04B4B;
            --text: #EDEDE8;
            --muted: #9A9F9B;
        }
        .stApp {
            background: var(--bg) !important;
            color: var(--text) !important;
        }
        [data-testid="stHeader"], header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
            visibility: hidden !important;
        }
        #MainMenu, footer, [data-testid="stDecoration"] {
            visibility: hidden !important;
            display: none !important;
        }
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"] {
            background: var(--bg) !important;
            border-right: 1px solid var(--border);
            color: var(--text) !important;
        }
        .block-container {
            padding-top: 0.75rem !important;
            max-width: 1500px;
        }
        h1, h2, h3, h4, h5, h6, p, label {
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
            letter-spacing: 0;
        }
        .material-symbols-rounded,
        .material-icons,
        span[class*="material"] {
            font-family: "Material Symbols Rounded", "Material Icons" !important;
        }
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        button[aria-label="Close sidebar"],
        button[aria-label="Open sidebar"] {
            display: none !important;
            visibility: hidden !important;
        }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"],
        .muted {
            color: var(--muted) !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            border-radius: 8px;
            padding: 6px 8px;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: rgba(31, 209, 122, 0.12) !important;
            border-left: 3px solid var(--green);
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
            color: var(--green) !important;
            font-weight: 700;
        }
        .topbar, .card, .metric-card, .callout {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px;
            padding: 16px;
            box-shadow: none !important;
        }
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
        }
        .logo {
            font-size: 28px;
            font-weight: 800;
        }
        .muted {
            color: var(--muted);
        }
        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 6px 10px;
            border: 1px solid var(--border);
            background: #111815;
            font-size: 13px;
        }
        .badge-green {
            color: var(--green);
            border-color: rgba(31, 209, 122, 0.45);
        }
        .badge-amber {
            color: var(--amber);
            border-color: rgba(240, 185, 11, 0.45);
        }
        .badge-red {
            color: var(--red);
            border-color: rgba(224, 75, 75, 0.45);
        }
        .metric-card {
            min-height: 104px;
        }
        .metric-label {
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 28px;
            font-weight: 800;
            white-space: nowrap;
            line-height: 1.1;
        }
        .row-card {
            background: #0C100F !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
        }
        .out-badge, .in-badge {
            border-radius: 6px;
            padding: 4px 7px;
            font-weight: 700;
            font-size: 12px;
        }
        .out-badge { background: rgba(224,75,75,.16); color: var(--red); }
        .in-badge { background: rgba(31,209,122,.16); color: var(--green); }
        .chip {
            display: inline-grid;
            place-items: center;
            width: 28px;
            height: 28px;
            border-radius: 6px;
            font-weight: 800;
            color: #08100D;
            margin: 2px;
        }
        .chip-1, .chip-2 { background: var(--green); }
        .chip-3 { background: var(--amber); }
        .chip-4, .chip-5 { background: var(--red); color: white; }
        .avatar {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: inline-grid;
            place-items: center;
            background: #152019;
            color: var(--green);
            border: 1px solid rgba(31,209,122,.45);
            font-weight: 800;
            margin-right: 10px;
        }
        div[data-testid="stDataFrame"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            overflow: hidden;
        }
        div[data-testid="stDataFrame"] [role="grid"],
        div[data-testid="stDataFrame"] [role="row"],
        div[data-testid="stDataFrame"] [role="gridcell"],
        div[data-testid="stDataFrame"] [role="columnheader"],
        div[data-testid="stDataFrame"] [data-testid="StyledDataFrameDataCell"],
        div[data-testid="stDataFrame"] [data-testid="StyledDataFrameColumnHeader"] {
            background: var(--surface) !important;
            background-color: var(--surface) !important;
            color: var(--text) !important;
        }
        [data-testid="stTable"], [data-testid="stDataFrameResizable"] {
            background: var(--surface) !important;
        }
        .stDataFrame div {
            color: var(--text) !important;
        }
        button[kind], .stButton button {
            background: var(--surface) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
        }
        button[kind]:hover, .stButton button:hover {
            border-color: var(--green) !important;
            color: var(--green) !important;
        }
        [data-baseweb="select"] > div {
            background: var(--surface) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            padding: 7px 8px;
            border-bottom: 1px solid var(--border);
            color: var(--text);
            text-align: left;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


def render_topbar(gameweek: int, confidence: str) -> None:
    badge_class = {
        "High": "badge-green",
        "Medium": "badge-amber",
        "Low": "badge-red",
    }.get(confidence, "badge-amber")
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="logo">FPL Intelligence</div>
                <div class="muted">GW{gameweek} model view - deadline text placeholder</div>
            </div>
            <div>
                <span class="badge {badge_class}">Model confidence: {confidence}</span>
                <span class="badge">Refresh</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def initials(name: str) -> str:
    parts = [part for part in name.replace("-", " ").split() if part]
    return "".join(part[0].upper() for part in parts[:2])


def risk_badge(value: float) -> str:
    if value >= 0.7:
        return "green"
    if value >= 0.4:
        return "amber"
    return "red"


def fdr_chip(value: int | float) -> str:
    fdr = int(value) if pd.notna(value) else 3
    return f'<span class="chip chip-{fdr}">{fdr}</span>'


def dark_html_table(dataframe: pd.DataFrame, columns: list[str]) -> str:
    header = "".join(f"<th>{column}</th>" for column in columns)
    rows = []
    for _, row in dataframe[columns].iterrows():
        cells = "".join(f"<td>{row[column]}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def minutes_security_color(value: float) -> str:
    if value >= 0.7:
        color = "rgba(31,209,122,.20)"
    elif value >= 0.4:
        color = "rgba(240,185,11,.20)"
    else:
        color = "rgba(224,75,75,.20)"
    return f"background-color: {color}; color: #EDEDE8"


def xp_cell_color(value: float, average: float) -> str:
    if value >= average:
        return "background-color: rgba(31,209,122,.18); color: #EDEDE8"
    return "background-color: rgba(224,75,75,.16); color: #EDEDE8"


def dark_table_style(dataframe: pd.DataFrame):
    return dataframe.style.set_properties(
        **{
            "background-color": "#0F1311 !important",
            "color": "#EDEDE8 !important",
            "border-color": "#1F2422 !important",
        }
    ).set_table_styles(
        [
            {
                "selector": "th, th.col_heading, th.blank, th.row_heading",
                "props": [
                    ("background-color", "#0B0E0D !important"),
                    ("color", "#EDEDE8 !important"),
                    ("border-color", "#1F2422 !important"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("background-color", "#0F1311 !important"),
                    ("color", "#EDEDE8 !important"),
                    ("border-color", "#1F2422 !important"),
                ],
            },
        ]
    )


def highlight_first_row(row: pd.Series, first_index: int) -> list[str]:
    if row.name == first_index:
        return ["background-color: rgba(31,209,122,.16)" for _ in row]
    return ["" for _ in row]


def page_overview() -> None:
    predictions = dl.load_step6_predictions()
    players = dl.load_players_ranked()
    historical = dl.load_historical_player_gw()
    raw_accuracy = dl.load_raw_accuracy()
    model = dl.default_model(predictions)
    gameweek = dl.latest_prediction_gameweek(predictions)
    gw_predictions = dl.model_predictions_for_gameweek(predictions, model, gameweek)
    squad = dl.get_demo_squad(predictions, model, gameweek)
    top_11_points = squad["expected_points_adjusted"].sum()

    render_topbar(gameweek, dl.model_confidence(raw_accuracy))

    cols = st.columns(4)
    with cols[0]:
        metric_card(f"Predicted points GW{gameweek}", f"{top_11_points:.1f}")
    with cols[1]:
        metric_card("Squad value", "&pound;101.3m")
    with cols[2]:
        metric_card("Overall rank", "312k")
    with cols[3]:
        metric_card("Free transfers", "2")

    left, right = st.columns([0.6, 0.4])
    with left:
        st.subheader("Transfer Suggestions")
        suggestions = dl.get_transfer_suggestions(predictions, players, model, gameweek)
        for _, row in suggestions.iterrows():
            out_meta = f"xP {row['out_xp']:.1f} - {row['reason']}"
            in_meta = f"xP {row['in_xp']:.1f} - GBP {row['in_price']:.1f}"
            net_gain = f"{row['net_gain']:+.1f} pts (after -4 hit if applicable)"
            st.markdown(
                f"""
                <div class="row-card">
                    <span class="out-badge">OUT</span>
                    <b>{row['out_player']}</b> <span class="muted">{row['out_team']}</span>
                    <span class="muted">{out_meta}</span>
                    &nbsp; -> &nbsp;
                    <span class="in-badge">IN</span>
                    <b>{row['in_player']}</b> <span class="muted">{row['in_team']}</span>
                    <span class="muted">{in_meta}</span>
                    <div class="muted">Net gain: {net_gain}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.button("See model reasoning", disabled=True)

    with right:
        st.subheader("Captaincy")
        captains = gw_predictions.sort_values("expected_points_adjusted", ascending=False).head(2)
        for rank, (_, row) in enumerate(captains.iterrows(), start=1):
            badge = "badge-green" if rank == 1 else "badge"
            fixture_text = "Easy fixture" if row["opponent_strength"] < 1210 else "Stable role"
            captain_meta = (
                f"xP adj. {row['expected_points_adjusted']:.1f} - "
                f"ownership {row['selected_by_percent']:.1f}%"
            )
            minutes_reason = (
                f"{fixture_text} + {row['probability_60_plus_minutes']:.0%} "
                "minutes probability"
            )
            st.markdown(
                f"""
                <div class="row-card">
                    <span class="avatar">{initials(row['player_name'])}</span>
                    <span class="{badge}">#{rank}</span>
                    <b>{row['player_name']}</b>
                    <div class="muted">{captain_meta}</div>
                    <div>{minutes_reason}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    squad_col, fixture_col = st.columns([0.55, 0.45])
    with squad_col:
        st.subheader("My Squad - Predicted Points")
        squad_view = squad.copy()
        squad_view["position_average"] = dl.position_average_xp(squad_view)
        squad_view["xP GWN"] = squad_view["expected_points_adjusted"]
        squad_view["form"] = squad_view["points_last_3"]
        squad_table = squad_view[["position", "player_name", "form", "xP GWN"]].rename(
            columns={"position": "Pos", "player_name": "Player"}
        )
        squad_table["xP GWN"] = squad_table["xP GWN"].map(lambda value: f"{value:.1f}")
        st.markdown(dark_html_table(squad_table, list(squad_table.columns)), unsafe_allow_html=True)

    with fixture_col:
        st.subheader("Fixture Ticker")
        ticker = dl.build_fixture_ticker(historical, team_limit=20)
        html_rows = []
        for _, row in ticker.iterrows():
            cells = "".join(
                f"<td>{fdr_chip(row[col])}</td>"
                for col in ticker.columns
                if col != "team"
            )
            html_rows.append(f"<tr><td>{row['team']}</td>{cells}</tr>")
        header = "".join(f"<th>{col}</th>" for col in ticker.columns)
        st.markdown(
            f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(html_rows)}</tbody></table>",
            unsafe_allow_html=True,
        )

        st.subheader("Price Change Predictor")
        rising, falling = dl.get_price_change_estimates(players)
        st.caption("Rule-based estimate, not a model prediction.")
        st.write("Likely rises")
        rising_view = rising[["player_name", "team_name", "selected_by_percent", "form"]].head(5)
        st.markdown(
            dark_html_table(rising_view, list(rising_view.columns)),
            unsafe_allow_html=True,
        )
        st.write("Likely falls")
        falling_view = falling[["player_name", "team_name", "selected_by_percent", "form"]].head(3)
        st.markdown(
            dark_html_table(falling_view, list(falling_view.columns)),
            unsafe_allow_html=True,
        )

    st.subheader("Low Ownership, High xP")
    diff_cols = st.columns(3)
    differentials = dl.get_differentials(predictions, model, gameweek)
    for col, (_, row) in zip(diff_cols, differentials.iterrows(), strict=False):
        with col:
            metric_card(
                row["player_name"],
                f"{row['expected_points_adjusted']:.1f} xP",
            )
            st.caption(f"{row['team']} - {row['selected_by_percent']:.1f}% owned")


def page_player_rankings() -> None:
    st.header("Player Rankings")
    try:
        players = dl.load_players_ranked()
    except ValueError as error:
        st.error(str(error))
        return

    with st.expander("Source columns"):
        st.write(", ".join(players.columns))

    missing = [
        column for column in dl.PLAYERS_RANKED_REQUIRED_COLUMNS if column not in players.columns
    ]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return

    positions = ["All"] + sorted(players["position"].dropna().astype(str).unique().tolist())
    selected = st.selectbox("Position", positions)
    view = players.copy()
    if selected != "All":
        view = view[view["position"] == selected]
    if view.empty:
        st.warning(f"No players found for position: {selected}")
        return

    columns = [
        "player_name",
        "team_name",
        "position",
        "price",
        "points_per_game",
        "form",
        "minutes_security",
        "value_score",
        "captain_score",
        "transfer_score",
    ]
    st.dataframe(
        dark_table_style(
            view[columns]
            .rename(
                columns={
                    "player_name": "name",
                    "team_name": "team",
                    "points_per_game": "PPG",
                }
            )
            .fillna(0)
        ).map(
            minutes_security_color,
            subset=["minutes_security"],
        ),
        use_container_width=True,
        hide_index=True,
    )


def page_captaincy() -> None:
    predictions = dl.load_step6_predictions()
    gameweek = dl.latest_prediction_gameweek(predictions)
    models = sorted(predictions["model"].unique())
    selected_model = st.selectbox(
        "Model",
        models,
        index=models.index(dl.default_model(predictions)),
    )
    st.header("Captaincy Picks")
    st.caption("Minutes probability shown - low values indicate rotation risk.")
    top = (
        dl.model_predictions_for_gameweek(predictions, selected_model, gameweek)
        .sort_values("expected_points_adjusted", ascending=False)
        .head(10)
    )
    display = top[
        [
            "player_name",
            "team",
            "position",
            "predicted_points",
            "probability_60_plus_minutes",
            "expected_points_adjusted",
            "selected_by_percent",
        ]
    ].copy()
    st.dataframe(
        dark_table_style(display).apply(
            lambda row: highlight_first_row(row, display.index[0]),
            axis=1,
        ),
        use_container_width=True,
        hide_index=True,
    )


def page_transfer_targets() -> None:
    players = dl.load_players_ranked().copy()
    st.header("Transfer Targets")
    players["rotation_risk"] = players["minutes_security"].apply(
        lambda value: "rotation risk" if value < 0.4 else ""
    )
    columns = [
        "player_name",
        "team_name",
        "price",
        "value_score",
        "form",
        "selected_by_percent",
        "minutes_security",
        "rotation_risk",
        "transfer_score",
    ]
    st.dataframe(
        dark_table_style(players.sort_values("transfer_score", ascending=False).head(20)[columns]),
        use_container_width=True,
        hide_index=True,
    )


def page_model_comparison() -> None:
    st.header("Which model predicts FPL points best? Here's the evidence.")
    raw = dl.load_raw_accuracy()
    adjusted = dl.load_adjusted_accuracy()
    top10 = dl.load_top10_metrics()
    impact = dl.load_adjustment_impact()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Raw Points Accuracy")
        st.dataframe(dark_table_style(raw), use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Minutes-Adjusted Accuracy")
        st.dataframe(dark_table_style(adjusted), use_container_width=True, hide_index=True)

    combined = pd.concat(
        [
            raw.assign(score_type="raw")[["model", "MAE", "score_type"]],
            adjusted.assign(score_type="adjusted")[["model", "MAE", "score_type"]],
        ],
        ignore_index=True,
    )
    fig = px.bar(
        combined,
        x="model",
        y="MAE",
        color="score_type",
        barmode="group",
        color_discrete_map={"raw": "#F0B90B", "adjusted": "#1FD17A"},
    )
    fig.update_layout(template="plotly_dark", paper_bgcolor="#0B0E0D", plot_bgcolor="#0B0E0D")
    st.plotly_chart(fig, use_container_width=True)

    top10_long = top10.melt(
        id_vars="model",
        value_vars=["precision_at_10", "recall_at_10"],
        var_name="metric",
        value_name="score",
    )
    fig2 = px.bar(
        top10_long,
        x="model",
        y="score",
        color="metric",
        barmode="group",
        color_discrete_map={"precision_at_10": "#1FD17A", "recall_at_10": "#F0B90B"},
    )
    fig2.update_layout(template="plotly_dark", paper_bgcolor="#0B0E0D", plot_bgcolor="#0B0E0D")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
        """
        <div class="callout">
        <b>Key finding:</b> Minutes adjustment improved MAE for every model but worsened
        RMSE. It helps typical predictions but increases some large misses when the
        minutes classifier is wrong.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(dark_table_style(impact), use_container_width=True, hide_index=True)
    st.markdown(
        """
        <div class="card">
        <b>MAE</b>: average prediction miss in FPL points, so lower means more reliable
        week to week.<br>
        <b>RMSE</b>: like MAE but punishes big mistakes more, useful for spotting risky
        models.<br>
        <b>precision@10</b>: how many of the model's top 10 picks were actually top-10
        scorers that week.
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_backtest() -> None:
    st.header(
        "If you had used this model all season, how many captain points would you have earned?"
    )
    captaincy = dl.load_captaincy_backtest()
    predictions = dl.load_step6_predictions()
    timeline = dl.build_captaincy_timeseries(predictions)
    summary = dl.load_step7_summary()

    st.dataframe(dark_table_style(captaincy), use_container_width=True, hide_index=True)
    winner = captaincy.iloc[0]["strategy"]
    colors = {strategy: "#6B7470" for strategy in timeline["strategy"].unique()}
    colors[winner] = "#1FD17A"
    fig = px.line(
        timeline,
        x="gameweek",
        y="cumulative_captain_points",
        color="strategy",
        color_discrete_map=colors,
    )
    fig.update_layout(template="plotly_dark", paper_bgcolor="#0B0E0D", plot_bgcolor="#0B0E0D")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<div class="callout">{summary}</div>', unsafe_allow_html=True)
    st.caption(
        "This backtest covers one season (2025-26). Results may vary across seasons due to "
        "FPL's inherent randomness."
    )


def main() -> None:
    pages = {
        "Overview": page_overview,
        "Player Rankings": page_player_rankings,
        "Captaincy Picks": page_captaincy,
        "Transfer Targets": page_transfer_targets,
        "Model Comparison": page_model_comparison,
        "Backtest Results": page_backtest,
    }
    selected_page = st.sidebar.radio("Navigation", list(pages), label_visibility="collapsed")
    pages[selected_page]()


if __name__ == "__main__":
    main()
