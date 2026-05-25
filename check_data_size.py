import pandas as pd

def check_data_size():
    df = pd.read_csv('outputs/extract_results/records_validated.csv')
    chains = pd.read_csv('outputs/event_chain/event_chains.csv')
    
    print('最终数据规模:')
    print(f'  总记录数: {len(df)}')
    print(f'  公告类型数: {len(df["ann_type"].unique())}')
    print(f'  事件链总数: {len(chains)}')
    print(f'  完整事件链: {len(chains[chains["complete"] == True])}')
    print(f'  不完整事件链: {len(chains[chains["complete"] == False])}')
    
    print('\n公告类型分布:')
    print(df['ann_type'].value_counts())
    
    print('\n事件链类型分布:')
    print(chains['event_type'].value_counts())

if __name__ == '__main__':
    check_data_size()
