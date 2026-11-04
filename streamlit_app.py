import sys

if 'httpx2' in sys.modules:
    del sys.modules['httpx2']
sys.modules['httpx2'] = sys.modules.get('httpx', __import__('httpx'))

import streamlit as st
import json
import re
import pandas as pd
import plotly.express as px
from agent import agent_executor

st.title("My AI Data Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 1. שחזור ההיסטוריה - כולל ציור הגרפים שנשמרו
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "viz" in message and "chart_data" in message:
            viz = message["viz"]
            chart_data = message["chart_data"]
            if viz and chart_data:
                df = pd.DataFrame(chart_data)
                if not df.empty and 'x_col' in df.columns and 'y_col' in df.columns:
                    chart_type = viz.get("type", "bar")
                    title = viz.get("title", "Chart")
                    if chart_type == "pie":
                        st.plotly_chart(px.pie(df, names='x_col', values='y_col', title=title), use_container_width=True)
                    elif chart_type == "line":
                        st.plotly_chart(px.line(df, x='x_col', y='y_col', title=title, markers=True), use_container_width=True)
                    elif chart_type == "bar":
                        st.plotly_chart(px.bar(df, x='x_col', y='y_col', title=title), use_container_width=True)

if prompt := st.chat_input("what would you like to ask?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                formatted_messages = [(m["role"], m["content"]) for m in st.session_state.messages]

                response = agent_executor.invoke(
                    {"messages": formatted_messages},
                    config={"recursion_limit": 60}
                )
                
                ai_message = response["messages"][-1].content
                json_match = re.search(r'\{.*\}', ai_message, re.DOTALL)
                
                if json_match:
                    data_dict = json.loads(json_match.group(0))
                    
                    # 2. שולפים את הנתונים הנכונים מתוך ה-JSON של הסוכן
                    clean_answer = data_dict.get("answer") 
                    viz = data_dict.get("visualization")
                    chart_data = data_dict.get("data")
                    
                    # 3. בונים את "קופסת" ההודעה החדשה
                    full_message = {"role": "assistant"}
                    
                    # מטפלים בטקסט
                    if clean_answer:
                        st.markdown(clean_answer)
                        full_message["content"] = clean_answer
                    else:
                        fallback = ai_message.split('{')[0] if '{' in ai_message else ai_message
                        st.markdown(fallback)
                        full_message["content"] = fallback
                    
                    # מטפלים בגרף
                    if viz and chart_data:
                        full_message["viz"] = viz
                        full_message["chart_data"] = chart_data
                        
                        df = pd.DataFrame(chart_data)
                        if not df.empty and 'x_col' in df.columns and 'y_col' in df.columns:
                            chart_type = viz.get("type", "bar")
                            title = viz.get("title", "Chart")
                            
                            if chart_type == "pie":
                                fig = px.pie(df, names='x_col', values='y_col', title=title)
                                st.plotly_chart(fig, use_container_width=True)
                            elif chart_type == "line":
                                fig = px.line(df, x='x_col', y='y_col', title=title, markers=True)
                                st.plotly_chart(fig, use_container_width=True)
                            elif chart_type == "bar":
                                fig = px.bar(df, x='x_col', y='y_col', title=title)
                                st.plotly_chart(fig, use_container_width=True)
                                
                    # 4. שומרים את ההודעה המלאה בזיכרון
                    st.session_state.messages.append(full_message)

                else:
                    st.markdown(ai_message)
                    st.session_state.messages.append({"role": "assistant", "content": ai_message})
                    
            except Exception as e:
                st.error(f"Error: {e}")