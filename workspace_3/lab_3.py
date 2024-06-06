from spyre import server 
from download_csv import *
from data_cleaning import *
from replace import *
import matplotlib.pyplot as plt
import seaborn as sns

country = "UKR"
year_1 = 1982
year_2 = 2024
type_data = "Mean"

directory = "/home/kali/Desktop/data_analysis/workspace_2/lab_3_venv/data_csv"

PROVINCE_NAME_dict = {1: 'Вінницька',  2: 'Волинська',  3: 'Дніпропетровська',  4: 'Донецька',  5: 'Житомирська',
    6: 'Закарпатська',  7: 'Запорізька',  8: 'Івано-Франківська',  9: 'Київська',  10: 'Кіровоградська',
    11: 'Луганська',  12: 'Львівська',  13: 'Миколаївська',  14: 'Одеська',  15: 'Полтавська',
    16: 'Рівенська',  17: 'Сумська',  18: 'Тернопільська',  19: 'Харківська',  20: 'Херсонська',
    21: 'Хмельницька',  22: 'Черкаська',  23: 'Чернівецька',  24: 'Чернігівська',  25: 'Республіка Крим'}

clean_directory(directory)
download_csv(country, year_1, year_2, type_data, directory)
data_frames = read_data(directory)
data_frames_work = replace_function(data_frames)   

class Web_Application(server.App):
    title = "National Oceanic and Atmospheric Administration🌍 NOAA data vizualization" 
    inputs = [
        {
            "type": 'dropdown', 
            "label": 'NOAA data dropdown',
            "options": [{"label": 'Vegetation Condition Index (VCI)', "value": 'VCI'},
                        {"label": 'Temperature Condition Index (TCI)', "value": 'TCI'},
                        {"label": 'Vegetation Health (VHI)', "value": 'VHI'}],
            "key": 'index',
            "action_id": 'update_data'
        },
        {
            "type": 'dropdown',
            "label": 'Region',
            "options": [{"label": PROVINCE_NAME_dict[region], "value": region} for region in sorted(data_frames_work['PROVINCE_ID'].unique())],
            "key": 'region',
            "action_id": 'update_data'
        },
        {
            "type": 'text',
            "label": 'Range of weeks: (1 - 52)',
            "key": 'range_weeks',
            "value": '1 - 52',
            "action_id": 'simple_html_output'
        },
        {
            "type": 'text',
            "label": 'Range years',
            "key": 'range_year',
            "value" : '1982-2024',
            "action_id": 'update_data'            
        }
    ]

    controls = [
        {
            "type": "button",
            "id": "update_data",
            "label": "Get information"
        }
    ]
    
    tabs = ["Table", "Graph"]
    
    outputs = [
        {
            "type": "plot",
            "id": "plot",
            "control_id": "update_data",
            "tab": "Graph",
            "on_page_load": True
        },
        {
            "type": "table",
            "id": "table_id",
            "control_id": "update_data",
            "tab": "Table",
            "on_page_load": True
        }
    ] 
    
    def getData(self, params):
        index = params["index"]
        region = int(params["region"])
        range_weeks = params["range_weeks"]
        range_year = params["range_year"]
        
        province_name = PROVINCE_NAME_dict.get(region, "")
             
        if isinstance(range_year, list):
            year_1, year_2 = range_year
            week_1, week_2 = range_weeks
        else:
            year_1, year_2 = map(int, range_year.split('-'))
            week_1, week_2 = map(int, range_weeks.split('-'))
        
        data_frame = data_frames_work[(data_frames_work["PROVINCE_ID"] == region) & 
                                    (data_frames_work["Week"].between(week_1, week_2)) &
                                    (data_frames_work["Year"].between(year_1, year_2))][["PROVINCE_ID", "Year", "Week", index]]
        
        data_frame.insert(1, "PROVINCE_NAME", province_name)
        
        return data_frame

    def getPlot(self, params):
        df = self.getData(params).drop(['PROVINCE_ID'], axis=1)
        index = params["index"] 
        region = int(params["region"])    

        if df.empty:
            return plt.gcf()
        
        fig, axs = plt.subplots(2,  figsize=(20, 15)) 

        # Графік 1: Лінійний графік
        sns.lineplot(x='Week', y=index, data=df, label=index, marker='o',  ax=axs[0], linestyle='-', color='black')
        axs[0].set_title(f"Noaa data visualization {index} for {country}: region: {df.iloc[0]['PROVINCE_NAME']} ", fontsize=18,  color='black', weight='bold')  
        axs[0].set_xlabel("Week", fontsize=15,  color='black', weight='bold')  
        axs[0].set_ylabel(index, fontsize=15, color='black', weight='bold')   
        axs[0].grid(True, linestyle='--', alpha=0.95)
        axs[0].legend(fontsize=15)
        axs[0].tick_params(axis='both', which='major', labelsize=10, colors='black')  
        axs[0].set_xlim(df['Week'].min() - 1, df['Week'].max() + 1)    
        axs[0].set_ylim(df[index].min() * 0.9, df[index].max() * 1.1) 
        axs[0].annotate('Start', xy=(df['Week'].min(), df[index].min()), xytext=(df['Week'].min(), df[index].min() - 20),
                    arrowprops=dict(facecolor='red', shrink=0.05), fontsize=10, color='black', horizontalalignment='center')
        axs[0].annotate('End', xy=(df['Week'].max(), df[index].min()), xytext=(df['Week'].max(), df[index].min() - 20),
                    arrowprops=dict(facecolor='red', shrink=0.05), fontsize=10, color='black', horizontalalignment='center')

        # Графік 2: Теплова карта
        sns.heatmap(df.pivot(index="Week", columns="Year", values=index), cmap="Greens", annot=True, ax=axs[1])
        axs[1].set_title(f"Noaa data visualization {index} for {country}: region: {df.iloc[0]['PROVINCE_NAME']}", fontsize=18,  color='black', weight='bold')
        
        return fig



if __name__ == "__main__":
    app = Web_Application()
    app.launch(port=9999)
