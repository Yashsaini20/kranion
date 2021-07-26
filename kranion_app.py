from numpy.core.fromnumeric import mean
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import math
import streamlit as st
import plotly.express as px
from datetime import datetime


import warnings
warnings.filterwarnings("ignore")

st.title('Kranion')
st.subheader('**Upload Cycles Data**')
st.write('***Data format***') 
st.write('Data file should be .csv file and has only *one column*, *without column names*')
uploaded_file = st.file_uploader(" ",key="cycle_data")

st.subheader('**Upload Points Data**')
st.write('***Data format***') 
st.write('Data file should be .csv file and has a total of *6 columns*, *without column names*')

uploaded_file2 = st.file_uploader(" ", key="points_data")

if uploaded_file is not None:

  data = pd.read_csv(uploaded_file,header= None, skip_blank_lines=False)

if uploaded_file2 is not None:

  df2 = pd.read_csv(uploaded_file2,header= None, skip_blank_lines=False)
#data
#xls = pd.ExcelFile('/content/drive/MyDrive/Kranion/Raw Game And Points Data Example - July 7th.xlsx',)
#data = pd.read_excel(xls,header= None, skip_blank_lines=False) #reading first tab
#df2 = pd.read_excel(xls,1,header= None, skip_blank_lines=False) #reading 2nd tab for points/scores

#data = pd.read_csv('/content/drive/MyDrive/Kranion/Raw Game Data.csv',header= None, skip_blank_lines=False)
#data

#df2 = pd.read_csv('/content/drive/MyDrive/Kranion/Points Data.csv', header= None, skip_blank_lines=False)
#df2.head()

#data.isnull().sum()

#data.drop([0],inplace=True)
#data.reset_index(drop=True,inplace=True)
#data

# ( FOR TWO COLUMN DATA )

# #Dataset for cycle-start
# dataset = data[1]
# dataset=pd.DataFrame(dataset)
# print(len(cycle_data))

# # del(data[1])
# print(dataset)

# Split data in different cycles
cycle_data = np.split(data, *np.where(data[0].str.startswith("NaN")))
#Dropping all NaN values of cycle-start dataset
# dataset.dropna(inplace=True)
# dataset.reset_index(drop=True, inplace=True)
# print(dataset)

for i in range(0,len(cycle_data)):
    cycle_data[i] = cycle_data[i].dropna(how='all')

# print(cycle_data[0])

#print(cycle_data)

cycle_points_data = np.split(df2, *np.where(df2[0].str.startswith("NaN")))
#print(len(cycle_points_data))  #it should be equal to len(cycle_data)
#print(len(cycle_data))

#print(cycle_points_data[1])

## Removing NaN rows

for i in range(0,len(cycle_points_data)):
    cycle_points_data[i] = cycle_points_data[i].dropna(how='all')

# Remove incomplete cycles(when game closed inbetween the run)
# Taking all possible cases of game end
game_end_states = ['PlayerStopped','CycleStopCheck','DragsterCrashed']    # States needed   # CycleStopCheck state occurs when 3 times failure in target game or either user hit the wall
joined_end_states = '|'.join(game_end_states)

for cycle in cycle_data:
  if cycle[0].str.contains(joined_end_states).any():
    pass
  else:
    del(cycle_points_data[cycle_data.index(cycle)])
    del(cycle)

# Function for extracting a state time

def list_of_state_time_needed(state_start_with,indexofthe_value,symbol_string):
    required_code=[]
    required_value_list=[]
    states_length = []
    
    for cycle in cycle_data:
        required_code.append(cycle[cycle[0].str.startswith(state_start_with)])
        
        
    for one_cycle in required_code:
        states = one_cycle[0].values.tolist()

        states_length.append(len(states))
    
        if not states:
            required_value_list.append(None)
        else:
            for state in states:
                all_state_values = re.split(symbol_string,state)
                required_value_list.append(int(all_state_values[indexofthe_value]))
    
    return(required_value_list,states_length)

#Extract obstacle and obstacle-times for all states
# Here spliting on ~ and @ , statename-?ObstacleSpawn , index of the value in the list after spliting-4

objectspawn_time,states_length_objectspawn = list_of_state_time_needed("?ObstacleSpawn",4,"~|@")
obstacleremoved_time,states_length_obstacleremoved = list_of_state_time_needed("?ObstacleCorrectlyDestroyed",4,"~|@")

