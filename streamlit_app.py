# example/st_app.py

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

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
    data['snapDate_str'] = pd.to_datetime(data['snapDate']).dt.strftime('%Y-%m-%d')


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

    st.subheader("⛔ Disappear Bundles")

    st.space()

    Cols_Left2,Cols_Right2 = st.columns([3,1])


    with  Cols_Left2:


        Diappear_Bundles = data[data['Image Url'].isna()]
        Display_disappear_Bundles = Diappear_Bundles[['rank','Id', 'name', 'creatorName', 'Image Url', 'snapDate','Created','creatorType','creatorHasVerifiedBadge','favoriteCount','link']].copy()

        
        
        event1 = st.dataframe(Display_disappear_Bundles, 
                width=800,
                height=400,
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

    with Cols_Right2:
        if len(event1.selection.rows) > 0:
            selected_row_index1 = event1.selection.rows[0]
            selected_data1 = Diappear_Bundles.iloc[selected_row_index1]
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
            
                img = selected_data1.get('Image Url')
                if pd.notna(img) and str(img).strip() != '':
                    st.image(img, width=400)
                else:
                    st.write("No image available")

            
            with st.container(border=True): 
                    
                    # Title with clickable arrow to the selected item's link (opens in new tab) — inline
                    link = selected_data1.get('link', '')
                    if pd.notna(link) and str(link).strip() != '':
                        st.markdown(
                            f"""<div style='display:inline-flex; align-items:center; gap:8px;'>
                                <span style='font-size:1.8rem; font-weight:600; margin:0;'>{selected_data1['name']}</span>
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
                        rank_val = "N/A" if pd.isna(selected_data1['rank']) else int(float(selected_data1['rank']))
                    except Exception:
                        rank_val = selected_data1['rank']
                    st.write(f"**Rank:** <span style='color:#5496ff'>{rank_val}</span>", unsafe_allow_html=True)
                    st.write(f"**Asset ID:** `{selected_data1['Id']}`")
                    # Creator with verified tick and creator type label (handle bool/numeric/string truthy values)
                    try:
                        creator_name = selected_data1['creatorName'] if pd.notna(selected_data1['creatorName']) else "N/A"
                    except Exception:
                        creator_name = selected_data1.get('creatorName', 'N/A')
                    raw_verified = selected_data1.get('creatorHasVerifiedBadge', None)
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
                    creator_type = selected_data1.get('creatorType', '')
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
                    fav_raw = selected_data1.get('favoriteCount', None)
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
                    st.write(f"**Created:** {selected_data1['Created'].strftime('%d %b %Y')} ({int((today - selected_data1['Created']).days)} days old)")
                    st.write(f"**SnapDate:** {selected_data1['snapDate']}")
                    

        else:
            st.info("Click a row in the table to see more details here.")    

    st.space()
    st.divider()

elif page == "Data Analysis":

    
    st.set_page_config(
        layout="wide",
        page_title="R-2284_Dash",
        page_icon=":bar_chart:",

    )

    st.title("Data Analysis")
    st.write("This is the Data Analysis page.")

    conn = st.connection("gsheets", type=GSheetsConnection)

    data = conn.read(worksheet="Testing DATA.1")

    data['Created'] = pd.to_datetime(data['Created'], errors='coerce')
    data['snapDate_str'] = pd.to_datetime(data['snapDate']).dt.strftime('%Y-%m-%d')





    



    
              



