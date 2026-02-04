# example/st_app.py

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Data Analysis", "Settings"])

if page == "Home":

    st.set_page_config(
        layout="wide",
        page_title="R-2284_Dash",
        page_icon=":bar_chart:",

    )

    st.title("Welcome, X3sw")

    st.space()

    conn = st.connection("gsheets", type=GSheetsConnection)

    data = conn.read(worksheet="Testing DATA.1")

    data['Created'] = pd.to_datetime(data['Created'], errors='coerce')
    # Ensure snapDate is a proper datetime object immediately
    data['snapDate'] = pd.to_datetime(data['snapDate'], errors='coerce')

    # Create a separate column JUST for the dropdown text
    data['snapDate_str'] = data['snapDate'].dt.strftime('%Y-%m-%d')


    st.subheader("⚙️ Controls")

    Cols_UPLeft,Cols_UPRight = st.columns(2)


    with Cols_UPLeft:
        
            # 1. Sorting Dropdown
        sort_option = st.selectbox(
                "Sort By:",
                options=["Newest First", "Oldest First"]
            )

            # 2. Applying the Sort
        if sort_option == "Newest First":
                # Make sure your date column is actually a datetime object
                data['Created'] = pd.to_datetime(data['Created'])
                data = data.sort_values(by="Created",ascending=False)
        elif sort_option == "Oldest First":
                data = data.sort_values(by="Created", ascending=True)

    with Cols_UPRight:
        


        available_dates = sorted(data['snapDate_str'].unique(), reverse=True)
        options = ["Show All"] + available_dates    
            
        selected_date = st.selectbox("Choose Snapshot:",options=options)
        # --- Apply the Filter to the Main Data ---
        if selected_date != "Show All":
            # Filter the dataframe to match only the selected date

            filtered_data = data[data['snapDate_str'] == selected_date]

        else:

            filtered_data = data




    Cols_Left,Cols_Right = st.columns([3,1])

    with Cols_Left:
        display_df = filtered_data[['rank','Id', 'name', 'creatorName', 'Image Url', 'snapDate','Created','creatorType','creatorHasVerifiedBadge','favoriteCount','link']].copy()
        # Create the selection-enabled dataframe

        

        event = st.dataframe(
            display_df, 
            width=600,
            height=750,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",  # This ensures the app updates the right column immediately
            selection_mode="single-row",
            column_config={
                "Id": st.column_config.NumberColumn("ID",format="%d"),
                "Id": None,
                "Image Url": None,
                "snapDate": None,
                "creatorType": None,
                "creatorHasVerifiedBadge": None,
                "favoriteCount": None,
                "link": None,
                "rank": st.column_config.Column("Rank", width="200"),
                "Created": st.column_config.DateColumn("Created Date", format="DD MMM YYYY")
            }
        )

    with Cols_Right:
        if len(event.selection.rows) > 0:
            selected_row_index = event.selection.rows[0]
            selected_data = filtered_data.iloc[selected_row_index]
            data['Id'] = pd.to_numeric(data['Id'], errors='coerce').astype('Int64')
            today = datetime.now()

            # 3. Calculate the difference in days
            # .dt.days gives us just the integer (e.g., 5) instead of "5 days 00:00:00"
            days_diff = (today - data['Created']).dt.days

            # 4. Create the formatted string: "01 Jan 2024 (5 days old)"
            # We use a lambda to handle singular/plural and formatting
            data['Created_Display'] = data.apply(
                lambda x: f"{x['Created'].strftime('%d %b %Y')} ({int((today - x['Created']).days)} days old)" 
                if pd.notnull(x['Created']) else "N/A", 
                axis=1
                )

            with st.container(border=True):
            
                img = selected_data.get('Image Url')
                if pd.notna(img) and str(img).strip() != '':
                    st.image(img, width=400)
                else:
                    st.write("No image available")

            
            with st.container(border=True): 
                    
                    # Title with clickable arrow to the selected item's link (opens in new tab) — inline
                    link = selected_data.get('link', '')
                    if pd.notna(link) and str(link).strip() != '':
                        st.markdown(
                            f"""<div style='display:inline-flex; align-items:center; gap:8px;'>
                                <span style='font-size:1.8rem; font-weight:600; margin:0;'>{selected_data['name']}</span>
                                <a href='{str(link)}' target='_blank' rel='noopener noreferrer' style='text-decoration:none; display:inline-flex; align-items:center;'>
                                    <svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' aria-hidden='true'>
                                        <path d='M5 12h14M13 5l7 7-7 7' stroke='#5496ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/>
                                    </svg>
                                </a>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        # show title inline but without link
                        st.markdown(f"<span style='font-size:1.25rem; font-weight:600'>{selected_data['name']}</span>", unsafe_allow_html=True)

                    st.space(1)
                    # Format rank as integer (no decimal) and show N/A when missing
                    try:
                        rank_val = "N/A" if pd.isna(selected_data['rank']) else int(float(selected_data['rank']))
                    except Exception:
                        rank_val = selected_data['rank']
                    st.write(f"**Rank:** <span style='color:#5496ff'>{rank_val}</span>", unsafe_allow_html=True)
                    st.write(f"**Asset ID:** `{selected_data['Id']}`")
                    # Creator with verified tick and creator type label (handle bool/numeric/string truthy values)
                    try:
                        creator_name = selected_data['creatorName'] if pd.notna(selected_data['creatorName']) else "N/A"
                    except Exception:
                        creator_name = selected_data.get('creatorName', 'N/A')
                    raw_verified = selected_data.get('creatorHasVerifiedBadge', None)
                    verified = False
                    if pd.notna(raw_verified):
                        if isinstance(raw_verified, bool):
                            verified = bool(raw_verified)
                        else:
                            try:
                                # numeric values like 1 or 1.0
                                num = float(raw_verified)
                                verified = num != 0
                            except Exception:
                                s = str(raw_verified).strip().lower()
                                verified = s in ('true', '1', '1.0', 'yes', 'y', 't')
                    creator_type = selected_data.get('creatorType', '')
                    creator_type_label = f" <span style='color:#9b9b9b'>({str(creator_type).capitalize()})</span>" if pd.notna(creator_type) and creator_type != '' else ""
                    # Use Roblox official verified tick image when verified
                    verified_badge = ""
                    if verified:
                        verified_badge = (
                            "<img src='https://en.help.roblox.com/hc/article_attachments/41933934939156' "
                            "style='width:18px;height:18px;display:inline-block;vertical-align:middle;margin-left:6px;border-radius:2px;' "
                            "alt='verified' title='Verified'>"
                        )
                    st.write(f"**Creator:** <span style='color:#70cbff'>{creator_name}</span>{verified_badge}{creator_type_label}", unsafe_allow_html=True)
                    # Compact format for favorites (e.g., 39895 -> 40k)
                    fav_raw = selected_data.get('favoriteCount', None)
                    if pd.notna(fav_raw):
                        try:
                            fav_num = float(fav_raw)
                            if fav_num >= 1_000_000:
                                fav_display = f"{int(round(fav_num / 1_000_000))}M"
                            elif fav_num >= 1_000:
                                fav_display = f"{int(round(fav_num / 1_000))}k"
                            else:
                                fav_display = str(int(fav_num))
                        except Exception:
                            fav_display = str(fav_raw)
                    else:
                        fav_display = "N/A"
                    st.write(f"**Favorites:** <span style='color:#ffe373'>{fav_display}</span>", unsafe_allow_html=True)
                    st.write(f"**Created:** {selected_data['Created'].strftime('%d %b %Y')} ({int((today - selected_data['Created']).days)} days old)")
                    st.write(f"**SnapDate:** {selected_data['snapDate']}")
                    

        else:
            st.info("Click a row in the table to see more details here.")    

                
    st.space()
    st.divider()
    
    

    st.subheader("⛔ Disappear Bundles (Range Comparison)")
    st.markdown("Find items that existed in the **First Range** but are completely missing from the **Second Range**.")

    # --- 1. Date Range Selection UI ---
    # Get min/max dates for defaults
    min_dt = data['snapDate'].min().to_pydatetime()
    max_dt = data['snapDate'].max().to_pydatetime()

    here_start_default = max(min_dt, max_dt - timedelta(days=7))
    gone_start_default = max(min_dt, max_dt - timedelta(days=6))

    d_col1, d_col2 = st.columns(2)

    with d_col1:
        here_dates = st.date_input(
            "Was Here (Range)",
            # Safety: ensure start <= end by using [start, end] logic
            value=(here_start_default, max_dt), 
            min_value=min_dt,
            max_value=max_dt,
            format="DD/MM/YYYY"
    )

    with d_col2:
        gone_dates = st.date_input(
            "Is Gone (Range)",
            value=(gone_start_default, max_dt),
            min_value=min_dt,
            max_value=max_dt,
            format="DD/MM/YYYY"
        )

        # Validating that we have ranges (start and end) for both
    if isinstance(here_dates, tuple) and len(here_dates) == 2 and isinstance(gone_dates, tuple) and len(gone_dates) == 2:
        # --- ADD THESE 4 CONVERSION LINES ---
        start_here = pd.to_datetime(here_dates[0])
        end_here = pd.to_datetime(here_dates[1])
        start_gone = pd.to_datetime(gone_dates[0])
        end_gone = pd.to_datetime(gone_dates[1])

        # --- 2. The Filtering Logic ---
        # Now these comparisons will work perfectly
        mask_gone = (data['snapDate'] >= start_gone) & (data['snapDate'] <= end_gone)
        ids_in_gone_range = data.loc[mask_gone, 'Id'].unique()
        
        mask_here = (data['snapDate'] >= start_here) & (data['snapDate'] <= end_here)
        bundles_in_here_range = data.loc[mask_here].copy()

        # C. Filter: Keep rows from "Here" where ID is NOT in "Gone"
        # We use ~ (not) and .isin()
        disappeared_candidates = bundles_in_here_range[~bundles_in_here_range['Id'].isin(ids_in_gone_range)]

        # D. Deduplicate: A bundle might appear multiple times in the "Here" range.
        # We want to show the LATEST appearance before it disappeared.
        # Sort by date descending so the first occurrence is the latest one
        disappeared_candidates = disappeared_candidates.sort_values(by='snapDate', ascending=False)
        Diappear_Bundles = disappeared_candidates.drop_duplicates(subset=['Id'], keep='first')

        st.caption(f"Comparing **{start_here} to {end_here}** against **{start_gone} to {end_gone}**")
        st.space()

        # --- 3. The Layout (Left: Table, Right: Detail Card) ---
        Cols_Left2, Cols_Right2 = st.columns([3, 1])

        with Cols_Left2:
            if not Diappear_Bundles.empty:
                Display_disappear_Bundles = Diappear_Bundles[[
                    'rank','Id', 'name', 'creatorName', 'Image Url', 
                    'snapDate','Created','creatorType',
                    'creatorHasVerifiedBadge','favoriteCount','link'
                ]].copy()
                
                event1 = st.dataframe(
                    Display_disappear_Bundles, 
                    width=800,
                    height=780, 
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun", 
                    selection_mode="single-row",
                    column_config={
                        "Id": st.column_config.NumberColumn("ID", format="%d"),
                        "Image Url": None, 
                        "snapDate": st.column_config.DateColumn("Last Seen", format="DD MMM YYYY"), # Renamed for clarity
                        "creatorType": None,
                        "creatorHasVerifiedBadge": None,
                        "favoriteCount": None,
                        "link": None,
                        "rank": st.column_config.Column("Rank", width="small"),
                        "Created": st.column_config.DateColumn("Created Date", format="DD MMM YYYY")
                    }
                )
            else:
                st.success("No disappeared bundles found with these specific ranges.")
                event1 = None 

        with Cols_Right2:
            # Check if event1 exists and has a selection
            if event1 and len(event1.selection.rows) > 0:
                selected_row_index1 = event1.selection.rows[0]
                selected_data1 = Display_disappear_Bundles.iloc[selected_row_index1]
                today = datetime.now()

                # --- Detail View Logic (Same as before) ---
                with st.container(border=True):
                    img = selected_data1.get('Image Url')
                    if pd.notna(img) and str(img).strip() != '':
                        st.image(img, use_container_width=True)
                    else:
                        st.write("No image available")

                with st.container(border=True): 
                    link = selected_data1.get('link', '')
                    if pd.notna(link) and str(link).strip() != '':
                        st.markdown(
                            f"""<div style='display:inline-flex; align-items:center; gap:8px;'>
                                <span style='font-size:1.8rem; font-weight:600; margin:0; line-height:1.2;'>{selected_data1['name']}</span>
                                <a href='{str(link)}' target='_blank' rel='noopener noreferrer' style='text-decoration:none; display:inline-flex; align-items:center;'>
                                    <svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' aria-hidden='true'>
                                        <path d='M5 12h14M13 5l7 7-7 7' stroke='#5496ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/>
                                    </svg>
                                </a>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"<span style='font-size:1.25rem; font-weight:600'>{selected_data1['name']}</span>", unsafe_allow_html=True)

                    st.divider()
                    
                    try:
                        rank_val = "N/A" if pd.isna(selected_data1['rank']) else int(float(selected_data1['rank']))
                    except:
                        rank_val = selected_data1['rank']
                    st.write(f"**Rank:** <span style='color:#5496ff'>{rank_val}</span>", unsafe_allow_html=True)
                    
                    st.write(f"**Asset ID:** `{selected_data1['Id']}`")
                    
                    # Creator
                    creator_name = selected_data1.get('creatorName', 'N/A')
                    if pd.isna(creator_name): creator_name = "N/A"
                    
                    raw_verified = selected_data1.get('creatorHasVerifiedBadge', None)
                    verified = False
                    if pd.notna(raw_verified):
                        s = str(raw_verified).strip().lower()
                        verified = s in ('true', '1', '1.0', 'yes', 'y', 't') or (isinstance(raw_verified, (int, float)) and raw_verified != 0)

                    creator_type = selected_data1.get('creatorType', '')
                    creator_type_label = f" <span style='color:#9b9b9b'>({str(creator_type).capitalize()})</span>" if pd.notna(creator_type) and creator_type != '' else ""

                    verified_badge = ""
                    if verified:
                        verified_badge = "<img src='https://en.help.roblox.com/hc/article_attachments/41933934939156' style='width:18px;height:18px;display:inline-block;vertical-align:middle;margin-left:6px;border-radius:2px;' alt='verified'>"
                    
                    st.write(f"**Creator:** <span style='color:#70cbff'>{creator_name}</span>{verified_badge}{creator_type_label}", unsafe_allow_html=True)

                    # Favorites
                    fav_raw = selected_data1.get('favoriteCount', None)
                    fav_display = "N/A"
                    if pd.notna(fav_raw):
                        try:
                            fav_num = float(fav_raw)
                            if fav_num >= 1_000_000: fav_display = f"{int(round(fav_num / 1_000_000))}M"
                            elif fav_num >= 1_000: fav_display = f"{int(round(fav_num / 1_000))}k"
                            else: fav_display = str(int(fav_num))
                        except:
                            fav_display = str(fav_raw)
                    st.write(f"**Favorites:** <span style='color:#ffe373'>{fav_display}</span>", unsafe_allow_html=True)

                    # Date
                    if pd.notna(selected_data1['Created']):
                        created_dt = pd.to_datetime(selected_data1['Created'])
                        days_old = (today - created_dt).days
                        st.write(f"**Created:** {created_dt.strftime('%d %b %Y')} ({days_old} days old)")
                    else:
                        st.write("**Created:** N/A")
                    
                    # IMPORTANT: Update label to indicate this is the LAST time it was seen
                    st.write(f"**Last Seen:** {selected_data1['snapDate']}")

            else:
                if not Diappear_Bundles.empty:
                    st.info("👈 Select a row to view details")

    else:
        st.info("Please select both a Start and End date for both ranges to begin.")


