# 🎬 TMDB 5000 Movie Dashboard

An interactive data visualization dashboard developed using **Python, Streamlit, and Plotly** to explore movie trends, financial performance, audience ratings, and genre relationships.

## Dataset

This project uses the **TMDB 5000 Movie Dataset**, originally sourced from The Movie Database (TMDB) and available on Kaggle.

**Dataset source:** https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata

The cleaned dataset contains 4,803 movies and 35 columns, including movie titles, genres, release dates, production countries, languages, budgets, revenues, popularity, and audience ratings.

The cleaned data is included in this repository as `tmdb_cleaned.csv`.

## Project Objectives

The main goal is to develop an interactive dashboard that helps users explore movie release trends, genre distributions, audience ratings, geographical production patterns, and financial performance.

## Visualizations

The dashboard contains nine interactive visualizations:

| # | Visualization | Purpose |
|---|---|---|
| 1 | Calendar Heatmap | Analyze movie release patterns by month and day |
| 2 | Sankey Diagram | Explore relationships between languages, genres, and ratings |
| 3 | Geographical Map | Visualize movie production across countries |
| 4 | Violin Plot | Compare audience rating distributions across genres |
| 5 | Treemap | Examine box-office revenue distribution by genre |
| 6 | Parallel Coordinates | Compare multiple movie performance variables |
| 7 | Scatter Plot | Analyze the relationship between budgets and revenues |
| 8 | Sunburst Chart | Explore movie eras, genres, and ratings |
| 9 | Network Diagram | Identify connections between frequently combined genres |

## Technologies Used

- Python
- Streamlit
- Pandas and NumPy
- Plotly
- NetworkX
- SciPy
- PyCountry

## Project Structure

```text
TMDBMovieDashboard/
├── app.py
├── person1.py
├── person2.py
├── scatter_plot.py
├── sunburst.py
├── network_diagram.py
├── tmdb_cleaned.csv
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── README.md
```

## Installation and Usage

**1. Clone the repository**

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
```

Replace the example URL with the actual repository URL.

**2. Install the required dependencies**

```bash
python -m pip install -r requirements.txt
```

**3. Run the Streamlit application**

```bash
python -m streamlit run app.py
```

**4. Open the dashboard**

The application should open automatically in your browser. Otherwise, visit:

http://localhost:8501

## Interactive Features

The dashboard provides three main filters:

- **Movie Genres:** Select one or multiple genres, or leave the selection empty to include all genres.
- **Release Year Range:** Display movies released within the selected years.
- **Minimum Audience Rating:** Exclude movies below the selected rating.

The dashboard also supports interactive chart controls, including hover information, zooming, and chart-specific interactions.

## Key Findings

The analysis highlights several patterns:

- September has the highest number of movie releases (588).
- The United States is the most common production country (3,956 movies).
- The 2000s contain the largest number of movies (2,048).
- Higher production budgets do not always guarantee stronger financial performance.
- Drama–Romance (603 movies), Comedy–Drama (576 movies), and Drama–Thriller (554 movies) are among the strongest genre connections.

These findings reflect the available dataset and may change when dashboard filters are applied.

## Team Members and Contributions

### Faruk Semih Korkut — Data Preprocessing and Visualization

**Visualizations developed:**
- Violin Plot
- Treemap
- Parallel Coordinates Plot

**Additional responsibilities:**
- Cleaned and prepared the movie dataset.
- Created the `tmdb_cleaned.csv` file.
- Implemented interactive features for his three visualizations.
- Analyzed and explained the findings from his charts.

### Enver Topçu — Dashboard Development and Visualization

**Visualizations developed:**
- Calendar Heatmap
- Sankey Diagram
- Geographical Map

**Additional responsibilities:**
- Developed the main Streamlit dashboard.
- Integrated the visualizations into the application.
- Implemented at least three interactive dashboard filters.
- Analyzed and explained the findings from his charts.

### Işık Gündüz — Visualization, Documentation and GitHub

**Visualizations developed:**
- Scatter Plot
- Sunburst Chart
- Network Diagram

**Additional responsibilities:**
- Developed interactive features for her three visualizations.
- Prepared and organized the GitHub repository.
- Wrote and organized the `README.md` documentation.
- Combined and prepared the English project report.
- Analyzed and explained the findings from her charts.

### Shared Responsibilities

All team members were responsible for developing their assigned visualizations in Python, implementing interactions, interpreting their results in English, and presenting their own contributions during the project presentation.

## Project Information

**Course:** Data Visualization

**Project Type:** Group Project

**Dataset:** TMDB 5000 Movie Dataset

**Dashboard Framework:** Streamlit

## Notes

This project was developed for educational purposes. Its findings are based on the available dataset and are intended for exploratory analysis.