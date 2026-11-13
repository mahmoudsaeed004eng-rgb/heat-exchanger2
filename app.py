import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# إعدادات الصفحة
st.set_page_config(
    page_title="تصميم المبادل الحراري E-1", page_icon="🔥", layout="wide"
)

st.title("🔥 تصميم وتحسين المبادل الحراري (Shell & Tube - Case 1: E-1)")
st.markdown(
    "**الهدف التصميمي:** تسخين خليط التغذية العضوي (Limonene + Cyclohexane + α-Pinene) باستخدام بخار منخفض الضغط (LPS)[span_0](start_span)[span_0](end_span)."
)

# --- القائمة الجانبية للمدخلات (Sidebar Inputs) ---
st.sidebar.header("⚙️ مدخلات التشغيل والتصميم")

st.sidebar.subheader("1. خصائص المائع البارد (Tube Side)")
m_lim = st.sidebar.number_input(
    "معدل تدفق الليمونين (kg/s)", value=0.422045, format="%.6f"
)
cp_lim = st.sidebar.number_input("الحرارة النوعية لليمونين (kJ/kg·K)", value=2.18)

m_cyc = st.sidebar.number_input(
    "معدل تدفق السيكلوهكسان (kg/s)", value=0.007005, format="%.6f"
)
q_cyc_total = st.sidebar.number_input(
    "إجمالي حرارة السيكلوهكسان مع التبخير (kW)", value=3.07145
)

m_pin = st.sidebar.number_input(
    "معدل تدفق ألفا-بينين (kg/s)", value=0.019000, format="%.6f"
)
cp_pin = st.sidebar.number_input("الحرارة النوعية لألفا-بينين (kJ/kg·K)", value=2.07)

t_cold_in = st.sidebar.number_input("حرارة دخول المائع البارد (°C)", value=70.0)
t_cold_out = st.sidebar.number_input("حرارة خروج المائع البارد (°C)", value=117.0)

st.sidebar.subheader("2. خصائص البخار الساخن (Shell Side)")
t_steam = st.sidebar.number_input("درجة حرارة البخار الثابتة (°C)", value=140.0)
h_cond = st.sidebar.number_input("حرارة تكثف البخار (kJ/kg)", value=2153.0)

st.sidebar.subheader("3. الثوابت الهندسية والأبعاد الأولية")
u_assumed = st.sidebar.number_input(
    "معامل انتقال الحرارة المفترض U (W/m²·°C)", value=300.0
)
f_factor = st.sidebar.number_input("معامل التصحيح (F)", value=1.0)
do_mm = st.sidebar.selectbox(
    "القطر الخارجي للأنبوب do (mm)", [12.0, 14.0, 16.0, 18.0, 20.0, 25.0], index=4
)
tube_length = st.sidebar.selectbox(
    "طول الأنبوب L (m)", [1.5, 1.83, 2.0, 2.44, 3.0], index=1
)
clearance_mm = st.sidebar.number_input(
    "خلوص الرأس العائم Clearance (mm)", value=53.0
)

# --- الحسابات الهندسية الأساسية ---
delta_t_cold = t_cold_out - t_cold_in
q_lim = m_lim * cp_lim * delta_t_cold
q_pin = m_pin * cp_pin * delta_t_cold
q_total_kw = q_lim + q_cyc_total + q_pin

# معدل تدفق البخار
m_steam = q_total_kw / h_cond

# حساب LMTD
dt1 = t_steam - t_cold_out
dt2 = t_steam - t_cold_in
if dt1 > 0 and dt2 > 0 and dt1 != dt2:
    lmtd = (dt2 - dt1) / math.log(dt2 / dt1)
else:
    lmtd = dt1

lmtd_corrected = lmtd * f_factor

# حساب المساحة والأنابيب
req_area = (q_total_kw * 1000) / (u_assumed * lmtd_corrected)
do_m = do_mm / 1000.0
area_one_tube = math.pi * do_m * tube_length
n_tubes = math.ceil(req_area / area_one_tube)
installed_area = n_tubes * area_one_tube

