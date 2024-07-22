import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

# 设置随机种子以确保结果的稳定性
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# 读取数据
file_path = '/cygene4/pipeline/check_sequence_penalty_score/Pooled.10samples.txt'   # , '/cygene4/pipeline/check_sequence_penalty_score/Pooled_Data_P243p30A10-A11-A12-A08-3p31A21.csv'
data = pd.read_csv(file_path, sep="\t")

# 提取特征和标签
X = data[['local_gc_content_penalty_score', 'W12S12_motifs_penalty_score', 'long_repeats_penalty_score', 'homopolymers_penalty_score']]
y = data['MTP_Results']

# 标准化特征
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=RANDOM_SEED)

# 随机森林超参数调优
rf_param_dist = {
    'n_estimators': [50, 100],
    'max_depth': [None, 10, 20],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 2]
}

rf_random_search = RandomizedSearchCV(RandomForestClassifier(random_state=RANDOM_SEED), rf_param_dist, n_iter=10, cv=3, scoring='accuracy', random_state=RANDOM_SEED)
rf_random_search.fit(X_train, y_train)

# 最优随机森林模型
best_rf_model = rf_random_search.best_estimator_
best_rf_accuracy = best_rf_model.score(X_test, y_test)

# 打印最优模型准确率
print(f'Best Random Forest Accuracy: {best_rf_accuracy:.4f}')

# 计算总罚分函数
def calculate_total_penalty_importances(data, importances, scaler):
    scaled_features = scaler.transform(data[['local_gc_content_penalty_score', 'W12S12_motifs_penalty_score', 'long_repeats_penalty_score', 'homopolymers_penalty_score']])
    return np.dot(scaled_features, importances)

# 使用最优随机森林模型权重计算总罚分
best_rf_weights = best_rf_model.feature_importances_
data['total_penalty_score_rf'] = calculate_total_penalty_importances(data, best_rf_weights, scaler)

# 保存模型和标准化器
joblib.dump(best_rf_model, 'best_rf_model3.pkl')
joblib.dump(scaler, 'scaler3.pkl')

# 保存结果
# output_file_path = 'optimized_penalty_scores.Test.csv'
# data.to_csv(output_file_path, index=False)
# print(f"Results saved to {output_file_path}")

# 打印最优模型的权重
print("Optimal weights from the best Random Forest model:")
print(f'local_gc_content_penalty_score: {best_rf_weights[0]:.4f}')
print(f'W12S12_motifs_penalty_score: {best_rf_weights[1]:.4f}')
print(f'long_repeats_penalty_score: {best_rf_weights[2]:.4f}')
print(f'homopolymers_penalty_score: {best_rf_weights[3]:.4f}')
