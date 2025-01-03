import csv 
import pandas as pd 
import argparse

def read_csv(file_path):

    return pd.read_csv(file_path)



def clean_data(data):
    #align right rows to corresponding columns
    data = data.transpose()
    data = data.reset_index()
    data.columns = data.iloc[0]
    data = data.drop(0)
    







def main():
    parser = argparse.ArgumentParser(description='Preprocess data')
    parser.add_argument("-i",'--input', type=str, help='Input file path')
    parser.add_argument("-o",'--output', type=str, help='Output file path')



    args = parser.parse_args()
    data = read_csv(args.input)
    data = clean_data(data)
    data.to_csv(args.output, index=False)
    

if __name__ == '__main__':
    main()
