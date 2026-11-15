import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import pycountry


def create_calendar_heatmap(df):
     
    data = df.copy()

    
    data["release_date"] = pd.to_datetime(
        data["release_date"], errors="coerce"
    )

    
    data = data.dropna(subset=["release_date"])

    
    data["month"] = data["release_date"].dt.month
    data["day"] = data["release_date"].dt.day

    
    counts = (
        data.groupby(["month", "day"])
        .size()
        .unstack(fill_value=0)
        .reindex(
            index=range(1, 13),
            columns=range(1, 32),
            fill_value=0
        )
    )

    months = [
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=counts.values,
            x=list(range(1, 32)),
            y=months,
            colorscale="YlOrRd",
            colorbar=dict(title="Movie Count"),
            hovertemplate=(
                "Month: %{y}<br>"
                "Day: %{x}<br>"
                "Movies: %{z}<extra></extra>"
            )
        )
    )

    fig.update_layout(
        title="Movie Releases by Month and Day",
        xaxis_title="Day of Month",
        yaxis_title="Month",
        height=550
    )

    return fig

# Sankey Diagram
def create_sankey(df):
    data = df[
        ["original_language", "primary_genre", "rating_category"]
    ].copy()

    # Eksik verileri temizle
    data = data.dropna()

    # Metin biçimlerini standartlaþtýr
    for col in data.columns:
        data[col] = data[col].astype(str).str.strip()

    data = data[
        (data["original_language"] != "") &
        (data["primary_genre"] != "") &
        (data["rating_category"] != "")
    ]

    # Düðümlerin birbirine karýþmamasý için
    # her aþamaya farklý bir kimlik veriyoruz.
    language_nodes = [
        "Language: " + x
        for x in sorted(data["original_language"].unique())
    ]

    genre_nodes = [
        "Genre: " + x
        for x in sorted(data["primary_genre"].unique())
    ]

    rating_nodes = [
        "Rating: " + x
        for x in sorted(data["rating_category"].unique())
    ]

    all_nodes = language_nodes + genre_nodes + rating_nodes

    node_index = {
        name: i for i, name in enumerate(all_nodes)
    }

    sources = []
    targets = []
    values = []

    # 1. aþama: Dil -> Tür
    language_genre = (
        data.groupby(["original_language", "primary_genre"])
        .size()
        .reset_index(name="count")
    )

    for _, row in language_genre.iterrows():
        sources.append(
            node_index["Language: " + row["original_language"]]
        )
        targets.append(
            node_index["Genre: " + row["primary_genre"]]
        )
        values.append(int(row["count"]))

    # 2. aþama: Tür -> Puan kategorisi
    genre_rating = (
        data.groupby(["primary_genre", "rating_category"])
        .size()
        .reset_index(name="count")
    )

    for _, row in genre_rating.iterrows():
        sources.append(
            node_index["Genre: " + row["primary_genre"]]
        )
        targets.append(
            node_index["Rating: " + row["rating_category"]]
        )
        values.append(int(row["count"]))

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=15,
                thickness=15,
                label=all_nodes
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values
            )
        )
    )

    fig.update_layout(
        title="Movie Language, Genre and Rating Flow",
        font_size=11,
        height=750
    )

    return fig

# Geographical Map
def create_geographical_map(df):
    data = df.copy()

    # Üretim ülkelerini içeren sütunu kullanýyoruz.
    country_counts = {}

    for value in data["production_countries"].dropna():

        try:
            countries = json.loads(value)
        except (TypeError, ValueError):
            continue

        # Ayný filmde ayný ülkeyi iki kez saymamak için
        seen_countries = set()

        for country in countries:

            country_code = country.get("iso_3166_1")
            country_name = country.get("name")

            if not country_code:
                continue

            # Plotly haritasýnda ISO-3 ülke kodlarýný kullanýyoruz.
            try:
                country_info = pycountry.countries.get(
                    alpha_2=country_code
                )

                if country_info is None:
                    continue

                iso3 = country_info.alpha_3

            except (LookupError, AttributeError):
                continue

            if iso3 in seen_countries:
                continue

            seen_countries.add(iso3)

            if iso3 not in country_counts:
                country_counts[iso3] = {
                    "country": country_name,
                    "movie_count": 0
                }

            country_counts[iso3]["movie_count"] += 1

    map_data = pd.DataFrame([
        {
            "iso3": iso3,
            "country": info["country"],
            "movie_count": info["movie_count"]
        }
        for iso3, info in country_counts.items()
    ])

    if map_data.empty:
        return go.Figure()

    fig = px.choropleth(
        map_data,
        locations="iso3",
        color="movie_count",
        hover_name="country",
        hover_data={"iso3": False, "movie_count": True},
        color_continuous_scale="Blues",
        labels={"movie_count": "Movie Count"},
        title="Movie Production by Country"
    )

    fig.update_layout(
        height=600,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="natural earth"
        )
    )

    return fig