#Assign None to "time" when player gets hit by FIRST obstacle 

for j in range(len(states_length_objectspawn)):
    if (states_length_objectspawn[j] == 1 and states_length_obstacleremoved[j] == 0):
        objectspawn_time[sum(states_length_objectspawn[:j])] = None

#How many times obstacle appeared and how many times it gets destroyed in a particular state

#print(states_length_objectspawn,states_length_obstacleremoved,"\n")

# Time taken of each obstacle arrival and time taken for removing each obstacle
#print(objectspawn_time,len(objectspawn_time),"\n")
#print(obstacleremoved_time,len(obstacleremoved_time),"\n")

#Extracting time when crosshair starts moving and when player pressed stop button

crosshair_start_moving, states_length = list_of_state_time_needed("?TriggerStartMoving",4,"~|@")
stop_button_response, states_length = list_of_state_time_needed("?TriggerCheckResult",4,"~|@")
    
#print(crosshair_start_moving,stop_button_response)

# Function For substracting 2 lists: list2 - list1

def list_subtract(list1,list2):
    list_subtracted = [round(time2 - time1,2) if (time1 and time2) != None else None for time1,time2 in zip(list1,list2)]
    return list_subtracted


# Getting player response time on crosshair game section

player_response_stop = list_subtract(crosshair_start_moving,stop_button_response)
#print(player_response_stop)

# Remove time-record of "object-spawn" when it hit the obstacle, as it is of no use in recording response
# Also have to make the length of new_objectspawn_time and obstacleremoved_time equal, to perform operations

def remove_hit_spawns(objectspawn_time,states_length_objectspawn,states_length_obstacleremoved):
    
    length = 0
    del_count = 0
    for length1,length2 in zip(states_length_objectspawn,states_length_obstacleremoved):
        diff = length1-length2
        length += length1

        if diff != 0 and length1 != 1:
            del(objectspawn_time[length-del_count-1:length-del_count])
            del_count += 1
        
    return(objectspawn_time)

new_objectspawn_time = remove_hit_spawns(objectspawn_time,states_length_objectspawn,states_length_obstacleremoved)


#print(len(new_objectspawn_time) == len(obstacleremoved_time),"\n")
#print(new_objectspawn_time,len(new_objectspawn_time))

# Have to separate all time values by cycle:

def list_by_cycle(old_list,states_length):
    
    add = 0
    new_objectspawn_time= []
    for length in states_length:
        if length == 0:
            length = 1
        else:
            pass
        count = length
        length += add
        new_objectspawn_time.append(old_list[add:length])
        add += count
    
    return(new_objectspawn_time)

new_objectspawn_time = list_by_cycle(new_objectspawn_time,states_length_obstacleremoved)
new_obstacleremoved_time = list_by_cycle(obstacleremoved_time,states_length_obstacleremoved)
#print(new_objectspawn_time,"\n\n",new_obstacleremoved_time)

# Getting the player response time by substracting obstacle removal time and button press time

player_response_destroy = [[time2 - time1 if (time1 and time2) != None else None for time1,time2 in zip(list1,list2)] for list1,list2 in zip(new_objectspawn_time,new_obstacleremoved_time)]
#print(player_response_destroy)

# Function for extracting z-axis positions of dragster and wall at the end of player-stop state

def list_of_positions_needed(state_start_with,indexofthe_value,symbol_string):
    required_code=[]
    required_value_list=[]
    states_length = []
    
    for cycle in cycle_data:
        required_code.append(cycle[cycle[0].str.startswith(state_start_with)])
    
    for one_cycle in required_code:
        states = one_cycle[0].values.tolist()
        

        if not states:
            required_value_list.append(None)
        else:
            for state in states:
                object_data = re.split(symbol_string,state)
                object_values = re.split("~",object_data[indexofthe_value])
                required_value_list.append(float(object_values[-1]))
    
    return(required_value_list)




endstate_player = list_of_positions_needed("?PlayerStopped",15,"\$")

endstate_wall = list_of_positions_needed("?PlayerStopped",17,"\$")


# Substracting the 2 list to get the distance between wall and dragster at the end of the game

player_response_wall = list_subtract(endstate_player,endstate_wall)
#print(player_response_wall)

#Extracting all game ids

all_game_ids = []
for i in range(0,len(cycle_data)):
    all_game_ids.append(cycle_data[i].iloc[0,0])
#print(all_game_ids)

# # Extracting time of play     ( FOR TWO COLUMN DATA )

