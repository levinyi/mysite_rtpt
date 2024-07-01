import pandas as pd
from sklearn.linear_model import LogisticRegression

# Load the data
data = pd.read_csv('/cygene4/pipeline/check_sequence_penalty_score/Pooled_Data_P243p30A10-A11-A12-A08-3p31A21.csv')
# Extract features and labels
X = data[['local_gc_content_penalty_score', 'W12S12_motifs_penalty_score', 'long_repeats_penalty_score', 'homopolymers_penalty_score']]
y = data['MTP_NGS']

# Train the logistic regression model
model = LogisticRegression()
model.fit(X, y)

# Get the weights
W1, W2, W3, W4 = model.coef_[0]

# Calculate penalty scores
penalty_scores = X.iloc[:, 0] * W1 + X.iloc[:, 1] * W2 + X.iloc[:, 2] * W3 + X.iloc[:, 3] * W4

print("Weights:", W1, W2, W3, W4)
print("Penalty Scores:", penalty_scores)
