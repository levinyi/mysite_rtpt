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

# 计算总罚分加权函数
def calculate_weighted_penalty_score(data, weights):
    return np.dot(data, weights)

def predict_new_data_from_df(new_data_df, model_path, scaler=None, weights_path=None):
    # 加载模型
    model = joblib.load(model_path)
    weights = np.load(weights_path) if weights_path else None

    # 提取特征
    feature_columns = [
        'HighGC_penalty_score', 'LowGC_penalty_score', 'W12S12Motifs_penalty_score',
        'LongRepeats_penalty_score', 'Homopolymers_penalty_score', 'DoubleNT_penalty_score',
        'LCC', 'Total_Length'
    ]
    X_new = new_data_df[feature_columns].fillna(0)

    # 强制将 'LCC' 列转换为 float 类型
    X_new['LCC'] = pd.to_numeric(X_new['LCC'], errors='coerce').fillna(0)

    # 标准化特征（如果有标准化器）
    if scaler:
        X_new = scaler.transform(X_new)
    # 预测
    predictions = model.predict(X_new)
    print("predictions: ", predictions)  # 打印预测结果, 0 代表不能合成成功，1 代表可以合成成功
    # print("model.feature_importances_: ")
    # print(model.feature_importances_)
    # print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    # 计算总罚分
    if hasattr(model, 'feature_importances_'):
        X_new_for_importances = X_new.values.astype(float)  # 将 DataFrame 转换为 NumPy 数组
        new_data_df['total_penalty_score_rf'] = calculate_total_penalty_importances(X_new_for_importances, model.feature_importances_)
    
    if weights is not None:
        new_data_df['total_penalty_score_weight'] = calculate_weighted_penalty_score(X_new, weights)
    # print(model.feature_importances_)
    # print(weights)
    new_data_df['predictions'] = predictions
    new_data_df['total_penalty_score'] = new_data_df['total_penalty_score_rf'] if 'total_penalty_score_rf' in new_data_df else new_data_df['total_penalty_score_weight']
    # print("new_data_df: ", new_data_df)
    return new_data_df

# 计算特异性
def specificity_score(y_true, y_pred):
    tn, fp, _, _ = confusion_matrix(y_true, y_pred).ravel()
    return tn / (tn + fp)

# 预测示例
def main(data_df, model_index):
    # 设置模型和权重文件路径
    model_path = f"best_rf_model_{model_index}.pkl"
    scaler = None  # 无需加载标准化器
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
    print(f"{input_file_name}\t{tp}\t{tn}\t{fp}\t{fn}\t{sensitivity:.4f}\t{specificity:.4f}\t{accuracy:.4f}\t{false_positive_rate:.4f}")

    # 输出结果
    print(f"Model {model_index} Results\tTP: {tp}\tTN: {tn}\tFP: {fp}\tFN: {fn}")
    print(f"Sensitivity: {sensitivity:.4f}\tSpecificity: {specificity:.4f}\tAccuracy: {accuracy:.4f}\tFalse Positive Rate: {false_positive_rate:.4f}")

    return data_df

if __name__ == "__main__":
    data_path = sys.argv[1]  # 输入文件路径
    model_index = sys.argv[2]  # 模型索引

    data_df = pd.read_csv(data_path, sep="\t")
    predicted_df = main(data_path, model_index)
    print("Prediction completed!")
