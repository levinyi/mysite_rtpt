import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score


# 设置随机种子以确保结果的稳定性
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def main(data, index):

    # 提取特征和标签
    X = data[['highGC_penalty_score', 'lowGC_penalty_score', 'W12S12Motifs_penalty_score', 
            'LongRepeats_penalty_score', 'Homopolymers_penalty_score', 
            'LCC_penalty_score',
            ]]
    y = data['MTP_Results']

    # 移除前5列全为空的行
    X = X.dropna(subset=['highGC_penalty_score', 'lowGC_penalty_score', 'W12S12Motifs_penalty_score', 
                        'LongRepeats_penalty_score', 'Homopolymers_penalty_score'], how='all')
    y = y.loc[X.index]

    # 标准化特征
    '''
    在机器学习中，是否需要标准化特征数据取决于您使用的模型类型。对于 RandomForestClassifier 这样的基于树的模型，标准化并不是严格必要的，因为随机森林不依赖于特征的尺度或分布。但是，对于一些基于距离的模型（如线性回归、逻辑回归、支持向量机、k近邻算法等），标准化是非常重要的。
    尽管如此，标准化特征数据仍然有一些好处：
    对比特征重要性：标准化后可以更直观地对比不同特征的重要性。
    处理具有不同量纲的特征：如果您的数据集中有一些特征的量纲差异很大，标准化可以防止这些特征对模型产生不均衡的影响。

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    '''

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)

    # 随机森林超参数调优
    rf_param_dist = {
        'n_estimators': [50, 100, 200],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }

    # 使用 RandomizedSearchCV 来在给定的超参数范围内随机搜索最佳的超参数组合，然后用这些超参数训练一个 RandomForestClassifier。
    rf_random_search = RandomizedSearchCV(RandomForestClassifier(random_state=RANDOM_SEED), rf_param_dist, n_iter=20, cv=3, scoring='accuracy', random_state=RANDOM_SEED)
    '''
        具体解释如下：
        RandomForestClassifier：这是基础模型。它是一个随机森林分类器。
        RandomizedSearchCV：这是一个用于超参数搜索的工具。它会在指定的参数空间内进行随机采样，并评估每个采样点的模型性能。
        在这行代码中，RandomizedSearchCV 会执行以下操作：
            使用 rf_param_dist 中定义的超参数空间进行采样。
            执行 n_iter=20 次采样，即随机选择20组超参数组合进行评估。
            使用 3 折交叉验证 (cv=3) 评估每组超参数组合的性能。
            使用 accuracy 作为评估标准 (scoring='accuracy')。
            在评估过程中，所有的随机性由 random_state=RANDOM_SEED 控制，以确保结果的可重复性。
            最终，RandomizedSearchCV 将选择性能最好的那组超参数，并返回对应的 RandomForestClassifier 模型。这个模型就是 rf_random_search.best_estimator_，即 best_rf_model。
    '''
    rf_random_search.fit(X_train, y_train)

    # 最优随机森林模型
    best_rf_model = rf_random_search.best_estimator_
    best_rf_accuracy = best_rf_model.score(X_test, y_test)

    # 保存模型和标准化器和权重
    best_rf_weights = best_rf_model.feature_importances_
    joblib.dump(best_rf_model, f'best_rf_model_{index}.pkl')
    # joblib.dump(scaler, f'scaler_{index}.pkl')
    np.save(f'best_rf_weights_{index}.npy', best_rf_weights)

    # 计算混淆矩阵和其他指标
    predictions = best_rf_model.predict(X)
    conf_matrix = confusion_matrix(y, predictions)

    # 确保是二分类问题
    if conf_matrix.shape == (2, 2):
        tn, fp, fn, tp = conf_matrix.ravel()
        sensitivity = recall_score(y, predictions)
        specificity = tn / (tn + fp)
        accuracy = accuracy_score(y, predictions)
        false_positive_rate = fp / (fp + tn)
        best_rf_weights = "\t".join([str(weight) for weight in best_rf_weights])
        print(f"{best_rf_accuracy:.4f}\t{best_rf_weights}\t{tn}\t{fp}\t{fn}\t{tp}\t{sensitivity:.4f}\t{specificity:.4f}\t{accuracy:.4f}\t{false_positive_rate:.4f}")
    else:
        print("Error: Confusion matrix is not 2x2")


if __name__ == '__main__':
    # file_path = sys.argv[1]
    # 读取数据
    file_path_list = [
        '/cygene4/pipeline/check_sequence_penalty_score/Pooled.11samples.txt',
        '/cygene4/pipeline/check_sequence_penalty_score/Pooled.9.longSequence.samples.txt',
        '/cygene4/pipeline/check_sequence_penalty_score/Pooled.20.mixed.samples.txt',
    ]
    for index, file_path in enumerate(file_path_list, start=4):
        data = pd.read_csv(file_path, sep="\t", low_memory=False)
        main(data, index)
