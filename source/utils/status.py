import pandas as pd


def out_status(out_index):
    col = ['status']
    record_lt = [{'status': str(out_index)}]
    df = pd.DataFrame(record_lt, columns=col)
    df.to_csv('status.csv')