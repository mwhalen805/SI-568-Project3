"""Final combined chart — A on top, B/C/D side by side below."""
import pandas as pd
import numpy as np
import altair as alt

alt.data_transformers.disable_max_rows()

np.random.seed(42)

df = pd.read_csv('Absenteeism_at_work.csv', sep=';')
emp = df.groupby('ID').agg(
    Distance=('Distance from Residence to Work', 'first'),
    TransportCost=('Transportation expense', 'first'),
    Workload=('Work load Average/day ', 'mean'),
    HitTarget=('Hit target', 'mean'),
    TotalAbsentHours=('Absenteeism time in hours', 'sum'),
).reset_index()
emp['Employee'] = 'Emp ' + emp['ID'].astype(str)


def min_max_norm(s):
    return (s - s.min()) / (s.max() - s.min())


dist_med = emp['Distance'].median()
cost_med = emp['TransportCost'].median()

emp['ExploitScore'] = (
    min_max_norm(emp['Distance']) * 0.35
    + min_max_norm(emp['TransportCost']) * 0.35
    + min_max_norm(emp['Workload']) * 0.15
    + (1 - min_max_norm(emp['HitTarget'])) * 0.15
) * 100

# ── A: Quadrant-based color ────────────────────────────────────────────
emp['Quadrant'] = np.select(
    [
        (emp['Distance'] <= dist_med) & (emp['TransportCost'] > cost_med),
        (emp['Distance'] > dist_med) & (emp['TransportCost'] > cost_med),
        (emp['Distance'] > dist_med) & (emp['TransportCost'] <= cost_med),
        (emp['Distance'] <= dist_med) & (emp['TransportCost'] <= cost_med),
    ],
    ['Near + Expensive', 'Far + Expensive', 'Far + Cheap', 'Near + Cheap'],
    default='Other',
)

# Jitter
emp['Dist_j'] = emp['Distance'] + np.random.uniform(-1.2, 1.2, len(emp))
emp['Cost_j'] = emp['TransportCost'] + np.random.uniform(-5, 5, len(emp))

# Near+Expensive flag
emp['NearExpensive'] = emp['Quadrant'] == 'Near + Expensive'

quad_colors_a = alt.Scale(
    domain=['Near + Expensive', 'Far + Expensive', 'Far + Cheap', 'Near + Cheap'],
    range=['#c0272d', "#fce8d1", "#c0e4bf", "#ede1b1"]
)

points_a = alt.Chart(emp).mark_circle(size=120, strokeWidth=0.6, stroke='#333', opacity=1).encode(
    x=alt.X('Dist_j:Q', title='Distance from Residence to Work (km)',
            scale=alt.Scale(domain=[0, 58])),
    y=alt.Y('Cost_j:Q', title='Monthly Transportation Expense ($)',
            scale=alt.Scale(domain=[100, 430])),
    color=alt.Color('Quadrant:N', scale=quad_colors_a,
                    legend=alt.Legend(title='Quadrant', orient='none',
                                     legendX=370, legendY=5, direction='horizontal',
                                     titleFontSize=9, labelFontSize=8,
                                     columns=4)),
)

ne = emp[emp['NearExpensive']].copy()
offsets = {
    31: (8, -10), 13: (8, -10), 18: (8, -10), 26: (8, 12),
    7: (8, -10), 21: (8, 10), 33: (8, -10), 24: (8, 10),
}
label_layers_a = []
for _, row in ne.iterrows():
    dx, dy = offsets.get(row['ID'], (8, -8))
    lbl = alt.Chart(pd.DataFrame([row])).mark_text(
        dx=dx, dy=dy, fontSize=8, fontWeight='bold', color='#b71c1c'
    ).encode(x='Dist_j:Q', y='Cost_j:Q', text='Employee:N')
    label_layers_a.append(lbl)

vline_a = alt.Chart(pd.DataFrame({'x': [dist_med]})).mark_rule(
    color='#888', strokeDash=[6, 3], strokeWidth=1.2
).encode(x='x:Q')
hline_a = alt.Chart(pd.DataFrame({'y': [cost_med]})).mark_rule(
    color='#888', strokeDash=[6, 3], strokeWidth=1.2
).encode(y='y:Q')

zone_label = alt.Chart(pd.DataFrame({
    'x': [3], 'y': [425], 'text': ['⚠ SUSPICIOUS ZONE']
})).mark_text(fontSize=11, fontWeight='bold', color='#b71c1c', align='left'
).encode(x='x:Q', y='y:Q', text='text:N')