# required_code=[]
# time_list=[]

# for cycle in cycle_data:   # Each "cycle" will be a dataframe
#   required_code.append(cycle[1].dropna())
    
# for one_cycle in required_code:
#   states = one_cycle.values.tolist()
        
#   for state in states:
#     all_state_values = re.split("~|=",state)  # Spliting the string on ~ and = signs
#     datetime_object = datetime.strptime(all_state_values[3], '%H:%M:%S').time()
#     time_list.append(datetime_object)
    


# print(len(time_list),"\n",type(time_list[0]))

# # Extracting time of play    ( FOR ONE COLUMN DATA )

required_code=[]
cycle_start_time=[]
    
for cycle in cycle_data:
  required_code.append(cycle[cycle[0].str.startswith("?CycleAdjustComplexity")])
        
        
for one_cycle in required_code:
  states = one_cycle[0].values.tolist()

  for state in states:
       all_state_values = re.split("=",state)  # Spliting the string on = sign
       datetime_object = datetime.strptime(all_state_values[1], '%H:%M:%S').time()  # Time format - Hour: Minute: Seconds
       cycle_start_time.append(datetime_object)

#print(len(cycle_start_time),"\n",type(cycle_start_time[0]))

## Extracting level of cycle
cycle_level =[]

for cycle in cycle_data:
  required_state = cycle[cycle[0].str.startswith("?CycleAdjustComplexity")][0]  #Getting the required value from dataframes and changing the type to pandas.series by extracting first column

  for i in required_state.str.split('~').str[0]:    # Spliting the state string on "~" and extracting first value i.e. full state-name 
    cycle_level.append(int(''.join([level for level in i if level.isdigit()])))

#cycle_level

#Extracting crosshair and target coordinates
#this data will be extracted from state ?TriggerCheckResult
#for cross hair $KAITrigger2D_2D~1954.408~1376.35~0.
#for target $KAITriggerTarget_2D~1920~1080~0. 

required_code=[]
x_crosshair=[]
y_crosshair=[]
x_target=[]
y_target=[]
for cycle in cycle_data:
  required_code.append(cycle[cycle[0].str.startswith("?TriggerCheckResult")])

states=[]

for one_cycle in required_code:
 states.append(one_cycle[0].values.tolist())

#print(states)
#print(len(states))

for state in states:
       all_state_values = re.split("~",state[0])  # Spliting the string on ~ sign
       x_crosshair.append(float(all_state_values[-3]))
       y_crosshair.append(float(all_state_values[-2]))
       x_target.append(float(all_state_values[-18]))
       y_target.append(float(all_state_values[-17]))

#print(len(x_crosshair))
#print(len(y_crosshair))
#print(len(x_target))
#print(len(y_target))

distance=[]

for i in range(0, len(x_crosshair)) :
  distance.append(math.sqrt((x_target[i]-x_crosshair[i])**2)+((y_target[i]-y_crosshair[i])**2))

#print(distance)


predloading = []   
guessing = []

obstacle_states = ['PrepareObstacleSpawn','AmmoLoaded','\?AmmoFired']    # States needed
regstr = '|'.join(obstacle_states)     # "|" work as "or" in regex therefore joing on "|"

for cycle in cycle_data:
  k = cycle[cycle[0].str.contains(regstr)][0]    # k is a cycle of type Pandas-Series 
  k.reset_index(inplace=True,drop=True)          # Normal indexing from 0
  for i in range(len(k)):
    if "PrepareObstacleSpawn" in k[i]:
      k[i] = "ObstacleSpawn"
    elif "AmmoLoaded" in k[i]:
      k[i] = "Loaded"
    else:
      k[i] = "Fired"

  for i in range(len(k)):
    try:
      if ((k[i] == "Loaded") & (k[i+1]=="ObstacleSpawn")):   # Predloding case- if a user loaded a weapon just before the spawn state
        predloading.append(1)                                # 1 - preloading occured for objectspawn
        if (k[i+2]=="Fired"):   
           guessing.append('T') 
        else :
            guessing.append('F')
      elif ((k[i] == "ObstacleSpawn") & (k[i+1]=="Loaded")):   # Non-Preloading case - if a user loaded a weapon just after the spawn state
        predloading.append(0)                                 # 0 - preloading dosen't occured for objectspawn
        guessing.append(0)

    except:       # if k[i] is the last state then k[i+1] will not exist, therefore using try-except
      continue


