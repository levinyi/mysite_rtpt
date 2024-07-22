# 使用保存的模型预测新数据
import joblib
import numpy as np
import pandas as pd
import sys
from sklearn.metrics import accuracy_score, confusion_matrix


# 计算总罚分函数
def calculate_total_penalty_importances(data, importances, scaler):
    # 检查并处理缺失值
    data = data[['local_gc_content_penalty_score', 'W12S12_motifs_penalty_score', 'long_repeats_penalty_score', 'homopolymers_penalty_score']].fillna(0)
    scaled_features = scaler.transform(data)
    return np.dot(scaled_features, importances)


def predict_new_data(new_data_path, model_path='best_rf_model2.pkl', scaler_path='scaler2.pkl'):
    # 加载模型和标准化器
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # 读取新数据
    new_data = pd.read_csv(new_data_path, sep='\t')
    
    # 提取特征并标准化
    X_new = new_data[['local_gc_content_penalty_score', 'W12S12_motifs_penalty_score', 'long_repeats_penalty_score', 'homopolymers_penalty_score']].fillna(0)
    
    # 标准化特征
    X_new_scaled = scaler.transform(X_new)
    
    # 预测
    predictions = model.predict(X_new_scaled)
    
    # 计算总罚分
    new_data['total_penalty_score_rf'] = calculate_total_penalty_importances(new_data, model.feature_importances_, scaler)
    new_data['predictions'] = predictions
    
    return new_data


# 预测示例
new_data_path = sys.argv[1]  # '/cygene4/pipeline/check_sequence_penalty_score/Pooled_Data_P243p30A10-A11-A12-A08-3p31A21.csv'
predicted_data = predict_new_data(new_data_path)
# print(predicted_data)
input_file_name = new_data_path.split('/')[-1].split('.')[0]
predicted_data.to_csv(f'{input_file_name}_model3_predicted.csv', index=False)


# 计算混淆矩阵
try:
    accuracy = accuracy_score(predicted_data['MTP_Results'], predicted_data['predictions'])
    tn, fp, fn, tp = confusion_matrix(predicted_data['MTP_Results'], predicted_data['predictions']).ravel()
except ValueError:
    tn, fp, fn, tp = 0, 0, 0, 0

print(f"{input_file_name}\t{accuracy:.4f}\t{tp}\t{tn}\t{fp}\t{fn}")