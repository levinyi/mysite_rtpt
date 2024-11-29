import os
import joblib
import numpy as np
import pandas as pd
import sys
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score

# 计算总罚分函数
def calculate_total_penalty_importances(data, importances):
    # 确保 data 是一个 NumPy 数组
    data = np.array(data, dtype=float)  # 将 data 转换为 NumPy 数组
    return np.dot(data, importances)


def predict_new_data_from_df(new_data_df, model_path, scaler=None, weights_path=None):
    # 加载模型
    model = joblib.load(model_path)
    weights = np.load(weights_path) if weights_path else None

    # 提取特征
    feature_columns = [
        'HighGC_penalty_score', 'LowGC_penalty_score', 'W12S12Motifs_penalty_score','LongRepeats_penalty_score', 
        'Homopolymers_penalty_score', 'DoubleNT_penalty_score', 'LCC'
    ]
    X_new = new_data_df[feature_columns].fillna(0)

    # 将所有特征列转换为数值类型，无法转换的设为0
    X_new = X_new.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # 保留原始特征用于计算罚分（使用未标准化的数据）
    X_original = X_new.copy()
    new_data_df['total_penalty_score'] = sum(X_original[col] for col in feature_columns)

    # 标准化特征（如果有标准化器）
    if scaler:
        scaler = joblib.load(scaler)
        X_new = scaler.transform(X_new)
        pass

    # 预测
    predictions = model.predict(X_new)
    
    if weights is not None:
        new_data_df['total_penalty_score_weight'] = np.dot(X_new, weights)
    
    # Add predictions and total penalty score to DataFrame
    new_data_df['predictions'] = predictions

    # **Set decimal precision for specific columns**
    columns_to_round = [
        'HighGC_penalty_score', 'LowGC_penalty_score', 'W12S12Motifs_penalty_score',
        'LongRepeats_penalty_score', 'Homopolymers_penalty_score', 'DoubleNT_penalty_score',
        'LCC', 'total_penalty_score'
    ]
    # Round these columns to 4 decimal places
    new_data_df[columns_to_round] = new_data_df[columns_to_round].round(4)

    return new_data_df

# 计算特异性
def specificity_score(y_true, y_pred):
    tn, fp, _, _ = confusion_matrix(y_true, y_pred).ravel()
    return tn / (tn + fp)

# 预测示例
def main(data_df, model_index):
    # 设置模型和权重文件路径
    model_path = f"best_rf_model_{model_index}.pkl"
    scaler = f"scaler_{model_index}.pkl"
    weights_path = f'best_rf_weights_{model_index}.npy'
    
    # 预测新数据
    predicted_data = predict_new_data_from_df(data_df, model_path, scaler, weights_path)
    
    return predicted_data

def calculate_metrics(data_path, model_index):
    # 没有测试，可能有问题
    
    # 读取数据
    data_df = pd.read_csv(data_path, sep="\t")

    # 保存预测结果
    input_file_name = os.path.basename(data_path).split('.')[0]
    # output_dir = os.path.dirname(data_path)
    # output_file = os.path.join(output_dir, f'{input_file_name}_model_{model_index}_predicted.csv')
    # predicted_data.to_csv(output_file, index=False)
    
    # 计算混淆矩阵和其他指标
    try:
        tn, fp, fn, tp = confusion_matrix(data_df['MTP_Results'], data_df['predictions']).ravel()
        sensitivity = recall_score(data_df['MTP_Results'], data_df['predictions'])
        specificity = specificity_score(data_df['MTP_Results'], data_df['predictions'])
        accuracy = accuracy_score(data_df['MTP_Results'], data_df['predictions'])
        false_positive_rate = fp / (fp + tn)
    except ValueError:
        accuracy, sensitivity, specificity = 0, 0, 0
        tn, fp, fn, tp = 0, 0, 0, 0
        false_positive_rate = 0
    
    # 输出结果
    # print(f"{input_file_name}\t{tp}\t{tn}\t{fp}\t{fn}\t{sensitivity:.4f}\t{specificity:.4f}\t{accuracy:.4f}\t{false_positive_rate:.4f}")

    # 输出结果
    # print(f"Model {model_index} Results\tTP: {tp}\tTN: {tn}\tFP: {fp}\tFN: {fn}")
    # print(f"Sensitivity: {sensitivity:.4f}\tSpecificity: {specificity:.4f}\tAccuracy: {accuracy:.4f}\tFalse Positive Rate: {false_positive_rate:.4f}")

    return data_df

if __name__ == "__main__":
    data_path = sys.argv[1]  # 输入文件路径
    model_index = sys.argv[2]  # 模型索引

    data_df = pd.read_csv(data_path, sep="\t")
    predicted_df = main(data_path, model_index)
    # print("Prediction completed!")
