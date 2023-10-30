#!/usr/bin/env python3.12
# assess_latency.py
import joblib
import pandas as pd
import pandas.errors
from rich.console import Console

from SQLWasp.ai_matrix import AiTrainer

c = Console()
trained_model_file_path = "data/input/ai/net_watcher.pkl"
input_data_csv_file_path = "data/input/ai/assess_latency/assess_latency.csv"
outfile_file_path = "data/output/assess_latency/assess_latency.csv"

# sample_data = pd.DataFrame(
#     {'GET Sent': 10,
#      'Ping Sent': 10,
#      'Delay': 0.0,
#      'Threshold': 0.1,
#      'Ping Threshold': 0.1,
#      'Std Dev Threshold': 0.1,
#      'Ping Std Dev Threshold': 0.1,
#      'GET Latency Average': 4.263334250450134,
#      'Min GET Latency': 4.092668056488037,
#      'Max GET Latency': 4.369938850402832,
#      'Ping Latency Average': 0.10160462856292725,
#      'Min Ping Latency': 0.05791211128234863,
#      'Max Ping Latency': 0.34255385398864746,
#      'Std Dev': 0.09659887594529501,
#      'Ping Std Dev': 0.0852839563187572,
#      '1xx': 0,
#      '2xx': 10,
#      '3xx': 0,
#      '4xx': 0,
#      '5xx': 0,
#      'Test Final Evaluation': 1.0,
#      'Test Passed': 1}, index=[1]
# )

# for row in df.iterrows():
#     predictions = clf.predict(row)
#     c.print(f"Predictions: {predictions}")


class AIControl:
    def __init__(self, trained_model_path, input_data_csv_path, outfile_path):
        self.c = Console()
        self.trained_model_path = trained_model_path
        self.input_data_csv_path = input_data_csv_path
        self.outfile_path = outfile_path
        self.clf = None
        self.df = None
        self.predictions = None

    def load_trained_model(self):
        self.clf = joblib.load(self.trained_model_path)

    def load_df(self):
        try:
            self.df = pd.read_csv(self.input_data_csv_path)
        except ValueError:
            pass
        else:
            self.df.dropna()
            self.df.drop_duplicates()
            self.df = self.df.drop(columns=["Test Passed", "Test Final Evaluation"], axis=1)

    def predict(self):
        try:
            self.predictions = self.clf.predict(self.df)
            # c.print(f"Predictions: {self.predictions}")
        except ValueError:
            pass

    def train_model(self):
        ai_trainer = AiTrainer(self.outfile_path, self.trained_model_path)
        ai_trainer.run()

    def run(self):
        self.load_trained_model()
        self.load_df()
        self.predict()

