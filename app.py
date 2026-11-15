import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from person1 import (
    create_violin_plot,
    create_treemap,
    create_parallel_coordinates
)


from person2 import (
    create_calendar_heatmap,
    create_sankey,
    create_geographical_map
)

from scatter_plot import create_scatter_html
from sunburst import create_dashboard
from network_diagram import main as create_network_html



st.set_page_config(
    page_title="TMDB Movie Dashboard",
    layout="wide"
)

st.markdown("""
<style>
/* Light theme for Streamlit UI only; Plotly figures retain their own palettes. */
:root { color-scheme: light; }
html, body, [data-testid="stAppViewContainer"], .stApp,
[data-testid="stMain"], [data-testid="stHeader"] {
    background-color: #FAF7F2 !important;
    color: #303030 !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] {
    background-color: #F0ECE5 !important;
    color: #303030 !important;
}
/* Sidebar text, headings, captions and widget labels */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #303030 !important;
}
/* Multi-select and dropdown fields: dark text on white */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="input"] > div {
    background-color: #FFFFFF !important;
    color: #303030 !important;
    border-color: #CFC8BE !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-baseweb="select"] input::placeholder {
    color: #303030 !important;
    -webkit-text-fill-color: #303030 !important;
}
/* Slider values, handles and tick labels */
[data-testid="stSidebar"] [data-testid="stSlider"] *,
[data-testid="stSidebar"] [data-testid="stSliderTickBar"] * {
    color: #303030 !important;
}
/* Sidebar separator */
[data-testid="stSidebar"] hr { border-color: #D6CFC6 !important; }
/* Main app headings and text */
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] p { color: #303030; }
/* Plotly chart containers only, not the figures inside them */
.stPlotlyChart {
    background-color: #FFFFFF;
    border: 1px solid #E6E0D8;
    border-radius: 12px;
    padding: 12px;
}
.block-container { padding-top: 2rem; padding-bottom: 3rem; }
</style>
""", unsafe_allow_html=True)

st.title("TMDB 5000 Movie Dashboard")


df = pd.read_csv("tmdb_cleaned.csv")
# SIDEBAR FILTERS
st.sidebar.header("Movie Filters")
st.sidebar.caption("Use these controls to filter all nine visualizations.")

# An empty genre selection means all genres, so the sidebar stays compact.
genres = sorted(df["primary_genre"].dropna().unique().tolist())
selected_genres = st.sidebar.multiselect(
    "Movie Genres",
    options=genres,
    default=[],
    placeholder="All genres (choose one or more)",
    help="Leave empty to include all genres. Choose one genre to see only that genre, or several to compare them.",
)
st.sidebar.caption(
    "All genres are shown when no genre is selected. "
    "Select one or more genres to narrow the results."
)

min_year = int(df["release_year"].dropna().min())
max_year = int(df["release_year"].dropna().max())
selected_years = st.sidebar.slider(
    "Release Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    help="Only show movies released between the selected start and end years (inclusive).",
)
st.sidebar.caption("Only movies released within this year range are included.")

min_rating = st.sidebar.slider(
    "Minimum Audience Rating (0–10)",
    min_value=0.0,
    max_value=10.0,
    value=0.0,
    step=0.5,
    help="Hide movies whose TMDB average audience rating is below this value.",
)
st.sidebar.caption("Movies rated below this score are excluded.")

# APPLY FILTERS
# No selected genres = all genres, including rows without a primary genre.
genre_mask = (
    pd.Series(True, index=df.index)
    if not selected_genres
    else df["primary_genre"].isin(selected_genres)
)
filtered_df = df[
    genre_mask
    & df["release_year"].between(selected_years[0], selected_years[1])
    & (df["vote_average"] >= min_rating)
].copy()

st.sidebar.divider()
st.sidebar.caption(f"Showing {len(filtered_df):,} of {len(df):,} movies")

st.write("Total Movies:", len(df))
st.write("Filtered Movies:", len(filtered_df))


with st.expander("View Movie Dataset"):
    st.dataframe(
        filtered_df,
        use_container_width=True
    )



st.subheader("Calendar Heatmap")

fig = create_calendar_heatmap(filtered_df)

st.plotly_chart(fig, use_container_width=True)



st.subheader("Sankey Diagram")

sankey_fig = create_sankey(filtered_df)

st.plotly_chart(sankey_fig, use_container_width=True)



st.subheader("Geographical Map")

map_fig = create_geographical_map(filtered_df)

st.plotly_chart(map_fig, use_container_width=True)



# GRAPH 4 - VIOLIN PLOT
st.subheader("Violin Plot")

fig = create_violin_plot(filtered_df)
st.plotly_chart(fig, use_container_width=True)


# GRAPH 5 - TREEMAP
st.subheader("Treemap")

fig = create_treemap(filtered_df)
st.plotly_chart(fig, use_container_width=True)


# GRAPH 6 - PARALLEL COORDINATES
st.subheader("Parallel Coordinates")

fig = create_parallel_coordinates(filtered_df)
st.plotly_chart(fig, use_container_width=True)


# GRAPH 7 - SCATTER PLOT
st.subheader("Scatter Plot")

if filtered_df.empty:
    st.info("No movies match the selected filters.")
else:
    components.html(create_scatter_html(filtered_df), height=800, scrolling=True)


# GRAPH 8 - SUNBURST
st.subheader("Sunburst")

if filtered_df.empty:
    st.info("No movies match the selected filters.")
else:
    components.html(create_dashboard(filtered_df), height=900, scrolling=True)


# GRAPH 9 - NETWORK DIAGRAM
st.subheader("Network Diagram")

if filtered_df.empty:
    st.info("No movies match the selected filters.")
else:
    network_html = create_network_html(filtered_df)

    components.html(
        network_html,
        height=1050,
        scrolling=True
    )