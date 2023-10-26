#!/usr/bin/env python3.12
# assess_latency.py
import joblib
import pandas as pd
from rich.console import Console
from sklearn.ensemble import RandomForestClassifier
# from sklearn.neighbors import KNeighborsClassifier
# from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

c = Console()

outfile_file_path = "data/output/assess_latency/assess_latency.csv"
trained_model_file_path = "data/input/ai/net_watcher.pkl"


class AiTrainer:
    def __init__(self, outfile_path, trained_model_path):
        self.c = Console()
        self.outfile_path = outfile_path
        self.trained_model_path = trained_model_path
        self.df = pd.DataFrame()
        self.X = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.clf = None
        self.y_pred = None
        self.accuracy = None
        self.report = None
        self.confusion_matrix = None

    def load_df(self):
        self.df = pd.read_csv(self.outfile_path)
        self.df = self.df.dropna()
        self.df = self.df.drop_duplicates()
        # df = pd.get_dummies(df, columns=['URL', 'Host'])
        # c.print(df)

    def split_data(self):
        self.X = self.df.drop(columns=["Test Passed", "Test Final Evaluation"], axis=1)
        self.y = self.df["Test Passed"]
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.2,
                                                                                random_state=42)

    def create_classifier(self):
        # clf = DecisionTreeClassifier(criterion="log_loss")
        # clf = KNeighborsClassifier(n_neighbors=2)
        self.clf = RandomForestClassifier(n_estimators=100, random_state=32)
        self.clf.fit(self.X_train, self.y_train)

    def dump_trained_model(self):
        joblib.dump(self.clf, self.trained_model_path)

    def predict(self):
        self.y_pred = self.clf.predict(self.X_test)

    def accuracy_report(self):
        self.accuracy = accuracy_score(self.y_test, self.y_pred)
        self.report = classification_report(self.y_test, self.y_pred)
        self.confusion_matrix = confusion_matrix(self.y_test, self.y_pred)

    def print_reports(self):
        self.c.print("[Accuracy]:", self.accuracy, "\n", style="green")
        self.c.print("[Report]: \n", self.report, style="green")
        self.c.print("[Confusion Matrix]: \n", self.confusion_matrix, style="green")

    def run(self):
        self.load_df()
        self.split_data()
        self.create_classifier()
        self.dump_trained_model()
        self.predict()
        self.accuracy_report()
        self.print_reports()
