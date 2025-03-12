# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 12:13:28 2025

@author: DELL
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import shap
from streamlit.components.v1 import html

# System Configuration
TIME_POINTS = 3
VITAL_SIGNS = [
    ('Heart Rate', 'bpm', (30, 200)),
    ('Systolic BP', 'mmHg', (50, 250)),
    ('Diastolic BP', 'mmHg', (30, 150)),
    ('Mean Arterial Pressure', 'mmHg', (40, 180)),
    ('Respiratory Rate', '/min', (10, 50)),
    ('Temperature', '°C', (34.0, 42.0)),
    ('Oxygen Saturation', '%', (70, 100)),
    ('Blood Glucose', 'mmol/L', (3.0, 25.0))
]

@st.cache_resource
def load_model():
    """加载模型和SHAP解释器"""
    model = joblib.load('model_RandomForest.joblib')
    explainer = shap.TreeExplainer(model)
    return model, explainer

def generate_time_labels():
    now = datetime.now()
    return [
        (now - timedelta(hours=3)).strftime("%H:%M"),
        (now - timedelta(hours=2)).strftime("%H:%M"),
        (now - timedelta(hours=1)).strftime("%H:%M")
    ]

# Page Configuration
st.set_page_config(page_title="Sepsis Risk Analyzer", layout="wide")
st.title('Sepsis Risk Prediction System')