zone_sub = alt.Chart(pd.DataFrame({
    'x': [3], 'y': [414], 'text': ['Near but Expensive']
})).mark_text(fontSize=9, color='#b71c1c', align='left', fontStyle='italic'
).encode(x='x:Q', y='y:Q', text='text:N')

dist_lbl = alt.Chart(pd.DataFrame({
    'x': [dist_med + 1], 'y': [108], 'text': [f'Median = {dist_med:.0f} km']
})).mark_text(fontSize=8, color='#666', align='left', fontStyle='italic'
).encode(x='x:Q', y='y:Q', text='text:N')

cost_lbl = alt.Chart(pd.DataFrame({
    'x': [1], 'y': [cost_med + 7], 'text': [f'Median = ${cost_med:.0f}']
})).mark_text(fontSize=8, color='#666', align='left', fontStyle='italic'
).encode(x='x:Q', y='y:Q', text='text:N')

chart_a = points_a + vline_a + hline_a + zone_label + zone_sub + dist_lbl + cost_lbl
for lbl in label_layers_a:
    chart_a = chart_a + lbl
chart_a = chart_a.properties(
    width=700, height=300,
    title=alt.Title("A. Who's Spending Too Much to Get Here?",
                    fontSize=14, fontWeight='bold', anchor='middle')
)

# ── B: Horizontal Bar — Productivity per Transport Dollar ─────────────
emp['ProdPerDollar'] = (emp['HitTarget'] / 100 * emp['Workload']) / emp['TransportCost']

bars_b = alt.Chart(emp).mark_bar(strokeWidth=0.4, stroke='#333').encode(
    y=alt.Y('Employee:N',
            sort=alt.EncodingSortField(field='ProdPerDollar', order='ascending'),
            title=None, axis=alt.Axis(labelFontSize=8)),
    x=alt.X('ProdPerDollar:Q', title='Prod / $',
            scale=alt.Scale(domain=[0, emp['ProdPerDollar'].max() * 1.1])),
    color=alt.Color('ProdPerDollar:Q',
                    scale=alt.Scale(scheme='redyellowgreen',
                                    domain=[emp['ProdPerDollar'].min(), emp['ProdPerDollar'].max()]),
                    legend=None),
)

avg_prod = emp['ProdPerDollar'].mean()
avg_line_b = alt.Chart(pd.DataFrame({'x': [avg_prod]})).mark_rule(
    color='#b71c1c', strokeDash=[6, 3], strokeWidth=1.5
).encode(x='x:Q')

avg_text_b = alt.Chart(pd.DataFrame({
    'x': [avg_prod], 'label': [f'Avg ({avg_prod:.2f})']
})).mark_text(
    align='left', dx=3, dy=-200, fontSize=8, fontWeight='bold', color='#b71c1c'
).encode(x='x:Q', text='label:N')

chart_b = (bars_b + avg_line_b + avg_text_b).properties(
    width=200, height=420,
    title=alt.Title("B. Bang for the Buck",
                    fontSize=12, fontWeight='bold', anchor='middle',
                    subtitle='Productivity = (HitTarget% × Workload) / TransportCost',
                    subtitleFontSize=8, subtitleColor='#666')
)

# ── C: Heatmap ────────────────────────────────────────────────────────
heatmap_cols = ['Distance', 'TransportCost', 'Workload', 'HitTarget']
emp_hm = emp[['Employee', 'ExploitScore'] + heatmap_cols].copy()
for c in heatmap_cols:
    emp_hm[c] = min_max_norm(emp_hm[c])
emp_hm['HitTarget'] = 1 - emp_hm['HitTarget']

hm_long = emp_hm.melt(id_vars=['Employee', 'ExploitScore'],
                       value_vars=heatmap_cols,
                       var_name='Metric', value_name='NormValue')
hm_long['Metric'] = hm_long['Metric'].replace({
    'Distance': 'Dist',
    'TransportCost': 'Cost',
    'Workload': 'Work',
    'HitTarget': 'Miss%',
})

chart_c = alt.Chart(hm_long).mark_rect(stroke='white', strokeWidth=0.4).encode(
    y=alt.Y('Employee:N',
            sort=alt.EncodingSortField(field='ExploitScore', order='descending'),
            title=None, axis=alt.Axis(labelFontSize=8)),
    x=alt.X('Metric:N', title=None, axis=alt.Axis(labelFontSize=9, labelAngle=-30)),
    color=alt.Color('NormValue:Q',
                    scale=alt.Scale(scheme='redyellowgreen', reverse=True, domain=[0, 1]),
                    legend=None),
).properties(
    width=140, height=420,
    title=alt.Title('C. Risk Heatmap',
                    fontSize=12, fontWeight='bold', anchor='middle',
                    subtitle='Score = Dist×.35 + Cost×.35 + Work×.15 + Miss×.15',
                    subtitleFontSize=8, subtitleColor='#666')
)

