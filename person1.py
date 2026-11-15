"""
Person 1 – Faruk Semih Korkut
Topic: Film genres, ratings and financial performance

Charts
  1. create_violin_plot          – Movie Rating Distribution by Genre
  2. create_treemap              – Box Office Revenue Distribution by Genre
  3. create_parallel_coordinates – Multidimensional Analysis of Movie Performance

Every function takes the (already filtered) DataFrame read from tmdb_cleaned.csv
and returns a Plotly figure, so app.py only needs:

    from person1 import create_violin_plot
    st.plotly_chart(create_violin_plot(filtered_df), use_container_width=True)

The extra keyword arguments are optional; the defaults are the values used in
the presentation.
"""

import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --------------------------------------------------------------------------- #
# Shared style (same font, ink and blue ramp in all three charts)
# --------------------------------------------------------------------------- #
FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BLUE = "#2a78d6"
BLUE_DARK = "#1c5cab"
RED = "#e34948"
NEUTRAL = "#b9b7ae"

# Sequential blue ramp (light -> dark) for magnitudes
BLUE_RAMP = [
    [0.00, "#cde2fb"], [0.17, "#9ec5f4"], [0.33, "#6da7ec"],
    [0.50, "#3987e5"], [0.67, "#256abf"], [0.83, "#184f95"], [1.00, "#0d366b"],
]

MIN_VOTES = 50          # ratings based on fewer votes are too noisy (e.g. 10.0 from 1 vote)
MIN_MONEY = 10_000      # budgets/revenues below $10K are data-entry errors (e.g. budget = $7)


def _base_layout(fig, title, subtitle, height):
    fig.update_layout(
        title=dict(
            text=f"{title}<br><span style='font-size:13px;color:{INK_SECONDARY}'>{subtitle}</span>",
            x=0, xanchor="left", font=dict(size=18, color=INK),
        ),
        font=dict(family=FONT_FAMILY, size=13, color=INK_SECONDARY),
        height=height,
        margin=dict(l=10, r=10, t=90, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(font=dict(family=FONT_FAMILY, size=13)),
    )
    return fig


def _empty_figure(title, message):
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=15, color=INK_MUTED),
                       x=0.5, y=0.5, xref="paper", yref="paper")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _base_layout(fig, title, "No data for the current filters", 300)


def _genre_lists(df):
    """genre_list is stored as JSON text; accept already-parsed lists too."""
    return df["genre_list"].apply(lambda v: json.loads(v) if isinstance(v, str) else (v or []))


def explode_genres(df):
    """One row per (film, genre). A film with 3 genres appears 3 times."""
    out = df.copy()
    out["genre"] = _genre_lists(out)
    out["n_genres"] = out["genre"].apply(len)
    out = out[out["n_genres"] > 0].explode("genre")
    return out


def _money(v):
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v / 1e3:.0f}K"