#print(predloading,"\n",len(predloading))   # Length should be equal to total number of objectspawn in the data



predloading_by_cycle = list_by_cycle(predloading,states_length_objectspawn)    #Function defined above to separate values according to cycles
#print(predloading_by_cycle)
guessing_by_cycle = list_by_cycle(guessing,states_length_objectspawn)    #Function defined above to separate values according to cycles
#print(guessing_by_cycle)

no_of_times_ammo_preloaded_4_each_cycle = []

for i in range(0,len(predloading_by_cycle)):
  no_of_times_ammo_preloaded_4_each_cycle.append(sum(predloading_by_cycle[i]))

true_guessing_count =[]

for i in range(0,len(predloading_by_cycle)):
  count = 0
  for q in guessing_by_cycle[i] :
    if q == 'T' :
      count = count+1
  true_guessing_count.append(count)

# In both the csv files, intersection is Cycle GUID(CycleGUID in points csv(3rd column) and CYCLEGUID in cycle csv, last row of each cycle)

total_score = []

for i in range(0, len(cycle_points_data)):
 total_score.append(cycle_points_data[i][3]) #extracting the score amount


#extracting scores of each state for a cycle and storing them as total score

for i in range(len(total_score)):
  sum_score=0
  for single_state_score in total_score[i]:
    s =  int(single_state_score[9:])
    sum_score = sum_score + s

  total_score[i] = sum_score
 
print(total_score)

#Assigning numbers will be helpful in plotting
#Arrow Accuracy & Speed = 1		
#Time To Press Gearbox = 2
#Obstacle Handling = 3
#Wall Stopping = 4
score_states = []


for i in range(0, len(cycle_points_data)):
  score_states.append(cycle_points_data[i][5]) #extracting the score amount


no_of_times_obstacle_appeared = []

for i in range(0, len(player_response_destroy) ) :
   no_of_times_obstacle_appeared.append(len(player_response_destroy[i]))

#if player_response_destroy[i] will be ['None'], then also no_of_times_obstacle_appeared will be 1, because obstacle appeared, but player did not explode it

for i in range(0, len(player_response_wall)):
  if player_response_wall[i] == 'NaN':
    no_of_times_obstacle_appeared[i] = no_of_times_obstacle_appeared[i]+1 #obstacle appeared and car crashed

# Columns for the dataframe
extracted_data = {
    "Game ID" : all_game_ids,
    "Target Response Time(ms)" : player_response_stop,
    "No. of times obstacle appeared" : no_of_times_obstacle_appeared,
    "Explosion Response Times(ms)" : player_response_destroy,
    "Ammo preloaded?(1 = Yes)" : predloading_by_cycle,
    "Guess true?" : guessing_by_cycle,
    "No_of_times_ammo_preloaded"  : no_of_times_ammo_preloaded_4_each_cycle,
    "No_of_correct_guesses" : true_guessing_count,
    "Wall Response (distance)" : player_response_wall,
    "Time of Play (hr:min:s)" : cycle_start_time,
    "Distance b/w crosshair nd target" : distance,
    "Cycle Level" : cycle_level,
    "Total Score" : total_score
}

df = pd.DataFrame(extracted_data)

#print(df.info())
#df
#GameId is unique to each player

#df['Game ID'].unique()

cycle_count = df['Game ID'].value_counts()
less_count = cycle_count[cycle_count<2].index.values
for k in range(len(less_count)):
  df.drop(df[df['Game ID'] == less_count[k]].index,inplace=True)
  df.reset_index(drop=True,inplace=True)
  
#df.info()

#storing unique player code
player_id = df['Game ID'].unique()
#df['Game ID'].nunique()

player_no = []
count = []
for i in range(1, len(player_id)+1):
  player_no.append(i) #assign unique no. to each code for readability 
  count.append(0)
#player_no

player_details = pd.DataFrame()
player_details['player_id'] = player_id
player_details['player_no'] = player_no #assign unique no. to each code for readability 
player_details['no_of_times_played'] = count #total no. of games played by each player will be stored in it

#assignin unique no. to each code to enhance readability, unique no. corresponding to each player from DataFrame 'player_details' is assigned to "Game ID"
j=0
for p in df['Game ID'] :
  for q in range(0,len(player_details)) :
    if p == player_details['player_id'][q]:
      df['Game ID'][j] = player_details['player_no'][q]
      player_details['no_of_times_played'][q] = player_details['no_of_times_played'][q]+1 #counting the no. of games played by each player
  j=j+1