elif page == "Data Analysis":

    
    st.set_page_config(
        layout="wide",
        page_title="R-2284_Dash",
        page_icon=":bar_chart:",

    )

    conn = st.connection("gsheets", type=GSheetsConnection)

    data = conn.read(worksheet="Testing DATA.1")
    data = conn.read(worksheet="Testing DATA.1")
    # CRITICAL: Convert these immediately
    data['snapDate'] = pd.to_datetime(data['snapDate'], errors='coerce')
    data['Created'] = pd.to_datetime(data['Created'], errors='coerce')
   
   
    # Now that it's a datetime, this line (at 436) will work:
    max_dt = data['snapDate'].max().to_pydatetime()

    st.divider()
    st.subheader("📊 Rank Movement Analytics")

    # --- STEP 1: SAFE DATE CONVERSION ---
    # Ensure snapDate is datetime immediately
    data['snapDate'] = pd.to_datetime(data['snapDate'], errors='coerce')
    valid_dates = data.dropna(subset=['snapDate'])

    # Specify ['snapDate'] so Pandas only looks at the date column
    min_dt = data['snapDate'].dropna().min().to_pydatetime().date()
    max_dt = data['snapDate'].dropna().max().to_pydatetime().date()

    if not valid_dates.empty:
        min_dt = valid_dates['snapDate'].min().to_pydatetime()
        max_dt = valid_dates['snapDate'].max().to_pydatetime()

        # --- STEP 2: PRESETS ---
        preset = st.radio("Range Preset:", ["Today vs Yesterday", "This Week vs Last Week", "Monthly", "Custom"], horizontal=True)

        if preset == "Today vs Yesterday":
            p_val = sorted((max(min_dt, max_dt - timedelta(days=1)), max(min_dt, max_dt - timedelta(days=1))))
            c_val = sorted((max_dt, max_dt))
        elif preset == "This Week vs Last Week":
            p_val = sorted((max(min_dt, max_dt - timedelta(days=14)), max(min_dt, max_dt - timedelta(days=7))))
            c_val = sorted((max(min_dt, max_dt - timedelta(days=6)), max_dt))
        else:
            p_val = sorted((min_dt, max_dt))
            c_val = sorted((min_dt, max_dt))

        # 4. Finally, create the date inputs
        col1, col2 = st.columns(2)
        with col1:
            past_rng = st.date_input("Previous Period", value=p_val, key=f"past_{preset}")
        with col2:
            curr_rng = st.date_input("Current Period", value=c_val, key=f"curr_{preset}")

        # --- STEP 3: DATA PROCESSING ---
        if len(past_rng) == 2 and len(curr_rng) == 2:
            p_start, p_end = pd.to_datetime(past_rng[0]), pd.to_datetime(past_rng[1])
            c_start, c_end = pd.to_datetime(curr_rng[0]), pd.to_datetime(curr_rng[1])

            # Aggregate average rank for both periods
            df_past = data[(data['snapDate'] >= p_start) & (data['snapDate'] <= p_end)].groupby('Id')['rank'].mean()
            df_curr = data[(data['snapDate'] >= c_start) & (data['snapDate'] <= c_end)].groupby('Id')['rank'].mean()

            # Merge and calculate delta
            comparison = pd.merge(df_past, df_curr, on='Id', suffixes=('_past', '_curr')).dropna()
            comparison['rank_diff'] = comparison['rank_past'] - comparison['rank_curr'] # Positive = Climbing
            
            # Bring back the names for the chart
            names = data.drop_duplicates('Id').set_index('Id')[['name']]
            plot_data = comparison.join(names).reset_index()

            # --- STEP 4: PLOTLY BAR CHART (Top Movers) ---
            st.write("### 🚀 Top Movers (Rank Change)")
            
            # Filter for top 15 climbers and top 15 fallers
            top_n = st.slider("Number of bundles to show in bar chart", 5, 50, 15)
            # Then update your filtering line:
            top_climbers = plot_data.sort_values('rank_diff', ascending=False).head(top_n)
            top_fallers = plot_data.sort_values('rank_diff', ascending=True).head(top_n)
            movers = pd.concat([top_climbers, top_fallers])

            fig = px.bar(
                movers,
                x='rank_diff',
                y='name',
                orientation='h',
                color='rank_diff',
                color_continuous_scale='RdYlGn', # Red for negative, Green for positive
                labels={'rank_diff': 'Rank Change (Pos = Climbing)', 'name': 'Bundle Name'},
                custom_data=['Id'],
                hover_data=['rank_past', 'rank_curr'],
                text_auto='.0f'
                )
            
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
            st.plotly_chart(fig, use_container_width=True)

            # --- STEP 5: OVERALL DISTRIBUTION (Scatter Plot) ---
            st.write("### 🌌 Overall Rank Correlation")
                        # 1. Create the scatter plot
            # 1. Create the scatter plot WITHOUT the marginal parameters
            st.write("### 🌌 Overall Rank Correlation")
            fig_scatter = px.scatter(
                plot_data,
                x='rank_past',
                y='rank_curr',
                hover_name='name',
                color='rank_diff',
                color_continuous_scale='RdYlGn',
                labels={'rank_past': 'Previous Rank', 'rank_curr': 'Current Rank'},
                title="Comparison of All Bundles (Items below the diagonal line are Climbing)"
            )
            # Add a diagonal line (Items below this line are improving)
            fig_scatter.add_shape(type="line", x0=0, y0=0, x1=max(plot_data['rank_past']), y1=max(plot_data['rank_past']),
                                line=dict(color="Gray", dash="dash"))
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        else:
            st.error("No valid dates found in data. Please check your 'snapDate' column.")






    



    
              