# أقطار الحزمة والغلاف (Square Pitch, 1 Pass: K1=0.215, n1=2.207)
k1, n1 = 0.215, 2.207
db_mm = do_mm * ((n_tubes / k1) ** (1 / n1))
ds_mm = db_mm + clearance_mm
l_ds_ratio = tube_length / (ds_mm / 1000.0)
baffle_spacing = ds_mm / 3.0

# --- عرض النتائج الرئيسية (KPIs) ---
st.subheader("📊 ملخص نتائج التصميم الحراري والميكانيكي")
col1, col2, col3, col4 = st.columns(4)
col1.metric("الحمل الحراري (Q)", f"{q_total_kw:.2f} kW")
col2.metric("معدل تدفق البخار", f"{m_steam:.4f} kg/s")
col3.metric("LMTD المصحح", f"{lmtd_corrected:.2f} °C")
col4.metric("المساحة المطلوبة (A)", f"{req_area:.3f} m²")

col5, col6, col7, col8 = st.columns(4)
col5.metric("عدد الأنابيب (Nt)", f"{n_tubes} أنبوب")
col6.metric("قطر الحزمة (Db)", f"{db_mm:.1f} mm")
col7.metric("قطر الغلاف (Ds)", f"{ds_mm:.1f} mm")
status_text = "✅ مقبول (5-10)" if 5 <= l_ds_ratio <= 10 else "⚠️ خارج المدى"
col8.metric("نسبة L/Ds", f"{l_ds_ratio:.2f}", status_text)

st.divider()

# --- الرسم البياني لتوزيع درجات الحرارة ---
st.subheader("📈 منحنى توزيع درجات الحرارة (Temperature Profile)")
x_vals = np.linspace(0, tube_length, 50)
t_hot_profile = np.full_like(x_vals, t_steam)
t_cold_profile = t_cold_in + (t_cold_out - t_cold_in) * (x_vals / tube_length)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=x_vals,
        y=t_hot_profile,
        mode="lines",
        name="البخار الساخن (Shell Side)",
        line=dict(color="red", width=3),
    )
)
fig.add_trace(
    go.Scatter(
        x=x_vals,
        y=t_cold_profile,
        mode="lines",
        name="الخليط العضوي (Tube Side)",
        line=dict(color="blue", width=3, dash="dash"),
    )
)
fig.update_layout(
    xaxis_title="طول الأنبوب (m)",
    yaxis_title="درجة الحرارة (°C)",
    height=400,
)
st.plotly_chart(fig, use_container_width=True)

# --- جدول التحسين الهندسي (Optimization Table) ---
st.subheader("🔍 جدول مقارنة الأبعاد القياسية والتحسين (Optimization)")
diameters = [12.0, 14.0, 16.0, 18.0, 20.0]
lengths = [1.5, 1.83, 2.0, 2.44]
opt_data = []

for d in diameters:
    for l in lengths:
        a_single = math.pi * (d / 1000.0) * l
        nt = math.ceil(req_area / a_single)
        a_inst = nt * a_single
        excess = ((a_inst - req_area) / req_area) * 100
        db = d * ((nt / k1) ** (1 / n1))
        ds = db + clearance_mm
        ratio = l / (ds / 1000.0)
        valid = 5.0 <= ratio <= 10.0
        opt_data.append(
            {
                "القطر (mm)": d,
                "الطول (m)": l,
                "عدد الأنابيب": nt,
                "المساحة الفعلية (m²)": round(a_inst, 3),
                "الزيادة %": round(excess, 2),
                "قطر الغلاف Ds (mm)": round(ds, 1),
                "نسبة L/Ds": round(ratio, 2),
                "تصميم مقبول؟": "✅ نعم" if valid else "❌ لا",
            }
        )

df_opt = pd.DataFrame(opt_data)
st.dataframe(df_opt, use_container_width=True)
