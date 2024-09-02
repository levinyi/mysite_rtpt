import os
import joblib
import numpy as np
import pandas as pd
import sys
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score

# 计算总罚分函数
def calculate_total_penalty_importances(data, importances):
    return np.dot(data, importances)

# 计算总罚分加权函数
def calculate_weighted_penalty_score(data, weights):
    return np.dot(data, weights)

def predict_new_data(new_data_path, model_path, scaler=None, weights_path=None):
    # 加载模型
    model = joblib.load(model_path)
    weights = np.load(weights_path) if weights_path else None

    # 读取新数据
    new_data = pd.read_csv(new_data_path, sep='\t')
    
    # 提取特征
    feature_columns = [
        'highGC_penalty_score', 'lowGC_penalty_score', 'W12S12Motifs_penalty_score',
        'LongRepeats_penalty_score', 'Homopolymers_penalty_score', 'doubleNT_penalty_score',
        'LCC_penalty_score'
    ]
    X_new = new_data[feature_columns].fillna(0)
    
    # 标准化特征（如果有标准化器）
    if scaler:
        X_new = scaler.transform(X_new)
    
    # 预测
    predictions = model.predict(X_new)
    
    # 计算总罚分
    if hasattr(model, 'feature_importances_'):
        new_data['total_penalty_score_rf'] = calculate_total_penalty_importances(X_new, model.feature_importances_)
    if weights is not None:
        new_data['total_penalty_score_weight'] = calculate_weighted_penalty_score(X_new, weights)
    
    new_data['predictions'] = predictions
    
    return new_data

# 计算特异性
def specificity_score(y_true, y_pred):
    tn, fp, _, _ = confusion_matrix(y_true, y_pred).ravel()
    return tn / (tn + fp)

# 预测示例
def main():
    new_data_path = sys.argv[1]  # 输入文件路径
    index = sys.argv[2]  # 模型索引
    
    # 设置模型和权重文件路径
    model_path = f"best_rf_model_{index}.pkl"
    scaler = None  # 无需加载标准化器
    weights_path = f'best_rf_weights_{index}.npy'
    
    # 预测新数据
    predicted_data = predict_new_data(new_data_path, model_path, scaler, weights_path)
    
    # 保存预测结果
    input_file_name = os.path.basename(new_data_path).split('.')[0]
    output_dir = os.path.dirname(new_data_path)
    output_file = os.path.join(output_dir, f'{input_file_name}_model_{index}_predicted.csv')
    predicted_data.to_csv(output_file, index=False)
    
    # 计算混淆矩阵和其他指标
    try:
        tn, fp, fn, tp = confusion_matrix(predicted_data['MTP_Results'], predicted_data['predictions']).ravel()
        sensitivity = recall_score(predicted_data['MTP_Results'], predicted_data['predictions'])
        specificity = specificity_score(predicted_data['MTP_Results'], predicted_data['predictions'])
        accuracy = accuracy_score(predicted_data['MTP_Results'], predicted_data['predictions'])
        false_positive_rate = fp / (fp + tn)
    except ValueError:
        accuracy, sensitivity, specificity = 0, 0, 0
        tn, fp, fn, tp = 0, 0, 0, 0
        false_positive_rate = 0
    
    # 输出结果
    print(f"{input_file_name}\t{tp}\t{tn}\t{fp}\t{fn}\t{sensitivity:.4f}\t{specificity:.4f}\t{accuracy:.4f}\t{false_positive_rate:.4f}")

if __name__ == "__main__":
    main()