# --------------------------------------------------------------------------- #
# 1) Violin plot – rating distribution by genre
# --------------------------------------------------------------------------- #
def create_violin_plot(df, min_votes=MIN_VOTES, min_films=30, genres=None):
    """
    Distribution of vote_average for each genre.
    - Only films with at least `min_votes` votes (rating must be reliable).
    - A film counts in every genre it belongs to.
    - Genres with fewer than `min_films` films are hidden (a violin needs data).
    - Genres are sorted by median rating, best at the top.
    """
    title = "Movie Rating Distribution by Genre"
    data = df[df["vote_count"] >= min_votes]
    e = explode_genres(data)
    if genres:
        e = e[e["genre"].isin(genres)]
    counts = e["genre"].value_counts()
    e = e[e["genre"].isin(counts[counts >= min_films].index)]
    if e.empty:
        return _empty_figure(title, "No genre has enough rated films for these filters.")

    medians = e.groupby("genre")["vote_average"].median().sort_values()
    order = list(medians.index)                 # lowest first -> drawn at the bottom
    labels = {g: f"{g} ({counts[g]:,})" for g in order}
    overall_median = data.loc[data.index.isin(e.index), "vote_average"].median()

    fig = go.Figure()
    for g in order:
        sub = e[e["genre"] == g]
        fig.add_trace(go.Violin(
            x=sub["vote_average"],
            y=[labels[g]] * len(sub),
            name=labels[g],
            orientation="h",
            line=dict(color=BLUE_DARK, width=1.5),
            fillcolor="rgba(42,120,214,0.30)",
            box=dict(visible=True, width=0.35, fillcolor="rgba(255,255,255,0.9)",
                     line=dict(color=BLUE_DARK, width=1.5)),
            meanline=dict(visible=False),
            points="outliers",
            marker=dict(color=RED, size=6, line=dict(color="white", width=1)),
            text=sub["title"],
            hoveron="violins+points",
            hovertemplate="<b>%{text}</b><br>Rating: %{x:.1f}<extra>" + g + "</extra>",
            spanmode="hard",
            width=0.85,
            showlegend=False,
        ))

    fig.add_vline(x=overall_median, line=dict(color=INK_MUTED, width=1.5, dash="dash"))
    fig.add_annotation(x=overall_median, y=1, yref="paper", yanchor="bottom",
                       text=f"All-film median {overall_median:.1f}", showarrow=False,
                       font=dict(size=12, color=INK_SECONDARY))

    _base_layout(
        fig, title,
        f"{data.loc[data.index.isin(e.index)].shape[0]:,} films with ≥ {min_votes} votes · "
        "sorted by median rating · red dots = outliers (hover for the title)",
        height=max(380, 34 * len(order) + 150),
    )
    fig.update_xaxes(title="Average user rating (0–10)",
                     range=[max(0, e["vote_average"].min() - 0.3), min(10, e["vote_average"].max() + 0.4)],
                     showgrid=True, gridcolor=GRID, zeroline=False, dtick=1)
    fig.update_yaxes(title=None, categoryorder="array", categoryarray=[labels[g] for g in order],
                     showgrid=False, ticksuffix="  ")
    fig.update_layout(violinmode="overlay", violingap=0.15)
    return fig


