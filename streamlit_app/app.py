import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FIFA World Cup Matches Dashboard", layout="wide")

# ---------------- Load Data ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("fifa_wc_matches_clean.csv")
    df['match_date'] = pd.to_datetime(df['match_date'])
    return df

df = load_data()

# ---------------- Sidebar ----------------
st.sidebar.title("About this Dataset")
st.sidebar.write(
    "This dashboard explores FIFA Men's World Cup matches from **1970 to 2022** "
    "(1,322 team-match records). It covers match results, team stats, and "
    "pre-match form, and answers a few key questions about what predicts winning."
)
st.sidebar.markdown(
    "**Source:** [Kaggle — FIFA Men's World Cup Dataset (1970-2022)]"
    "(https://www.kaggle.com/datasets/isfakiqbalchowdhuruy/fifa-mens-world-cup-dataset-1970-2022)"
)

st.sidebar.header("Filters")

year_range = st.sidebar.slider(
    "Select tournament year range",
    int(df['year'].min()), int(df['year'].max()),
    (int(df['year'].min()), int(df['year'].max()))
)

stages = sorted(df['stage_name'].unique())
selected_stages = st.sidebar.multiselect("Select stage(s)", stages, default=stages)

outcome_filter = st.sidebar.selectbox("Filter by outcome", ["All", "Win", "Draw", "Loss"])

host_filter = st.sidebar.radio("Host status", ["All", "Host only", "Non-host only"])

# ---------------- Apply Filters ----------------
filtered = df[
    (df['year'] >= year_range[0]) & (df['year'] <= year_range[1]) &
    (df['stage_name'].isin(selected_stages))
]

if outcome_filter != "All":
    filtered = filtered[filtered['outcome'] == outcome_filter]

if host_filter == "Host only":
    filtered = filtered[filtered['is_host'] == 1]
elif host_filter == "Non-host only":
    filtered = filtered[filtered['is_host'] == 0]

# ---------------- Main Page ----------------
st.title("⚽ FIFA World Cup Matches Dashboard (1970-2022)")
st.write(
    "Explore team-level match data from every FIFA Men's World Cup between 1970 and 2022. "
    "Use the sidebar filters to narrow down by year, stage, outcome, or host status."
)

st.subheader("Data Preview")
st.dataframe(filtered.head(20))

st.subheader("Summary Statistics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Matches shown", f"{len(filtered):,}")
col2.metric("Avg goals for", round(filtered['goals_for'].mean(), 2) if len(filtered) else "-")
col3.metric("Win rate", f"{(filtered['outcome']=='Win').mean()*100:.1f}%" if len(filtered) else "-")
col4.metric("Avg yellow cards", round(filtered['yellow_cards'].mean(), 2) if len(filtered) else "-")

st.dataframe(filtered[['goals_for', 'goals_against', 'yellow_cards', 'red_cards', 'team_prior_win_rate']].describe())

# ---------------- Visualizations ----------------
st.subheader("Interactive Visualizations")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Goals Distribution", "Host vs Non-Host", "Shots vs Goals", "Cards by Stage"]
)

with tab1:
    fig = px.histogram(filtered, x="goals_for", nbins=10,
                        title="Distribution of Goals Scored per Match")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    host_outcome = (
        filtered.groupby('is_host')['outcome']
        .apply(lambda x: (x == 'Win').mean())
        .reset_index()
    )
    host_outcome['is_host'] = host_outcome['is_host'].map({0: 'Non-Host', 1: 'Host'})
    fig = px.bar(host_outcome, x='is_host', y='outcome',
                 labels={'outcome': 'Win Rate', 'is_host': ''},
                 title="Win Rate: Host Nation vs Non-Host", color='is_host')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    modern = filtered[filtered['possession'].notnull()]
    if len(modern) > 0:
        fig = px.scatter(modern, x='shots_on_target', y='goals_for',
                          title="Shots on Target vs Goals Scored (2002-2022 only)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No matches with detailed shot stats in the current filter (data only available from 2002 onward).")

with tab4:
    cards_by_stage = (
        filtered.groupby('stage_name')[['yellow_cards', 'red_cards']]
        .mean().reset_index().sort_values('yellow_cards')
    )
    fig = px.bar(cards_by_stage, x='stage_name', y='yellow_cards',
                 title="Average Yellow Cards by Stage")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Insights ----------------
st.subheader("Key Insights")
st.markdown("""
- **Hosting helps:** host nations won about **60%** of their matches vs about **39%** for non-hosts.
- **Form matters, a bit:** winning teams had a higher average prior win rate (0.41) than losing teams (0.30).
- **Knockout matches are slightly more physical:** average yellow cards rise from the group stage to the final.
- **Shots on target beat possession:** shots on target correlate with goals (r ≈ 0.54) far more than possession does (r ≈ 0.11).
""")

st.caption("Built with Streamlit • Data: FIFA Men's World Cup Dataset (1970-2022), Kaggle")