# ── D: Slope Chart ────────────────────────────────────────────────────
emp['CostRank'] = emp['TransportCost'].rank(ascending=False, method='first').astype(int)
emp['AbsentRank'] = emp['TotalAbsentHours'].rank(ascending=False, method='first').astype(int)
emp['Trapped'] = (emp['CostRank'] <= 12) & (emp['AbsentRank'] > 18)
emp['Category'] = np.where(emp['Trapped'], 'Trapped & Reliable', 'Other')

metric_order = ['Cost Rank', 'Absence Rank']
slope_data = pd.concat([
    emp.assign(Metric='Cost Rank', Rank=emp['CostRank']),
    emp.assign(Metric='Absence Rank', Rank=emp['AbsentRank']),
])

lines_d = alt.Chart(slope_data).mark_line().encode(
    x=alt.X('Metric:N', title=None, sort=metric_order,
            axis=alt.Axis(labelFontSize=9, labelFontWeight='bold', labelAngle=0)),
    y=alt.Y('Rank:Q', title='Rank',
            scale=alt.Scale(domain=[0, 37], reverse=True),
            axis=alt.Axis(values=list(range(1, 37, 5)), labelFontSize=8)),
    detail='Employee:N',
    color=alt.Color('Category:N',
                    scale=alt.Scale(domain=['Trapped & Reliable', 'Other'],
                                   range=['#d73027', '#b0b0b0']),
                    legend=alt.Legend(title='Category', orient='none',
                                     legendX=175, legendY=5,
                                     titleFontSize=9, labelFontSize=8)),
    strokeWidth=alt.condition(
        alt.datum.Category == 'Trapped & Reliable',
        alt.value(2.2), alt.value(0.7)
    ),
    opacity=alt.condition(
        alt.datum.Category == 'Trapped & Reliable',
        alt.value(0.9), alt.value(0.35)
    ),
)

dots_d = alt.Chart(slope_data).mark_circle(strokeWidth=0.4, stroke='#333').encode(
    x=alt.X('Metric:N', sort=metric_order),
    y=alt.Y('Rank:Q', scale=alt.Scale(domain=[0, 37], reverse=True)),
    detail='Employee:N',
    color=alt.Color('Category:N',
                    scale=alt.Scale(domain=['Trapped & Reliable', 'Other'],
                                   range=['#d73027', '#b0b0b0']),
                    legend=None),
    size=alt.condition(
        alt.datum.Category == 'Trapped & Reliable',
        alt.value(45), alt.value(18)
    ),
    opacity=alt.condition(
        alt.datum.Category == 'Trapped & Reliable',
        alt.value(0.9), alt.value(0.4)
    ),
)

trapped = emp[emp['Trapped']]
lbl_left_d = alt.Chart(trapped).mark_text(
    fontSize=8, fontWeight='bold', color='#b71c1c', align='right'
).encode(
    x=alt.value(45),
    y=alt.Y('CostRank:Q', scale=alt.Scale(domain=[0, 37], reverse=True)),
    text='Employee:N',
)
lbl_right_d = alt.Chart(trapped).mark_text(
    fontSize=8, fontWeight='bold', color='#b71c1c', align='left'
).encode(
    x=alt.value(238),
    y=alt.Y('AbsentRank:Q', scale=alt.Scale(domain=[0, 37], reverse=True)),
    text='Employee:N',
)

chart_d = (lines_d + dots_d + lbl_left_d).properties(
    width=220, height=420,
    title=alt.Title("D. Who's Trapped?",
                    fontSize=12, fontWeight='bold', anchor='middle',
                    subtitle='High cost rank but low absence rank = financially trapped',
                    subtitleFontSize=8, subtitleColor='#666')
)

# ══════════════════════════════════════════════════════════════════════
# COMBINE: A on top, B|C|D below
# ══════════════════════════════════════════════════════════════════════
bottom = alt.hconcat(chart_b, chart_c, chart_d, spacing=15)

final = alt.vconcat(
    chart_a, bottom, spacing=20
).properties(
    title=alt.Title(
        'Commuter Exploitation Dashboard: Identifying Targets for the Evil Boss',
        fontSize=18, fontWeight='bold', anchor='middle',
        subtitle=' ',
        subtitleFontSize=4,
    )
).configure(
    font='Arial',
).configure_view(
    strokeWidth=0
).configure_axis(
    gridColor='#e8e8e8'
)

final.save('final_dashboard.png', scale_factor=2)
print('Done! final_dashboard.png saved')