# --------------------------------------------------------------------------- #
# 2) Treemap – box office revenue by genre (click a genre to see its films)
# --------------------------------------------------------------------------- #
def create_treemap(df, top_films=10, genres=None):
    """
    Size  = share of total box office revenue. A film's revenue is split equally
            between its genres (Avatar has 4 genres -> 1/4 goes to each), so no
            dollar is counted twice and the tiles add up to 100 %.
    Color = average revenue per film (full revenue, not the split share).
    Click a genre to zoom in: its `top_films` biggest films + the rest as "Other films".
    """
    title = "Box Office Revenue Distribution by Genre"
    r = df[df["revenue_valid"].notna()].copy()
    e = explode_genres(r)
    if genres:
        e = e[e["genre"].isin(genres)]
    if e.empty:
        return _empty_figure(title, "No films with known revenue for these filters.")
    e["share"] = e["revenue_valid"] / e["n_genres"]

    total = e["share"].sum()
    ids, labels, parents, values, colors, texts, hovers = [], [], [], [], [], [], []

    def add(node_id, label, parent, value, color, text, hover):
        ids.append(node_id); labels.append(label); parents.append(parent)
        values.append(value); colors.append(color / 1e6); texts.append(text); hovers.append(hover)

    n_all = e["id"].nunique()
    add("root", "All genres", "", 0, e.drop_duplicates("id")["revenue_valid"].mean(),
        "<b>%{label}</b>",
        f"<b>All genres</b><br>Total box office: {_money(total)}<br>Films: {n_all:,}")

    genre_stats = (e.groupby("genre")
                     .agg(alloc=("share", "sum"), films=("id", "count"), avg=("revenue_valid", "mean"))
                     .sort_values("alloc", ascending=False))

    for g, row in genre_stats.iterrows():
        gid = f"g::{g}"
        add(gid, g, "root", 0, row["avg"],
            "<b>%{label}</b><br>%{percentRoot:.1%}",
            f"<b>{g}</b><br>Share of total box office: {row['alloc'] / total:.1%}"
            f"<br>Revenue (split by genre): {_money(row['alloc'])}"
            f"<br>Films: {int(row['films']):,}"
            f"<br>Average revenue per film: {_money(row['avg'])}"
            "<br><i>Click to see the top films</i>")

        films = e[e["genre"] == g].sort_values("share", ascending=False)
        top, rest = films.head(top_films), films.iloc[top_films:]
        for _, f in top.iterrows():
            add(f"f::{g}::{f['id']}", f["title"], gid, f["share"], f["revenue_valid"],
                "%{label}<br>%{percentParent:.1%}",
                f"<b>{f['title']}</b> ({int(f['release_year']) if pd.notna(f['release_year']) else 'n/a'})"
                f"<br>Full revenue: {_money(f['revenue_valid'])}"
                f"<br>Counted in {g}: {_money(f['share'])} (1/{int(f['n_genres'])} – film has {int(f['n_genres'])} genres)"
                f"<br>Share of {g}: {f['share'] / row['alloc']:.1%}")
        if len(rest):
            add(f"o::{g}", f"Other {len(rest):,} films", gid, rest["share"].sum(), rest["revenue_valid"].mean(),
                "%{label}<br>%{percentParent:.1%}",
                f"<b>Other {len(rest):,} {g} films</b><br>Counted in {g}: {_money(rest['share'].sum())}"
                f"<br>Share of {g}: {rest['share'].sum() / row['alloc']:.1%}"
                f"<br>Average revenue per film: {_money(rest['revenue_valid'].mean())}")

    cmax = float(genre_stats["avg"].max() / 1e6)
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values,
        branchvalues="remainder",
        marker=dict(colors=colors, colorscale=BLUE_RAMP, cmin=0, cmax=cmax,
                    line=dict(color="white", width=2), pad=dict(t=24, l=3, r=3, b=3),
                    colorbar=dict(title=dict(text="Avg revenue<br>per film", side="top"),
                                  tickprefix="$", ticksuffix="M", thickness=12, len=0.8,
                                  outlinewidth=0)),
        texttemplate=texts,
        customdata=hovers,
        hovertemplate="%{customdata}<extra></extra>",
        maxdepth=2,
        pathbar=dict(visible=True, thickness=24),
        tiling=dict(pad=2),
        textfont=dict(family=FONT_FAMILY, size=14),
        root=dict(color="#f0efec"),
    ))
    _base_layout(
        fig, title,
        f"{n_all:,} films with known revenue · tile size = share of total box office · "
        "color = average revenue per film · click a genre to zoom in",
        height=620,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=115, b=10))
    return fig


# --------------------------------------------------------------------------- #
# 3) Parallel coordinates – budget, revenue, popularity, rating, runtime
# --------------------------------------------------------------------------- #
def _tick_money(v):
    if v >= 1e9:
        return f"${v / 1e9:g}B"
    if v >= 1e6:
        return f"${v / 1e6:g}M"
    return f"${v / 1e3:g}K"


def _log_ticks(values, candidates, fmt):
    lo, hi = np.nanmin(values), np.nanmax(values)
    ticks = [c for c in candidates if lo - 0.01 <= np.log10(c) <= hi + 0.01]
    return [float(np.log10(t)) for t in ticks], [fmt(t) for t in ticks]


