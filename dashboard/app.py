import streamlit as st
import duckdb
import os
import plotly.express as px

# initialize connection for fetching of data
conn = duckdb.connect(
    f"md:funds_transfer_db?motherduck_token={os.getenv('motherduck_token')}"
)

st.set_page_config(layout="wide", page_title='Fund Transfers Metrics')
st.title('Fund Transfer Metrics')

# kpi variables
total_transfers = conn.execute('SELECT COUNT(*) FROM transfers').fetchone()[0]
transfer_volume = str(round(conn.execute('SELECT SUM(amount) FROM transfers').fetchone()[0] / 1000000, 1)) + 'M'
fees_collected = str(round(conn.execute('SELECT SUM(fee) FROM transfers').fetchone()[0] / 1000, 1)) + 'K'
avg_transfer = str(round(conn.execute('SELECT AVG(amount) FROM transfers').fetchone()[0] / 1000, 1)) + 'K'


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Transfers", value=total_transfers)
with col2:
    st.metric(label="Transfer Volume", value=f"₱{transfer_volume}")
with col3:
    st.metric(label="Fees Collected", value=f"₱{fees_collected}")
with col4:
    st.metric(label="Average Transfer", value=f"₱{avg_transfer}")
st.divider()

col1, col2 = st.columns([2.25, 1.75], gap='large')

with col1:
    st.subheader('Daily Transaction Trends')

    sub_col1, sub_col2 = st.columns([0.35, 1.2]) # dropdown width

    with sub_col1:
    
        metric = st.selectbox(
            'Metric',
            ['Number of Transactions', 'Transfer Volume', 'Fees Collected'],
            label_visibility='collapsed'
        )

    if metric == 'Number of Transactions':
        query = """
            SELECT
                DATE_TRUNC('day', "timestamp") AS date,
                COUNT(*) AS value
            FROM transfers
            GROUP BY DATE_TRUNC('day', "timestamp")
            ORDER BY date
        """
        y_label = 'Number of Transactions'

    elif metric == 'Transfer Volume':
        query = """
            SELECT
                DATE_TRUNC('day', "timestamp") AS date,
                SUM(amount) AS value
            FROM transfers
            GROUP BY DATE_TRUNC('day', "timestamp")
            ORDER BY date
        """
        y_label = 'Transfer Volume (PHP)'

    else:
        query = """
            SELECT
                DATE_TRUNC('day', "timestamp") AS date,
                SUM(fee) AS value
            FROM transfers
            GROUP BY DATE_TRUNC('day', "timestamp")
            ORDER BY date
        """
        y_label = 'Fees Collected (PHP)'

    metric_over_time = conn.execute(query).fetchdf()

    fig_line = px.line(
        metric_over_time,
        x='date',
        y='value',
        labels={'date': 'Date', 'value': y_label}
    )

    fig_line.update_traces(
        line=dict(color="#6366F1", width=4)
    )

    fig_line.update_xaxes(
        tickformat="%b %d",
        dtick=86400000 * 7,
        showgrid=False,
        tickfont=dict(
            size=14,
            color="#64748B" 
        ),
        title_font=dict(
            size=15,
            color="#A2AEC0"
        )
    )

    fig_line.update_yaxes(
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.075)',
        tickfont=dict(
        size=14,
        color="#8392BD"
        ),
        title_font=dict(
            size=15,
            color="#FFFFFF"
        )
    )

    fig_line.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=360
    )

    st.plotly_chart(fig_line, use_container_width=True)

    # pie chart
    with col2:
        transfers_by_channel = conn.execute("""
        SELECT channel, COUNT(*) as transfer_count FROM transfers GROUP BY channel
        """).fetchdf()

        st.subheader('Payment Channel Share')
        color_map = {
        "card": "#49E99E",
        "instapay": "#38BDF8",
        "pesonet": "#6366F1",
        "qr_ph": "#334155"
        }

        fig = px.pie(
            transfers_by_channel,
            names='channel',
            values='transfer_count',
            hole=0.4,
            color='channel',
            color_discrete_map=color_map
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent',
            insidetextfont=dict(
                size=16,
                color="#F9F9FB"
            ),
            marker=dict(
                line=dict(color='#0E1117', width=3)
            )
        )

        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(
                    size=15
                )
            ),
            margin=dict(l=20, r=20, t=20, b=40),
            height=360
        )
        st.plotly_chart(fig, use_container_width=True)


st.divider()

# second section
col1, col2, col3 = st.columns(3, gap='large')

with col1:
    avg_amount_by_channel = conn.execute("""
        SELECT channel, AVG(amount) as avg_amount_per_channel 
        FROM transfers 
        GROUP BY channel
    """).fetchdf()

    st.subheader('Average Transaction Value (ATV)')

    color_map = {
    "card": "#49E99E",
    "instapay": "#38BDF8",
    "pesonet": "#6366F1",
    "qr_ph": "#334155"
    }

    fig_bar = px.bar(
        avg_amount_by_channel,
        x='channel',
        y='avg_amount_per_channel',
        color='channel',
        color_discrete_map=color_map,
        labels={'channel': 'Channel', 'avg_amount_per_channel': 'Average Amount (PHP)'}
    )

    fig_bar.update_traces(
        marker=dict(line=dict(color='#0E1117', width=1.5)),
        hovertemplate='<b>%{x}</b><br>Avg Amount: ₱%{y:,.2f}<extra></extra>'
    )

    fig_bar.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=280,
        margin=dict(l=0, r=0, t=10, b=10)
    )

    fig_bar.update_yaxes(
        tickprefix="₱",
        tickformat="~s",
        gridcolor="rgba(0, 0, 0, 0.06)"
    )

    fig_bar.update_xaxes(
        showgrid=False
    )

    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    transfers_by_dow = conn.execute("""
        SELECT 
            DAYNAME("timestamp") AS Day,
            DAYOFWEEK("timestamp") AS day_num,
            COUNT(*) AS Transactions
        FROM transfers
        WHERE "timestamp" >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
        GROUP BY Day, day_num
        ORDER BY day_num
    """).fetchdf()

    transfers_by_dow = transfers_by_dow.set_index('Day')

    st.subheader("Traffic by Day")
    st.caption('Last 7 Days')
    st.table(transfers_by_dow[['Transactions']])
    st.markdown("""
        <style>
        /* Add a subtle outline to the dataframe/table container */
        div[data-testid="stTable"], div[data-testid="stDataFrame"] {
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
            overflow: hidden;
        }
        </style>
        """, unsafe_allow_html=True)

with col3:
    st.subheader("Peak Activity by Hour")
    st.caption("24-Hour Distribution")

    hourly_activity = conn.execute("""
        SELECT 
            HOUR("timestamp") AS hour_of_day,
            COUNT(*) AS transfer_count
        FROM transfers
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """).fetchdf()

    fig_hourly = px.bar(
        hourly_activity,
        x='hour_of_day',
        y='transfer_count',
        labels={'hour_of_day': 'Hour (24h)', 'transfer_count': 'Transfers'}
    )
    fig_hourly.update_traces(marker_color="#6366F1")
    fig_hourly.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=280,
        margin=dict(l=0, r=0, t=10, b=10)
    )
    fig_hourly.update_yaxes(gridcolor="rgba(0,0,0,0.06)")
    st.plotly_chart(fig_hourly, use_container_width=True)