st.subheader('**Cycle Data**')
st.table(df)

st.subheader('**Player Details**')
st.table(player_details)

#player_details['no_of_times_played'].sum() #it should be equal to the total no. of rows in df

# Function for plotting response value with a Game ID
def value_vs_cycle(column):
    plt.clf()
    sns.set()
    plt.figure(figsize=(10,8)) 
    plot = sns.lineplot(data=df_game,x= df_game.index,y=column,hue="Game ID",markers=["o"],style='Game ID',palette = 'hot')
    plt.xticks(np.arange(0, len(df_game)+1, 1))
    plt.margins(0.05)
    plt.xlabel("Cycle Number")
    #plt.show()
    st.pyplot(plt.show())
    

        


# Grouped df on unique values of Game ID
df_grouped = df.groupby('Game ID')

# Input from user(Game ID) to plot against the responses
game_num = int(input("Enter the Game ID for visualizing the trend of cycles: "))
df_game = df_grouped.get_group(game_num)
df_game.reset_index(drop=True,inplace=True)

#PLOT
value_vs_cycle('Target Response Time(ms)')
value_vs_cycle('Wall Response (distance)')

# Data of first time played and last time played

last = df_grouped.last()
first = df_grouped.first()

df_response_target = pd.DataFrame()
df_response_wall = pd.DataFrame()

df_response_target['first_time'] = first['Target Response Time(ms)']
df_response_wall['first_time'] = first['Wall Response (distance)']

df_response_target['last_time'] = last['Target Response Time(ms)']
df_response_target.reset_index(inplace=True)

df_response_wall['last_time'] = last['Wall Response (distance)']
df_response_wall.reset_index(inplace=True)

#df_response_wall

# Function to plot interactive plots using Plotly Express
def interactive_plot(df, title):
  fig = px.line(title = title)
  for i in df.columns[1:]:
    fig.add_scatter(x = df['Game ID'], y = df[i], name = i)
  st.plotly_chart(fig)

interactive_plot(df_response_target, 'Target Response Time(ms)')
interactive_plot(df_response_wall, 'Wall Response (distance)')

# Frequency Plot

fig, ax = plt.subplots()
plt.xlabel('Game ID')
plt.ylabel('Number of Times Played')
plt.title('Frequency of playing')
plt.xticks(np.arange(0, len(player_details)+1, 1))
plt.yticks(np.arange(0, max(player_details['no_of_times_played'])+1, 1))
ax.hist(df_response_target['Game ID'], bins=len(player_details))
st.pyplot(fig)


mean_responses = df_grouped.mean()



fig, ax = plt.subplots()
plt.xlabel('Mean Target Response time')
plt.ylabel('Number of Times Played')
plt.yticks(np.arange(0, max(player_details['no_of_times_played'])+1, 1))
ax.scatter(mean_responses['Target Response Time(ms)'],player_details['no_of_times_played'], alpha = 0.5)
st.plotly_chart(fig)

#distance vs target response time

fig, ax = plt.subplots()
plt.xlabel('Target Response time')
plt.ylabel('Distance b/w crosshair and target')
plt.yticks(np.arange(0, max(df['Distance b/w crosshair nd target'])+1, 1))
ax.scatter(df['Target Response Time(ms)'],df['Distance b/w crosshair nd target'], alpha = 0.5)
st.plotly_chart(fig)

#mean explosion response time vs total_no_of_times_preloaded
mean_of_response_time = []

for list in df['Explosion Response Times(ms)']:
  mean_of_response_time.append(mean(list))

fig, ax = plt.subplots()
plt.xlabel('Mean Explosion Response time')
plt.ylabel('No. of times ammo preloaded')
plt.yticks(np.arange(0, max(df['No_of_times_ammo_preloaded'])+1, 1))
ax.scatter(mean_of_response_time,df['No_of_times_ammo_preloaded'], alpha = 0.5)
st.plotly_chart(fig)

#mean response time vs correct guess
fig, ax = plt.subplots()
plt.xlabel('Mean Explosion Response time')
plt.ylabel('No. of times correct ammo preloaded(correct guess)')
plt.yticks(np.arange(0, max(df['No_of_correct_guesses'])+1, 1))
ax.scatter(mean_of_response_time,df['No_of_correct_guesses'], alpha = 0.5)
st.plotly_chart(fig)



