# 使用保存的模型预测新数据
import os
import joblib
import numpy as np
import pandas as pd
import sys
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score

# 计算总罚分函数
def calculate_total_penalty_importances(data, importances, scaler):
    scaled_features = scaler.transform(data)
    return np.dot(scaled_features, importances)

# 计算总罚分加权函数
def calculate_weighted_penalty_score(data, weights):
    return np.dot(data, weights)

def predict_new_data(new_data_path, model_path='best_rf_model3.pkl', scaler_path='scaler3.pkl', weights_path='best_rf_weights3.npy'):
    # 加载模型和标准化器
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    weights = np.load(weights_path)

    # 读取新数据
    new_data = pd.read_csv(new_data_path, sep='\t')
    
    # 提取特征并标准化
    X_new = new_data[['highGC_penalty_score', 'lowGC_penalty_score', 'W12S12Motifs_penalty_score', 'LongRepeats_penalty_score', 'Homopolymers_penalty_score','LCC_penalty_score']].fillna(0)
    
    # 标准化特征
    X_new_scaled = scaler.transform(X_new)
    
    # 预测
    predictions = model.predict(X_new_scaled)
    
    # 计算总罚分
    new_data['total_penalty_score_rf'] = calculate_total_penalty_importances(X_new, model.feature_importances_, scaler)
    new_data['total_penalty_score_weight'] = calculate_weighted_penalty_score(X_new, weights)
    new_data['predictions'] = predictions
    
    return new_data

# 计算特异性
def specificity_score(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return tn / (tn + fn)

# 预测示例
new_data_path = sys.argv[1]  # '/cygene4/pipeline/check_sequence_penalty_score/Pooled_Data_P243p30A10-A11-A12-A08-3p31A21.csv'
index = sys.argv[2]
predicted_data = predict_new_data(new_data_path, f"best_rf_model_{index}.pkl", f"scaler_{index}.pkl", f'best_rf_weights_{index}.npy')

# 保存预测结果
input_file_name = new_data_path.split('/')[-1].split('.')[0]
output_dir = os.path.dirname(new_data_path)
predicted_data.to_csv(os.path.join(output_dir, f'{input_file_name}_model_{index}_predicted.csv'), index=False)

# 计算混淆矩阵和其他指标
try:
    tn, fn, fp, tp = confusion_matrix(predicted_data['MTP_Results'], predicted_data['predictions']).ravel()
    sensitivity = recall_score(predicted_data['MTP_Results'], predicted_data['predictions'])
    specificity = specificity_score(predicted_data['MTP_Results'], predicted_data['predictions'])
    accuracy = accuracy_score(predicted_data['MTP_Results'], predicted_data['predictions'])
    false_positive_rate = fp / (fp + tn)
except ValueError:
    accuracy, sensitivity, specificity = 0, 0, 0
    tn, fp, fn, tp = 0, 0, 0, 0
    false_positive_rate = 0

print(f"{input_file_name}\t{tp}\t{tn}\t{fp}\t{fn}\t{sensitivity:.4f}\t{specificity:.4f}\t{accuracy:.4f}\t{false_positive_rate:.4f}")
# 敏感度（召回率）、特异性、精确度（准确率）和假阳性率（误报率）。