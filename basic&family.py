# Basic Data Exploration (Summary Stats & Visualizations)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("Absenteeism_at_work.csv", sep=';')

print(df.info())
print(df.describe())
print(df.isnull().sum())

plt.figure(figsize=(8,5))
sns.histplot(df['Absenteeism time in hours'], bins=20, kde=True)
plt.title("Absenteeism Time Distribution")
plt.xlabel("Hours")
plt.ylabel("Count")
plt.show()

plt.figure(figsize=(8,5))
sns.boxplot(x='Day of the week', y='Absenteeism time in hours', data=df)
plt.title("Absenteeism by Day of the Week")
plt.show()

plt.figure(figsize=(8,5))
sns.scatterplot(x='Age', y='Absenteeism time in hours', data=df)
plt.title("Age vs Absenteeism Hours")
plt.show()

plt.figure(figsize=(10,6))
sns.heatmap(df[['Son','Pet','Age','Service time','Absenteeism time in hours']].corr(), annot=True, cmap='coolwarm')
plt.title("Correlation Matrix")
plt.show()



# Family Burden Score Calculation

def family_burden(row):
    score = row['Son']*2 + row['Pet'] # Children have a higher weight when calculating family burden.
    if 25 <= row['Age'] <= 50:
        score += 1 # Middle-aged employees may have more family responsibilities.
    score += 0.5 * (row['Service time'] // 2) # Used to assess employee loyalty. Long-tenured employees may “tolerate more.”
    return score

df['Family_Burden_Score'] = df.apply(family_burden, axis=1)

threshold = df['Family_Burden_Score'].quantile(0.8)
df['High_Family_Burden_Likelihood'] = df['Family_Burden_Score'] >= threshold # Employees in the top 20% of family burden scores are flagged.

print(df[['Son','Pet','Age','Service time','Family_Burden_Score','Absenteeism time in hours']].sort_values('Family_Burden_Score', ascending=False).head(10))

df.to_csv("Absenteeism_with_Family_Burden.csv", index=False)