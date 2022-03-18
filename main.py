from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import math
import random
import numpy as np
import statistics
from sklearn.preprocessing import LabelEncoder

# read the dataset

df = pd.read_csv("train.csv")

df = df.fillna(df.mode().iloc[0])

del df['Loan_ID']

genderEncoder = LabelEncoder()
marriedEncoder = LabelEncoder()
educationEncoder = LabelEncoder()
employedEncoder = LabelEncoder()
propertyEncoder = LabelEncoder()
loanStatusEncoder = LabelEncoder()

df['Gender'] = genderEncoder.fit_transform(df["Gender"])
df['Married'] = marriedEncoder.fit_transform(df['Married'])
df['Education'] = educationEncoder.fit_transform(df['Education'])
df['Self_Employed'] = employedEncoder.fit_transform(df['Self_Employed'])
df['Property_Area'] = propertyEncoder.fit_transform(df['Property_Area'])
df['Loan_Status'] = loanStatusEncoder.fit_transform(df['Loan_Status'])

df = df.values.tolist()


# split the dataset into test set and train set
def split_dataset(dataset, ratio):
    train_size = int(len(dataset) * ratio)
    train_set = []
    test_set = list(dataset)
    while len(train_set) < train_size:
        index = random.randrange(len(test_set))
        train_set.append(test_set.pop(index))
    return [train_set, test_set]


# split the dataset by class values & return a dictionary
def separate_by_class(dataset):
    separated = dict()
    for i in range(len(dataset)):
        vector = dataset[i]
        class_value = vector[-1]
        if class_value not in separated:
            separated[class_value] = list()
        separated[class_value].append(vector)
    return separated


# calculate mean, standard deviation and count for each column in dataset
def summarize_dataset(dataset):
    summaries = [(statistics.mean(column), statistics.stdev(column), len(column)) for column in zip(*dataset)]
    del (summaries[-1])
    return summaries


# split dataset by class then calculate statistics for each row
def summarize_by_class(dataset):
    separated = separate_by_class(dataset)
    summaries = {}
    for class_value, rows in separated.items():
        summaries[class_value] = summarize_dataset(rows)
    return summaries


# calculate the gaussian probability distribution function for x
def calculate_probability(x, mean, stdev):
    exponent = math.exp(-(math.pow(x - mean, 2) / (2 * math.pow(stdev, 2))))
    return (1 / (math.sqrt(2 * math.pi) * stdev)) * exponent


# calculate the probabilities of predicting each class for a given data
def calculate_class_probabilities(summaries, input):
    probabilities = dict()
    for class_value, class_summaries in summaries.items():
        probabilities[class_value] = 1
        for i in range(len(class_summaries)):
            mean, standard_deviation, _ = class_summaries[i]
            probabilities[class_value] *= calculate_probability(input[i], mean, standard_deviation)
    return probabilities


# predict the class for a given data
def predict(summaries, input):
    probabilities = calculate_class_probabilities(summaries, input)
    best_label, best_prob = None, -1
    for class_value, probability in probabilities.items():
        if best_label is None or probability > best_prob:
            best_prob = probability
            best_label = class_value
    return best_label


def get_predictions(summeries, test_set):
    predictions = []
    for i in range(len(test_set)):
        predictions.append(predict(summeries, test_set[i]))
    return predictions


def get_accuracy(test_set, predictions):
    correct = 0
    for x in range(len(test_set)):
        if test_set[x][-1] == predictions[x]:
            correct += 1
    return (correct / float(len(test_set))) * 100


split_ratio = 0.95
train_set, test_set = split_dataset(df, split_ratio)
print("Split {0} rows into train :- {1} and test :- {2} rows.".format(len(df), len(train_set), len(test_set)))

# prepare model
summaries = summarize_by_class(train_set)
predictions = get_predictions(summaries, test_set)

accuracy = get_accuracy(test_set, predictions)
print("Accuracy :- {0}%".format(accuracy))

app = FastAPI()


class request_body(BaseModel):
    Gender: str
    Married: str
    Dependents: int
    Education: str
    Self_Employed: str
    ApplicantIncome: int
    CoapplicantIncome: int
    LoanAmount: int
    Loan_Amount_Term: int
    Credit_History: int
    Property_Area: str


@app.post("/api/v1/predict")
def predict(request_body: request_body):
    user_data = [genderEncoder.transform(request_body.Gender), marriedEncoder.transform(request_body.Married), request_body.Dependents, educationEncoder.transform(request_body.Education),
                 employedEncoder.transform(request_body.Self_Employed), request_body.ApplicantIncome, request_body.CoapplicantIncome,
                 request_body.LoanAmount, request_body.Loan_Amount_Term, request_body.Credit_History,
                 propertyEncoder.transform(request_body.Property_Area)]
    print(user_data)
    user_data = np.reshape(user_data, (1, 11))
    predicted_data = get_predictions(summaries, user_data)
    return predicted_data
