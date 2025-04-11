import os, sys, glob, re
import pandas as pd
from datetime import datetime, date

class AllTransactions():
    def __init__(self, dataDir) -> None:
        self.dataDir = dataDir
        self.set_trans_data()

    def set_trans_data(self):
        self.trans = {'Summary' : None}
        self.credit_cards = []
        for trans_file in glob.glob(self.dataDir + 'transactions_*.csv'):
            key = re.match(r'transactions_(.*)\.csv', trans_file.split('/')[-1]).group(1).replace('_',' ')
            self.trans[key] = self.Tranascations(self, csv_file=trans_file)
            if len(key.split()) > 1:
                self.credit_cards.append(key.split()[2])
        if len(self.trans) > 1:
            self.trans['Summary'] = self.Tranascations(self)

    class Tranascations():
        def __init__(self, allTransactions, csv_file=None) -> None:
            self.allTransactions = allTransactions

            self.df = pd.DataFrame()
            self.income_df = pd.DataFrame()
            self.name = "NA"
            self.months = [""]
            self.years = [""]

            if not csv_file and len(self.allTransactions.trans) > 0:
                self.df = pd.concat([self.allTransactions.trans[k].df for k in self.allTransactions.trans.keys() if self.allTransactions.trans[k]] , axis=0)
                self.income_df = pd.concat([self.allTransactions.trans[k].income_df for k in self.allTransactions.trans.keys() if self.allTransactions.trans[k]] , axis=0)

                # remove credit card transaction from banks that already got detailed transaction from credit cards websites
                for cc in self.allTransactions.credit_cards:
                    credit_card_regexp = '.*' + str(cc) + " - כרטיסי אשראי לי" + '.*'
                    self.df = self.df[~self.df.description.str.contains(credit_card_regexp ,regex=True)]
                self.df = self.df[~self.df.description.str.contains("העברה מהחשבון|עפ.י הרשאה כאל" ,regex=True)]
                self.name = "Summary"

                # if there is added_data.csv, append it to the df
                if os.path.isfile("./data/added_data.csv"):
                    print("Adding added_data.csv to the df")
                    added_data_df = pd.read_csv("./data/added_data.csv")
                    self.df = pd.concat([self.df, added_data_df], ignore_index=True)
                    
            elif not csv_file and len(self.allTransactions.trans) == 0: 
                self.name = "Summary"
                self.df = pd.DataFrame()
            else:
                self.df = pd.read_csv(csv_file)
                self.name = re.match(r'transactions_(.*)\.csv', csv_file.split('/')[-1]).group(1).replace('_',' ')
                self.income_df = self.df[self.df['chargedAmount'] > 0]
                self.df['chargedAmount'] = self.df[self.df['chargedAmount'] < 0]['chargedAmount'].apply(lambda x:x*-1)


            self.months = list(set([re.match(r'[0-9]+-([0-9]+)-[0-9]+.*',x).group(1) for x in self.df.date.to_list()]))
            self.months = [datetime.strptime(m, "%m") for m in self.months]
            self.months.sort()
            self.months = [datetime.strftime(m, "%m") for m in self.months]

            self.years = list(set([re.match(r'([0-9]+)-[0-9]+-[0-9]+.*',x).group(1) for x in self.df.date.to_list()]))
            self.years = [datetime.strptime(m, "%Y") for m in self.years]
            self.years.sort()
            self.years = [datetime.strftime(m, "%Y") for m in self.years]