def create_parallel_coordinates(df, min_votes=MIN_VOTES, highlight_rating=None):
    """
    One line per film across five axes. Budget, revenue and popularity are on a
    log10 scale (a few blockbusters would otherwise squeeze everything else flat).
    Line color = rating: red below the median, grey around it, blue above it.

    Interactions in the chart itself: drag along any axis to select a range
    (brushing), drag an axis title to reorder axes.
    `highlight_rating=7.5` pre-selects films rated 7.5+ (handy for the demo).
    """
    title = "Multidimensional Analysis of Movie Performance"
    p = df[(df["budget_valid"] >= MIN_MONEY) & (df["revenue_valid"] >= MIN_MONEY)
           & df["runtime_valid"].notna() & (df["vote_count"] >= min_votes)].copy()
    if len(p) < 2:
        return _empty_figure(title, "Not enough films with budget, revenue and runtime for these filters.")

    p["log_budget"] = np.log10(p["budget_valid"])
    p["log_revenue"] = np.log10(p["revenue_valid"])
    p["log_popularity"] = np.log10(p["popularity"].clip(lower=0.01))

    money = [1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10]
    pop = [0.01, 0.1, 1, 10, 100, 1000]
    bt, bl = _log_ticks(p["log_budget"], money, _tick_money)
    rt, rl = _log_ticks(p["log_revenue"], money, _tick_money)
    pt, pl = _log_ticks(p["log_popularity"], pop, lambda v: f"{v:g}")

    rating = p["vote_average"]
    lo, hi, mid = rating.min(), rating.max(), rating.median()
    mid_pos = 0.5 if hi == lo else float(np.clip((mid - lo) / (hi - lo), 0.05, 0.95))
    colorscale = [[0, "#b8322f"], [mid_pos * 0.5, RED], [mid_pos, NEUTRAL],
                  [mid_pos + (1 - mid_pos) * 0.5, BLUE], [1, "#0d366b"]]

    rating_dim = dict(label="Rating (0–10)", values=rating,
                      range=[np.floor(lo), np.ceil(hi)])
    if highlight_rating is not None:
        rating_dim["constraintrange"] = [highlight_rating, np.ceil(hi)]

    fig = go.Figure(go.Parcoords(
        line=dict(color=rating, colorscale=colorscale, cmin=lo, cmax=hi, showscale=True,
                  colorbar=dict(title=dict(text="Rating", side="top"), thickness=12, len=0.8,
                                outlinewidth=0)),
        dimensions=[
            dict(label="Budget", values=p["log_budget"], tickvals=bt, ticktext=bl),
            dict(label="Revenue", values=p["log_revenue"], tickvals=rt, ticktext=rl),
            dict(label="Popularity", values=p["log_popularity"], tickvals=pt, ticktext=pl),
            rating_dim,
            dict(label="Runtime (min)", values=p["runtime_valid"],
                 range=[np.floor(p["runtime_valid"].min() / 10) * 10,
                        np.ceil(p["runtime_valid"].max() / 10) * 10]),
        ],
        unselected=dict(line=dict(color="#d9d8d2", opacity=0.15)),
        labelfont=dict(size=14, color=INK),
        tickfont=dict(size=12, color=INK_SECONDARY),
        rangefont=dict(size=1, color="rgba(0,0,0,0)"),
        labelangle=0,
    ))
    _base_layout(
        fig, title,
        f"{len(p):,} films with known budget, revenue and runtime and ≥ {min_votes} votes · "
        "budget, revenue, popularity on log scale · drag on an axis to filter",
        height=560,
    )
    fig.update_layout(margin=dict(l=70, r=40, t=150, b=30))
    return fig


# --------------------------------------------------------------------------- #
# Texts for the dashboard / README (findings computed on the full dataset)
# --------------------------------------------------------------------------- #
CHART_INFO = {
    "violin": {
        "title": "Movie Rating Distribution by Genre",
        "how_to_read": "Each violin shows how ratings are spread inside one genre; the white box is the "
                       "middle 50 % of films and its line is the median. Red dots are outlier films.",
        "insight": "Documentary (7.2), War (6.95) and History (6.8) have the highest median ratings, "
                   "Horror the lowest (5.85). Science Fiction has the widest spread: it produces both "
                   "classics and flops.",
    },
    "treemap": {
        "title": "Box Office Revenue Distribution by Genre",
        "how_to_read": "Tile size is the genre's share of total box office (multi-genre films are split "
                       "equally). Darker blue = higher average revenue per film. Click a genre to see its films.",
        "insight": "Action, Comedy, Adventure and Drama each take 12–13 % and together earn about half of "
                   "all revenue, but in different ways: Drama needs 1,527 films at $78M per film, Adventure "
                   "only 675 films at $244M per film. Animation has the highest average ($277M per film).",
    },
    "parallel": {
        "title": "Multidimensional Analysis of Movie Performance",
        "how_to_read": "Each line is one film across five axes. Drag along an axis to keep only a range; "
                       "drag an axis title to reorder.",
        "insight": "Budget and revenue move together, but budget does not buy ratings: films rated 7.5+ "
                   "have a median budget of $16M versus $35M for films rated below 6. Runtime is the axis "
                   "most linked to rating: 60 % of 7.5+ films run two hours or longer, against 12 % of films below 6.",
    },
}
