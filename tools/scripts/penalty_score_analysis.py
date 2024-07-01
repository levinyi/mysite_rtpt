import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score, roc_curve
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
from sklearn.linear_model import LinearRegression
import numpy as np


# 加载数据
data = pd.read_csv('/cygene4/pipeline/check_sequence_penalty_score/Pooled_Data_P243p30A10-A11-A12-A08-3p31A21.csv')


# 查找特征值全部为零且标签为零的样本
invalid_data = data[(data[['local_gc_content_penalty_score', 'W12S12_motifs_penalty_score', 
                           'long_repeats_penalty_score', 'homopolymers_penalty_score']].sum(axis=1) == 0)]

# 去除无效数据
data_cleaned = data.drop(invalid_data.index)

# 提取特征和标签
X_cleaned = data_cleaned[['local_gc_content_penalty_score', 'W12S12_motifs_penalty_score', 
                          'long_repeats_penalty_score', 'homopolymers_penalty_score']]
y_cleaned = data_cleaned['MTP_NGS']

# 使用逻辑回归模型计算特征权重
model = LogisticRegression(penalty='none', solver='lbfgs')
model.fit(X_cleaned, y_cleaned)
# 获取特征权重
weights = model.coef_[0]
print("Feature Weights:", weights)
# 重新计算总罚分
data_cleaned['total_penalty_score'] = np.dot(X_cleaned, weights)
# 显示前几行带有总罚分的数据
print(data_cleaned.head())

'''
# 检查数据
print(data.head())
print(data.describe())
print(data['MTP_NGS'].value_counts())

# 提取特征和标签
X = data[['local_gc_content_penalty_score', 'W12S12_motifs_penalty_score', 'long_repeats_penalty_score', 'homopolymers_penalty_score']]
y = data['MTP_NGS']

# 检查特征和标签
print(X.head())
print(y.head())

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# 训练模型
model = LogisticRegression(max_iter=100000)
model.fit(X_train, y_train)

# 预测
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

# 计算混淆矩阵
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:\n", cm)

# 分类报告
cr = classification_report(y_test, y_pred)
print("Classification Report:\n", cr)

# ROC曲线和AUC值
fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
auc = roc_auc_score(y_test, y_pred_proba)
plt.figure()
plt.plot(fpr, tpr, label='ROC curve (area = %0.2f)' % auc)
plt.plot([0, 1], [0, 1], 'k--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
plt.savefig('roc_curve.png')  # 保存ROC曲线图
plt.show()
print("AUC: ", auc)

# 获取模型权重
W1, W2, W3, W4 = model.coef_[0]
intercept = model.intercept_[0]

# 计算 penalty score
penalty_scores = X.dot([W1, W2, W3, W4]) + intercept

print("Weights:\n", W1, W2, W3, W4)
print("Intercept:\n", intercept)
print("Penalty Scores:\n", penalty_scores.describe())  # 输出 penalty score 的统计信息

# 将penalty score添加到原始数据中
data['Penalty Score'] = penalty_scores

# 通过排序和t检验来找到显著性阈值
sorted_scores = penalty_scores.sort_values()
best_threshold = 0
best_p_value = 1
for i in range(1, len(sorted_scores)):
    easy_group = sorted_scores[:i]
    hard_group = sorted_scores[i:]
    t_stat, p_value = ttest_ind(easy_group, hard_group)
    if p_value < best_p_value:
        best_p_value = p_value
        best_threshold = sorted_scores.iloc[i]

print("Best Threshold:", best_threshold)
print("Best P-Value:", best_p_value)

# 将 penalty score 分成两组
data['Label'] = ['hard' if score >= best_threshold else 'easy' for score in penalty_scores]

# 显示并保存结果
print(data['Label'].value_counts())  # 输出各组的样本数
print(data)
data.to_csv('penalty_scores_with_labels.csv', index=False)

# 绘制分类效果图
plt.figure(figsize=(10, 6))
plt.scatter(data[data['Label'] == 'easy'].index, data[data['Label'] == 'easy']['Penalty Score'], color='blue', label='Easy')
plt.scatter(data[data['Label'] == 'hard'].index, data[data['Label'] == 'hard']['Penalty Score'], color='red', label='Hard')
plt.axhline(y=best_threshold, color='green', linestyle='--', label=f'Threshold: {best_threshold:.2f}')
plt.xlabel('Index')
plt.ylabel('Penalty Score')
plt.title('Penalty Score Classification')
plt.legend()
plt.savefig('penalty_score_classification.png')
plt.show()
'''