# 自定义CSS样式
st.markdown("""
<style>
.shap-container {
    background: white !important;
    padding: 1rem !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)

# 时间序列输入模块
def time_series_input():
    time_labels = generate_time_labels()
    input_data = {}

    with st.form("time_series_form"):
        st.header("3-Hour Vital Signs Monitoring")
        
        for vs, unit, (min_val, max_val) in VITAL_SIGNS:
            st.subheader(f"{vs} ({unit})")
            cols = st.columns(3)
            
            time_values = []
            for i in range(TIME_POINTS):
                with cols[i]:
                    label = f"{i+1} hour ago ({time_labels[i]})"
                    value = st.number_input(
                        label=label,
                        min_value=min_val,
                        max_value=max_val,
                        value=round((min_val + max_val)/2, 1) if isinstance(min_val, float) else (min_val + max_val)//2,
                        key=f"{vs}_{i+1}h"
                    )
                    time_values.append(value)
            
            input_data[vs] = time_values

        submitted = st.form_submit_button("Analyze Data", type="primary")
    
    return submitted, input_data

# 特征计算
def calculate_features(data_dict):
    features = []
    stats_data = []
    
    for vs, values in data_dict.items():
        mean_val = np.mean(values)
        std_val = np.std(values)
        final_val = values[-1]
        
        stats_data.append({
            'Parameter': vs,
            'Mean': f"{mean_val:.1f}",
            'Std Dev': f"{std_val:.1f}",
            'Current': f"{final_val:.1f}",
            'Trend': "↑" if values[-1] > values[0] else "↓" if values[-1] < values[0] else "→"
        })
        
        features.extend([mean_val, std_val, final_val])
    
    return features, stats_data

# 可视化模块
def visualize_individual_trends(data_dict):
    st.header("Vital Signs Trend Analysis")
    
    time_labels = [f"-{3-i} hours" for i in range(TIME_POINTS)]
    
    for vs, values in data_dict.items():
        with st.expander(f"{vs} Trend"):
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(time_labels, values, marker='o', color='#1f77b4')
            ax.set_title(f"{vs} Trend")
            ax.set_xlabel("Time Points")
            ax.set_ylabel("Value")
            ax.grid(True)
            st.pyplot(fig)

# 主流程
submitted, input_data = time_series_input()

if submitted:
    # 数据验证
    missing_data = [vs for vs, values in input_data.items() if len(values) != TIME_POINTS]
    if missing_data:
        st.error(f"Missing data: {', '.join(missing_data)}")
        st.stop()
        
    # 特征计算
    try:
        features, stats_df = calculate_features(input_data)
        features_names = [f"{vs[0]}_{stat}" for vs in VITAL_SIGNS for stat in ['mean', 'std', 'final']]
        input_df = pd.DataFrame([features], columns=features_names)
    except Exception as e:
        st.error(f"Feature calculation error: {str(e)}")
        st.stop()
    
    # 加载模型
    model, explainer = load_model()
    
    with st.container():
        # 统计显示
        st.header("Analysis Report")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Statistical Summary")
            stats_display = pd.DataFrame(stats_df)
            st.dataframe(stats_display.set_index('Parameter'), 
                        use_container_width=True,
                        column_config={
                            "Trend": st.column_config.TextColumn(
                                help="↑: Increasing, ↓: Decreasing, →: Stable"
                            )
                        })
            
        with col2:
            visualize_individual_trends(input_data)
    
    # 模型预测
    try:
        proba = model.predict_proba(input_df)[0][1]
        risk_color = "#e74c3c" if proba > 0.7 else "#f1c40f" if proba > 0.4 else "#2ecc71"
        
        st.header("Risk Assessment")
        st.markdown(f"""
        <div style="background:{risk_color}20; padding:1.5rem; border-radius:10px">
            <div style="display: flex; justify-content: space-between; align-items: center">
                <div>
                    <h3 style="color:{risk_color}; margin:0">Sepsis Risk Probability: {proba*100:.1f}%</h3>
                    <p style="color:#7f8c8d; margin:0">Assessment Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                <div style="font-size:2rem; color:{risk_color}">
                    {"⚠️" if proba > 0.7 else "⚠️" if proba > 0.4 else "✅"}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 临床建议
        st.subheader("Clinical Actions")
        if proba > 0.7:
            st.error("""
            ​**Immediate Actions**:
            1. Activate sepsis response team
            2. Administer broad-spectrum antibiotics within 30 mins
            3. Obtain blood cultures and lactate levels
            4. Hourly vital signs monitoring
            """)
        elif proba > 0.4:
            st.warning("""
            ​**Urgent Actions**:
            1. Notify attending physician
            2. Perform complete blood count and cultures
            3. Repeat assessment in 2 hours
            4. Consider fluid resuscitation
            """)
        else:
            st.success("""
            ​**Monitoring Protocol**:
            1. Continue current treatment
            2. Reassess in 6 hours
            3. Monitor for infection signs
            """)
            
        # SHAP解释模块
        st.divider()
        st.subheader("Prediction Explanation")
        
        # 计算SHAP值
        shap_values = explainer.shap_values(input_df)
        
        # 双列布局
        col_shap1, col_shap2 = st.columns([2, 1])
        #print(explainer.expected_value[1])
        #print(shap_values[0][:,1])
        
        with col_shap1:
            # 决策图可视化
            plt.figure(figsize=(10, 6))
            shap.decision_plot(
                explainer.expected_value[1],
                shap_values[0][:,1],
                features_names,
                feature_display_range=slice(None, None, -1),
                highlight=0
            )
            st.pyplot(plt.gcf())
        
        with col_shap2:
            # 特征重要性排序
            st.markdown("**Key Influencing Factors**")
            importance_df = pd.DataFrame({
                'Feature': features_names,
                'Impact': shap_values[0][:,1]
            }).sort_values('Impact', key=abs, ascending=False).head(10)
            
            for _, row in importance_df.iterrows():
                impact_color = "#e74c3c" if row['Impact'] > 0 else "#3498db"
                st.markdown(
                    f"<div style='margin:0.5rem 0; padding:0.5rem; border-radius:5px; "
                    f"background:{impact_color}20; border-left:4px solid {impact_color}'>"
                    f"<b>{row['Feature']}</b>: {row['Impact']:+.3f}</div>",
                    unsafe_allow_html=True
                )
            
    except Exception as e:
        st.error(f"Prediction failed: {str(e)}")