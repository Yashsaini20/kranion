import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import math
import plotly.express as px
from datetime import datetime
import streamlit as st
from numpy.core.fromnumeric import mean
import base64
import io
import scipy.stats as sp

import warnings
warnings.filterwarnings("ignore")

def download_link(object_to_download, download_filename, download_link_text):
    
    #Generates a link to download the given object_to_download.

    #object_to_download (str, pd.DataFrame):  The object to be downloaded.
    #download_filename (str): filename and extension of file. e.g. mydata.csv, some_txt_output.txt
    #download_link_text (str): Text to display for download link.

    #Examples:
    #download_link(YOUR_DF, 'YOUR_DF.csv', 'Click here to download data!')
    #download_link(YOUR_STRING, 'YOUR_STRING.txt', 'Click here to download your text!')

    towrite = io.BytesIO()

    if isinstance(object_to_download,pd.DataFrame):
        object_to_download = object_to_download.to_excel(towrite, encoding='utf-8',index=False)
    towrite.seek(0)  # reset pointer
    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(towrite.read()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'





st.title('Kranion')
st.subheader('**Upload Cycles Data**')
st.write('***Data format***') 
st.write('Data file should be .csv file and has only *two column*, *without column names*')
uploaded_file = st.file_uploader(" ",key="cycle_data")
st.write("***!!!!UPLOAD FILE TO AVOID ERROR!!!!***")
st.subheader('**Upload Points Data**')
st.write('***Data format***') 
st.write('Data file should be .csv file and has a total of *6 columns*, *without column names*')

uploaded_file2 = st.file_uploader(" ", key="points_data")
st.write("***!!!!UPLOAD FILE TO AVOID ERROR!!!!***")

if uploaded_file is not None:

  data = pd.read_csv(uploaded_file,header= None, skip_blank_lines=False)

if uploaded_file2 is not None:

  df2 = pd.read_csv(uploaded_file2,header= None, skip_blank_lines=False)

#xls = pd.ExcelFile('/content/drive/MyDrive/Kranion/Raw Game And Points Data Example - July 7th.xlsx',)
#data = pd.read_excel(xls,header= None, skip_blank_lines=False) #reading first tab
#df2 = pd.read_excel(xls,1,header= None, skip_blank_lines=False) #reading 2nd tab for points/scores

#data = pd.read_csv('/content/drive/MyDrive/Kranion/Raw Game Data Final.csv',header= None, skip_blank_lines=False)
#data

#df2 = pd.read_csv('/content/drive/MyDrive/Kranion/Points Data Final.csv', header= None, skip_blank_lines=False)
#df2.info()

#data[0].isnull().sum()

#df2.isnull().sum() # this should be equal to data[0].isnull.sum()

#data.drop([0],inplace=True)
#data.reset_index(drop=True,inplace=True)
#data

# ( FOR TWO COLUMN DATA )

# #Dataset for cycle-start
dataset = data[1]
dataset=pd.DataFrame(dataset)
#print(len(cycle_data))

del(data[1])
#print(dataset)

# Split data in different cycles
cycle_data = np.split(data, *np.where(data[0].str.startswith("NaN")))
#Dropping all NaN values of cycle-start dataset
# dataset.dropna(inplace=True)
# dataset.reset_index(drop=True, inplace=True)
# print(dataset)

for i in range(0,len(cycle_data)):
    cycle_data[i] = cycle_data[i].dropna(how='all')

# print(cycle_data[0])

cycle_points_data = np.split(df2, *np.where(df2[0].str.startswith("NaN")))
#print(len(cycle_points_data))  #it should be equal to len(cycle_data)
#print(len(cycle_data))

#print(cycle_points_data[1])
#print(cycle_data[1])

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
    del(cycle_data[cycle_data.index(cycle)])

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
#print(objectspawn_time,len(objectspawn_time),"\n")

for j in range(len(states_length_objectspawn)):
    if (states_length_objectspawn[j] == 1 and states_length_obstacleremoved[j] == 0):
        objectspawn_time[sum(states_length_objectspawn[:j])] = None

#How many times obstacle appeared and how many times it gets destroyed in a particular state


#Time taken of each obstacle arrival and time taken for removing each obstacle
#print(objectspawn_time,len(objectspawn_time),"\n")
#print(obstacleremoved_time,len(obstacleremoved_time),"\n")

# Have to separate all time values by cycle:

def list_by_cycle(old_list,states_length):
    
    add = 0
    list_of_lists= []
    for length in states_length:
        if length == 0:
            length = 1
        else:
            pass
        count = length
        length += add
        list_of_lists.append(old_list[add:length])
        add += count
    
    return(list_of_lists)

#Extracting time when crosshair starts moving and when player pressed stop button

crosshair_start_moving, states_length_crosshair = list_of_state_time_needed("?TriggerStartMoving",4,"~|@")
stop_button_response, states_length_crosshair = list_of_state_time_needed("?TriggerCheckResult",4,"~|@")


#print(crosshair_start_moving,stop_button_response)

crosshair_start_moving = list_by_cycle(crosshair_start_moving,states_length_crosshair)
stop_button_response = list_by_cycle(stop_button_response,states_length_crosshair)

#print(crosshair_start_moving)
#print(stop_button_response)

# Function For substracting 2 lists: list2 - list1


## If list1 and list2 are lists-
def list_subtract(list1,list2):
    list_subtracted = [round(time2 - time1,2) if (time1 and time2) != None else None for time1,time2 in zip(list1,list2)]
    return list_subtracted


## If list1 and list2 are list of lists-
def list_of_lists_subtract(list1,list2):
  list_subtracted = [[time2 - time1 if (time1 and time2) != None else None for time1,time2 in zip(d1,d2)] for d1,d2 in zip(list1,list2)]
  return list_subtracted

player_response_stop = list_of_lists_subtract(crosshair_start_moving,stop_button_response)
#print(player_response_stop)

#### Issue test
#print(obstacleremoved_time.index(43759))

#print(objectspawn_time.index(54659))
# print(objectspawn_time.index(60206))
#print(obstacleremoved_time[730:740])
#print(objectspawn_time[688:700])

# Remove time-record of "object-spawn" when it hit the obstacle, as it is of no use in recording response
# Also have to make the length of new_objectspawn_time and obstacleremoved_time equal, to perform operations
#print(len(objectspawn_time), len(obstacleremoved_time),"\n")

def remove_hit_spawns(objectspawn_time,states_length_objectspawn,states_length_obstacleremoved):
    
    length = 0
    del_count = 0
    for length1,length2 in zip(states_length_objectspawn,states_length_obstacleremoved):
        diff = length1-length2
        length += length1

        if diff != 0 and length1 != 1:
            del(objectspawn_time[length-del_count-1])
            del_count += 1

    return(objectspawn_time)


new_objectspawn_time = remove_hit_spawns(objectspawn_time,states_length_objectspawn,states_length_obstacleremoved)


#print(len(new_objectspawn_time), len(obstacleremoved_time),"\n")
#print(new_objectspawn_time,len(new_objectspawn_time))

# ### Finding issue

# fdb = []

# for i in range(len(new_objectspawn_time)):
#   if (obstacleremoved_time[i] != None and new_objectspawn_time[i] != None):
#     if obstacleremoved_time[i] < new_objectspawn_time[i]:
#       fdb.append(i)
        
#     # if (new_obstacleremoved_time[i] == None and new_objectspawn_time[i][j] != None) or (new_obstacleremoved_time[i][j] != None and new_objectspawn_time[i][j] == None):
#     #   none.append(i)

# # print(fdb) 
# print(obstacleremoved_time[730:740],"\n",new_objectspawn_time[730:740])

new_objectspawn_time = list_by_cycle(new_objectspawn_time,states_length_obstacleremoved)
new_obstacleremoved_time = list_by_cycle(obstacleremoved_time,states_length_obstacleremoved)
#print(new_objectspawn_time,"\n\n",new_obstacleremoved_time)

# ### Finding issue
# negative = []
# none = []

# for i in range(len(new_objectspawn_time)):
#   for j in range(len(new_objectspawn_time[i])):
  
#     if (new_obstacleremoved_time[i][j] != None and new_objectspawn_time[i][j] != None):
#       if new_obstacleremoved_time[i][j] < new_objectspawn_time[i][j]:

#         negative.append(i)
        
#     if (new_obstacleremoved_time[i][j] == None and new_objectspawn_time[i][j] != None) or (new_obstacleremoved_time[i][j] != None and new_objectspawn_time[i][j] == None):
#       none.append(i)

# print(negative,"\n",none)   ## Cycle indexes

#print(new_objectspawn_time[174])
#print(new_obstacleremoved_time[174])

# Getting the player response time by substracting obstacle removal time and button press time

player_response_destroy = list_of_lists_subtract(new_objectspawn_time,new_obstacleremoved_time)
#print(player_response_destroy)

# Function for extracting z-axis end-positions of dragster and wall at the end of player-stop state
#state_start_with - state start name
#object_found - name of the object whose position we want
#symbol_string - split the state string on symbol_string

def list_of_positions_needed(state_start_with,object_found,symbol_string):
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
                del(object_data[0])                            # object_data[0] contained information of object at the start of the state, no need of it

                for end_object in object_data:
                  if end_object.find(object_found) != -1:
                    break
              
                object_values = re.split("~",end_object)       # Now end_object is the string containig information of required object at the end of the state
                required_value_list.append(float(object_values[-1]))  ## -1 for extracting z-axis location
    
    return(required_value_list)




endstate_player = list_of_positions_needed("?PlayerStopped","KAIPlayer_Player_1","\$")

endstate_wall = list_of_positions_needed("?PlayerStopped","KAIFinishLine_Instant_1","\$")


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

#print(cycle_level)

#extracting duration of each cycle

duration_of_each_cycle =[]
required_code =[]
for cycle in cycle_data:
  required_code.append(cycle[cycle[0].str.startswith("?CycleProcessTrackerPlayerData")])

states=[]

for one_cycle in required_code:
 states.append(one_cycle[0].values.tolist())

for state in states:
       all_state_values = re.split("~",state[0])
       #print(all_state_values,all_state_values[-2])
       duration_of_each_cycle.append(int(all_state_values[-2])/1000)

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

states_length = []

for one_cycle in required_code:
  states=one_cycle[0].values.tolist()
  states_length.append(len(states))

# print(states)
#print(len(states))


  for state in states:
    all_state_values = re.split("~",state)  # Spliting the string on ~ sign
    x_crosshair.append(float(all_state_values[-3]))
    y_crosshair.append(float(all_state_values[-2]))
    x_target.append(float(all_state_values[-18]))
    y_target.append(float(all_state_values[-17]))
        # if len(state) >1:
        #   print(states.index(state),len(state))

#print(len(x_crosshair))
#print(len(y_crosshair))
#print(len(x_target))
#print(len(y_target))

distance=[]

for i in range(0, len(x_crosshair)) :
  distance.append(round(math.sqrt((x_target[i]-x_crosshair[i])**2)+((y_target[i]-y_crosshair[i])**2),2))

#print(distance)
#print(len(distance))

distance_by_cycle = list_by_cycle(distance,states_length)
#print(distance_by_cycle)

#"""**Predloaded**"""

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
        guessing.append('0')

    except:       # if k[i] is the last state then k[i+1] will not exist, therefore using try-except
      continue


#print(predloading,"\n",len(predloading))   # Length should be equal to total number of objectspawn in the data



predloading_by_cycle = list_by_cycle(predloading,states_length_obstacleremoved)    #Function defined above to separate values according to cycles
#print(predloading_by_cycle)
guessing_by_cycle = list_by_cycle(guessing,states_length_obstacleremoved)    #Function defined above to separate values according to cycles
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

#"""### Points Dataframe Starting"""

total_score = []

for i in range(0, len(cycle_points_data)):
 total_score.append(cycle_points_data[i][3]) #extracting the score amount


tracker_id = []

for i in range(0, len(cycle_points_data)):
 tracker_id.append(cycle_points_data[i][1]) #extracting the score amount

#checking
#print(total_score[1])
#s=int(total_score[1][11][9:])
#print(s)
#print(type(s))

#extracting scores of each state for a cycle and storing them as total score

for i in range(len(total_score)):
  sum_score=0
  for single_state_score in total_score[i]:
    s =  int(single_state_score[8:])
    sum_score = sum_score + s

  total_score[i] = sum_score
 
#print(total_score, len(total_score))

#Assigning numbers will be helpful in plotting
#Arrow Accuracy & Speed = 1		
#Time To Press Gearbox = 2
#Obstacle Handling = 3
#Wall Stopping = 4
score_states = []


for i in range(0, len(cycle_points_data)):
  score_states.append(cycle_points_data[i][5]) #extracting the score amount

#score_states[0]

#extracting tracker ID
tracker_id_list = []
for i in range(len(tracker_id)):
  s = tracker_id[i].iloc[0]
  s = s[11:]
  tracker_id_list.append(s)

#print(tracker_id_list, len(tracker_id_list))

no_of_times_obstacle_appeared = []

for i in range(0, len(player_response_destroy) ) :
   no_of_times_obstacle_appeared.append(len(player_response_destroy[i]))

#if player_response_wall[i] will be ['None'], then also no_of_times_obstacle_appeared will be 1, because obstacle appeared, but player did not explode it

for i in range(0, len(player_response_wall)):
  if player_response_wall[i] == 'NaN':
    no_of_times_obstacle_appeared[i] = no_of_times_obstacle_appeared[i]+1 #obstacle appeared and car crashed

# print(len(all_game_ids))
# print(len(player_response_stop))
# print(len(no_of_times_obstacle_appeared))
# print(len(player_response_destroy))
# print(len(predloading_by_cycle))
# print(len(guessing_by_cycle))
# print(len(no_of_times_ammo_preloaded_4_each_cycle))
# print(len(true_guessing_count))
# print(len(player_response_wall))
# print(len(cycle_start_time))
# print(len(cycle_level))
# print(len(total_score))
# print(len(distance))

# Columns for the dataframe
extracted_data = {
    "player_id" : all_game_ids,
    'Tracker ID' : tracker_id_list,
    "Target Response Time(ms)" : player_response_stop,
    "No. of times obstacle appeared" : no_of_times_obstacle_appeared,
    "Explosion Response Times(ms)" : player_response_destroy,
    "Ammo preloaded?(1 = Yes)" : predloading_by_cycle,
    "Guess true?" : guessing_by_cycle,
    "No_of_times_ammo_preloaded"  : no_of_times_ammo_preloaded_4_each_cycle,
    "No_of_correct_guesses" : true_guessing_count,
    "Wall Response (distance)" : player_response_wall,
    "Time of Play (hr:min:s)" : cycle_start_time,
    "Distance b/w crosshair nd target" : distance_by_cycle,
    "Cycle Level" : cycle_level,
    "Total Score" : total_score,
    "cycle duration(in seconds)" : duration_of_each_cycle
}

df = pd.DataFrame(extracted_data)

#mean target response time 
mean_target_response_time = []

for times in df['Target Response Time(ms)']:
  mean_target_response_time.append(mean(times))
df['Mean Target Response Time'] = mean_target_response_time

#mean target response distance
mean_target_response_distance = []

for times in df['Distance b/w crosshair nd target']:
  mean_target_response_distance.append(mean(times))
df['Mean Target Response Distance'] = mean_target_response_distance

## Removing negative values from Explosion response


copy_df = df['Explosion Response Times(ms)']


for i in range(len(df['Explosion Response Times(ms)'])):

  true_neg_count = 0
  count = 0
  
  for j in range(len(copy_df[i])):

    j = j-count

    if copy_df[i][j] != None:
      
      if copy_df[i][j] < 0:
 
        del(df['Explosion Response Times(ms)'][i][j])    ## Removing negative response time
        del(df['Ammo preloaded?(1 = Yes)'][i][j])        ## Removing Ammo preloded for the same index

        if df['Guess true?'][i][j] == 'T':
          true_neg_count = true_neg_count+1       

        del(df['Guess true?'][i][j])                 ## Removing Guess true for the same index
        df['No. of times obstacle appeared'][i] -= 1    ## Reducing the count of obstacle apperered

        count +=1

  if not df['Explosion Response Times(ms)'][i]:
    df['Explosion Response Times(ms)'][i].append(None)       ## If any list had all -ve values, placing None in it bcoz it will be empty



  df['No_of_times_ammo_preloaded'][i] = sum(df['Ammo preloaded?(1 = Yes)'][i])        ## Re-calculating no. of time ammo preloaded
  df['No_of_correct_guesses'][i] -= true_neg_count                                    ## Reducing count of number of true guesses

##mean obstacle response value
mean_explosion_response_time = []

for times in df['Explosion Response Times(ms)']:
  mean_explosion_response_time.append(round(np.nanmean(times,dtype="float"),2))
df['Mean Explosion Response Time'] = mean_explosion_response_time

#print(df.info())

#GameId is unique to each player

cycle_count = df['player_id'].value_counts()
less_count = cycle_count[cycle_count<2].index.values
for k in range(len(less_count)):
  df.drop(df[df['player_id'] == less_count[k]].index,inplace=True)
  df.reset_index(drop=True,inplace=True)
  


#storing unique player code
player_id = df['player_id'].unique()
#df['player_id'].nunique()

player_no = []
count = []
cycle_in_which_ammo_first_preloaded = []

for i in range(1, len(player_id)+1):
  player_no.append(i) #assign unique no. to each code for readability 
  count.append(0)#later used
  cycle_in_which_ammo_first_preloaded.append(0)#later used
#print(player_no)

player_details = pd.DataFrame()
player_details['player_id'] = player_id
player_details['player_no'] = player_no #assign unique no. to each code for readability 
player_details['no_of_times_played'] = count #total no. of games played by each player will be stored in it

#assignin unique no. to each code to enhance readability, unique no. corresponding to each player from DataFrame 'player_details' is assigned to "player_id"
j=0
for p in df['player_id'] :
  for q in range(0,len(player_details)) :
    if p == player_details['player_id'][q]:
      df['player_id'][j] = player_details['player_no'][q]
      player_details['no_of_times_played'][q] = player_details['no_of_times_played'][q]+1 #counting the no. of games played by each player
  j=j+1

#after how many cycles ammo preloaded

df_grouped = df.groupby('player_id')

for i in df['player_id'].unique():
    a =  df_grouped.get_group(i)
    c=0
    for arr in a['Ammo preloaded?(1 = Yes)']:
      
      c+=1
      if sum(arr) >=1 :
        cycle_in_which_ammo_first_preloaded[i-1]=c
        break
      
#print(cycle_in_which_ammo_first_preloaded)
#len(cycle_in_which_ammo_first_preloaded)

#total_no_of_times_preloaded
total_no_of_times_preloaded =[] 

for i in df['player_id'].unique():
    a =  df_grouped.get_group(i)
    total_no_of_times_preloaded.append(a['No_of_times_ammo_preloaded'].sum())

#print(total_no_of_times_preloaded)
#len(total_no_of_times_preloaded)

player_details['cycle_in_which_ammo_first_preloaded']=cycle_in_which_ammo_first_preloaded
player_details['total_no_of_times_preloaded']=total_no_of_times_preloaded

##For display purpose
df_converted = df.copy()
df_converted["Target Response Time(ms)"] = df_converted["Target Response Time(ms)"].astype(str)
df_converted["Explosion Response Times(ms)"] = df_converted["Explosion Response Times(ms)"].astype(str)
df_converted["Ammo preloaded?(1 = Yes)"] = df_converted["Ammo preloaded?(1 = Yes)"].astype(str)
df_converted["Guess true?"] = df_converted["Guess true?"].astype(str)
##^^^^^For display purpose^^^^^^^

st.header('**Extracted Data**')
st.write('The raw data is processed in a readable format, first few rows are displayed below')
st.write('Please **download** the excel file to access all the rows. Download button is below each table.') 
st.subheader('**Cycle Data**')
st.table(df_converted.head())
#st.write(df.to_html(), unsafe_allow_html=True)


if st.button('Download Cycle Data as excel'):
    tmp_download_link = download_link(df, 'cycle_data.xlsx', 'Click here to download your data!')
    st.markdown(tmp_download_link, unsafe_allow_html=True)

st.subheader('**Player Details**')
st.table(player_details.head())

if st.button('Download Player Details as excel'):
    tmp_download_link = download_link(player_details, 'player_details.xlsx', 'Click here to download your data!')
    st.markdown(tmp_download_link, unsafe_allow_html=True)

#player_details['no_of_times_played'].sum() #it should be equal to the total no. of rows in df

st.header('**Overall Insights**')
st.write("**Total no. of players:**", len(player_details))
st.write("**Total no. of cycles played:**", len(df))
## Summary Statistics


st.write('**Mean number of cycles played by a player**',np.mean(player_details['no_of_times_played']))

st.write('**Standard Deviation of number of cycles played by players**',np.std(player_details['no_of_times_played']))

st.write('**Median of number of cycles played by a player**',np.median(player_details['no_of_times_played']))

st.write('**25, 50 and 75 percentiles of number of cycles played by players**',np.percentile(player_details['no_of_times_played'],[25,50,75]))

st.write("**{} times ammo was preloaded exactly one time in a cycle**".format(df[df['No_of_times_ammo_preloaded'] == 1]['player_id'].nunique()))
st.write("**{} times ammo was preloaded more than one time in a cycle**".format(df[df['No_of_times_ammo_preloaded'] > 1]['player_id'].nunique()))

#st.write(np.percentile(player_details['no_of_times_played'],[25,50,75]))

st.subheader("**Histogram for no. of games(cycles) played by players**")
# Frequency Plot
fig, ax = plt.subplots()
plt.title('Frequency of playing')
plt.xticks(np.arange(1, len(player_details)+1, 1),fontsize=8)
plt.yticks(np.arange(1, max(player_details['no_of_times_played'])+1, 1),fontsize=8)
sns.barplot(x='player_no',y='no_of_times_played',data=player_details,order=player_details.sort_values('no_of_times_played',ascending=False).player_no)
plt.xlabel('Player ID')
plt.ylabel('Number of Times Played')
st.pyplot(fig)



## Function for plotting response value with a player_id
def value_vs_cycle(column):
    fig,ax = plt.subplots(1)
    sns.set()
    sns.lineplot(data=df_game,x= df_game.index+1,y=column,hue="player_id",style="player_id",markers=['o'],palette='hot')
    plt.xticks(np.arange(1, len(df_game)+1, 1))
    plt.margins(0.05)
    plt.xlabel("Cycle Number")
    st.pyplot(fig)

# Grouped df on unique values of player_id
df_grouped = df.groupby('player_id')


# Data of first time played and last time played

last = df_grouped.last()
first = df_grouped.first()

df_response_target = pd.DataFrame()
df_response_wall = pd.DataFrame()
df_response_obstacle = pd.DataFrame()

df_response_target['First Cycle'] = first['Mean Target Response Time']
df_response_wall['First Cycle'] = first['Wall Response (distance)']
df_response_obstacle['First Cycle'] = first['Mean Explosion Response Time']

df_response_target['Last Cycle'] = last['Mean Target Response Time']
df_response_target.reset_index(inplace=True)

df_response_wall['Last Cycle'] = last['Wall Response (distance)']
df_response_wall.reset_index(inplace=True)

df_response_obstacle['Last Cycle'] = last['Mean Explosion Response Time']
df_response_obstacle.reset_index(inplace=True)

# df_response_target

# Function to plot interactive plots using Plotly Express
def interactive_plot(df, title):
  fig = px.line( title = title + 'vs player no',)

  for i in df.columns[1:3]:
    fig.add_scatter(x = df['player_id'], y = df[i], name = i,connectgaps=True)

  fig.update_layout(
    xaxis_title="Player No",
    yaxis_title=title)
  
  st.plotly_chart(fig)

st.subheader("**A interactive plot of Target Response Time(Time taken by player to hit the target) corresponding each player**")
st.write("We have plotted two cycles, one is very first cycle of game played by the player, and the other is last cycle of game played by the player")

interactive_plot(df_response_target, 'Target Response Time(ms)')

st.subheader("**A interactive plot of Wall Distance(at wall distance player stopped the dragster) corresponding each player**")
interactive_plot(df_response_wall, 'Wall Response (distance)')

mean_responses = df_grouped.mean()

st.subheader("**A plot between Mean Target Response Time and no. of times played**")
fig, ax = plt.subplots()
plt.xlabel('Mean Target Response time')
plt.ylabel('Number of Times Played')
# plt.title('Frequency of playing')
# plt.xticks(np.arange(0, len(player_details)+1, 1))
plt.yticks(np.arange(0, max(player_details['no_of_times_played'])+1, 1))
plt.scatter(mean_responses['Mean Target Response Time'],player_details['no_of_times_played'])
st.pyplot(fig)

#mean explosion response time vs total_no_of_times_preloaded

st.subheader("**Plot between Mean Target Response Time and no. of times ammo preloaded**")

fig, ax = plt.subplots(figsize=(10,8))
plt.xlabel('Mean Explosion Response time')
plt.ylabel('No. of times ammo preloaded')
plt.yticks(np.arange(0, max(df['No_of_times_ammo_preloaded'])+1, 1))
ax.scatter(df['Mean Explosion Response Time'],df['No_of_times_ammo_preloaded'], alpha = 0.5)
# ax.set_facecolor("white")
st.pyplot(fig)

st.subheader("**Plot between Mean Target Response Time and how many times correct ammo was preloaded**")
#mean response time vs correct guess
fig, ax = plt.subplots(figsize=(10,8))
plt.xlabel('Mean Explosion Response time')
plt.ylabel('No. of times correct ammo preloaded(correct guess)')
plt.yticks(np.arange(0, max(df['No_of_correct_guesses'])+1, 1))
ax.scatter(df['Mean Explosion Response Time'],df['No_of_correct_guesses'], alpha = 0.5,)
# ax.set_facecolor("white")
# sns.scatterplot(x= df['Mean Explosion Response Time'],y=df['No_of_correct_guesses'], alpha = 0.5)
st.pyplot(fig)
#len(df['Mean Explosion Response Time'])
#len(df[df['No_of_correct_guesses'] != 0])

st.subheader("**A plot of distance(distance between crosshair and target) and response time**")
#distance vs target response time

fig, ax = plt.subplots(figsize=(10,8))
plt.xlabel('Target Response time')
plt.ylabel('Distance b/w crosshair and target')
# plt.yticks(np.arange(0, max(df['Mean Target Response Distance'])+1, 1))
ax.scatter(df['Mean Target Response Time'],df['Mean Target Response Distance'], alpha = 0.5)
# ax.set_facecolor("white")
st.pyplot(fig)

st.subheader("**A plot showing variation of score according to game level**")
fig, ax = plt.subplots(figsize=(10,8))
plt.xlabel('Cycle Level')
plt.ylabel('Total Score')
plt.xticks(np.arange(0, max(df['Cycle Level'])+1, 1))
ax.scatter(df['Cycle Level'],df['Total Score'], alpha = 0.5)
# ax.set_facecolor("white")
st.pyplot(fig)

st.subheader("**Overall Improvements**")
st.write("In the plots given below, the more red value of a player is, the better is the improvement in response time/distance. And the more green value of a player is, the more is the response time/distance has increased.")
def overall_change_bars(df,title):
  df1 = df.copy(deep=True)
  df1['Change'] = df1['Last Cycle'] - df1['First Cycle']
  df1['colors'] = ['red' if x < 0 else 'green' for x in df1['Change']]
  df1.sort_values('Change',inplace=True)
  st.write('{} % players were able to improve their responses as compared to the first cycle'.format(round((df1['colors'].value_counts()['red']/len(df1))*100,3)),"\n")
  st.write('95% Confidence Interval in Change:', sp.norm.interval(alpha=0.95, loc=np.mean(df1['Change']), scale=sp.sem(df1['Change'])),"\n")

  plt.clf()
  fig, ax = plt.subplots(figsize=(14,10),dpi= 80)
  plt.hlines(y=df1.index, xmin=0, xmax=df1.Change, color=df1.colors, linewidth=5,alpha=0.9)
  for x, y, tex in zip(df1.Change, df1.index, df1.Change):
    plt.text(x, y, round(tex, 2), horizontalalignment='right' if x < 0 else 'left',verticalalignment='center', fontdict={'color':'red' if x < 0 else 'green', 'size':10})

# Decorations
  plt.gca().set(ylabel='$Player No$', xlabel='Change in {}'.format(title))
  plt.yticks(df1.index, df1.player_id, fontsize=13)
  plt.xticks(fontsize=13)

  plt.title('Overall change in {} for each player'.format(title), fontdict={'size':20})
  plt.grid(linestyle='--', alpha=0.5)
  plt.xlim(min(df1['Change'])-1000, max(df1['Change'])+1000)
  st.pyplot(fig)

#st.subheader("...........")
overall_change_bars(df_response_target, 'Target Response Time(ms)')
#st.subheader("...........")
overall_change_bars(df_response_wall, 'Wall Response (distance)')
#st.subheader("...........")
overall_change_bars(df_response_obstacle, 'Mean Explosion Response Time')

### Did the pre-loading become more effective overtime (i.e. lower response times)?

## For a cycle with more than 1 time preloading occur, overall change in response time is calculated by subtracting all time when pre-loading occur so if the result is positive then preloading is effective over time, if it negative then it is not effective
## Also for a particular player if the calculated response time(from above line) is decreasing over cycle also remaining positive then it means preloading is effective over cycles and conclusion is same if response time is negative and increasing

for key, item in df_grouped:   

  ## df_unique is dataframe of a player_id, Key is 'player_id'
  df_unique = df_grouped.get_group(key)           
  df_unique = df_unique[df_unique['No_of_times_ammo_preloaded'] > 1]   


  ## We need atleast 2 cycles for a player with pre-loading to compare
  if not (df_unique.empty) and (len(df_unique)>1):       


    change_in_time_list = []


    # Iterate over rows of dataframe
    for index, cycle in df_unique.iterrows():

      c = 0
      for indexi in range(len(cycle['Ammo preloaded?(1 = Yes)'])):

        # Filtering for case of preloading
        if (cycle['Ammo preloaded?(1 = Yes)'][indexi] == 1) and (cycle['Explosion Response Times(ms)'][indexi] != None):

          # For first time preloading in the cycle
          if c==0:
            change_in_time = cycle['Explosion Response Times(ms)'][indexi]
            c = c+1

          else:

            # Subtracting consecutive preloading response time
            change_in_time = change_in_time - cycle['Explosion Response Times(ms)'][indexi]
        
      change_in_time_list.append(change_in_time)
      

    ##plot
    fig,ax = plt.subplots(1)
    sns.set()
    sns.lineplot(x= df_unique.index+1,y=change_in_time_list,hue=df_unique['player_id'],style=df_unique['player_id'],markers=['o'],palette='hot')
    plt.margins(0.05)
    plt.xlabel("Cycle Number")
    plt.ylabel("Overall change in response time for a cycle(FOR PRELOADING)")
    #st.pyplot(fig)

#df_game
# Input from user(player_id) to plot against the responses
# Input from user(Game ID) to plot against the responses
st.subheader('**Enter the Player Id for visualizing the trend of cycles**')
st.text('Player Id is integer greater than 0 and not more than %d' %len(player_details))
game_num = st.number_input(" ",min_value=1,max_value=len(player_details))#int(input("Enter the Game ID for visualizing the trend of cycles: "))
df_game = df_grouped.get_group(int(game_num))
df_game.reset_index(drop=True,inplace=True)

st.subheader("**Player wise Analysis**")
st.subheader("*A plot showing mean target response of the player in each cycle*")
value_vs_cycle(df_game['Mean Target Response Time'])
st.subheader("*A plot showing distance at which dragster stopped by player in each cycle*")
value_vs_cycle(df_game['Wall Response (distance)'])
st.subheader("*A plot showing mean explosiom response time of the player in each cycle*")
value_vs_cycle(df_game['Mean Explosion Response Time'])

st.subheader("*A plot showing variation between Mean Target Response Distance and Mean Target Response time for player*")
fig,ax = plt.subplots(1)
sns.set()
sns.scatterplot(data=df_game,x= df_game['Mean Target Response Distance'],y=df_game['Mean Target Response Time'],hue="player_id",style="player_id",markers=["o"],palette='hot')
  #plt.xticks(np.arange(0, len(df_game)+1, 1))
plt.margins(0.05)
plt.xlabel("Mean Target Response Distance")
  # ax = plt.axes()
  # ax.set_facecolor("white")
st.pyplot(fig)


st.write("**Covariance (A measure of how 2 quantities vary together) between Mean Target Response Distance and Mean Target Response time for player {}**".format(game_num),":", np.cov(df_game['Mean Target Response Distance'],df_game['Mean Target Response Time'])[0][1])
 
def score_vs_level(column):
    fig,ax = plt.subplots(1)
    sns.set()
    sns.lineplot(data=df_game,x= df_game['Cycle Level'],y=column,hue="player_id",markers=["o"],style='player_id',palette = 'hot')
    plt.xticks(np.arange(0, len(df_game)+1, 1))
    plt.margins(0.05)
    plt.xlabel("Cycle Level")
    #ax=plt.axes()
    #ax.set_facecolor("white")
    st.pyplot(fig)

#score_vs_level(df_game['Total Score'])

# When reaching a new level for the first time, how much does reaction time change, on average? How does this interaction change for levels 2, 3, 4, 5? For example, is the average time to react to the target on level 3 20% higher then level 2, when the player first tries that level?

one_to_two_target = []
two_to_three_target = []
three_to_four_target = []
four_to_five_target = []

# one_to_two_obstacle = []
# two_to_three_obstacle = []
# three_to_four_obstacle = []
# four_to_five_obstacle = []

for key, item in df_grouped:   

  df_unique = df_grouped.get_group(key).reset_index(drop=True)

  for i in range(len(df_unique)):

    try:

      if (df_unique['Cycle Level'][i] == 1) and (df_unique['Cycle Level'][i+1] == 2):
        one_to_two_target.append(df_unique['Mean Target Response Time'][i+1] - df_unique['Mean Target Response Time'][i])
        # one_to_two_obstacle.append(df_unique['Mean Explosion Response Time'][i+1] - df_unique['Mean Explosion Response Time'][i])

      elif (df_unique['Cycle Level'][i] == 2) and (df_unique['Cycle Level'][i+1] == 3):
        two_to_three_target.append(df_unique['Mean Target Response Time'][i+1] - df_unique['Mean Target Response Time'][i])
        # two_to_three_obstacle.append(df_unique['Mean Explosion Response Time'][i+1] - df_unique['Mean Explosion Response Time'][i])

      elif (df_unique['Cycle Level'][i] == 3) and (df_unique['Cycle Level'][i+1] == 4):
        three_to_four_target.append(df_unique['Mean Target Response Time'][i+1] - df_unique['Mean Target Response Time'][i])
        # three_to_four_obstacle.append(df_unique['Mean Explosion Response Time'][i+1] - df_unique['Mean Explosion Response Time'][i])

      elif (df_unique['Cycle Level'][i] == 4) and (df_unique['Cycle Level'][i+1] == 5):
        four_to_five_target.append(df_unique['Mean Target Response Time'][i+1] - df_unique['Mean Target Response Time'][i])
        # four_to_five_obstacle.append(df_unique['Mean Explosion Response Time'][i+1] - df_unique['Mean Explosion Response Time'][i])

      else:
        pass
    
    except:
      pass

m1 = np.mean(one_to_two_target)
m2 = np.mean(two_to_three_target)
m3 = np.mean(three_to_four_target)
m4 = np.mean(four_to_five_target)

st.subheader("**Level to level changes**")

st.write("Mean change in target response time from level 1 to 2:",m1)
st.write("Mean change in target response time from level 2 to 3:",m2)
st.write("Mean change in target response time from level 3 to 4:",m3)
st.write("Mean change in target response time from level 4 to 5:",m4)

st.write("**Negative mean average change means average response time is decreasing from previous level to the next level. Positive mean average change means average response time is decreasing from previous level to the next level**")


d = round(((m2-m1)/m1)*100,2) #percentage_change_in_1to2_and_2to3_target
e = round(((m3-m2)/m2)*100,2) #percentage_change_in_2to3_and_3to4_target
f = round(((m4-m3)/m3)*100,2) #percentage_change_in_3to4_and_4to5_target


st.write("Therefore, percentage change in mean response time for going to level 3 in comparison of going to level 2 is **{} %**, percentage change for going to level 4 in comparison of going to level 3 is **{} %**, and percentage change for going to level 5 in comparison of going to level 4 is **{} %**".format(-d,e,f))

#st.write(-percentage_change_in_1to2_and_2to3_target)
#st.write(percentage_change_in_2to3_and_3to4_target)
#st.write(percentage_change_in_3to4_and_4to5_target)

# Response time overall decreases after the first cycle
#  Do you know how much, on average; perhaps a confidence interval?

last = df_grouped.last()
first = df_grouped.first()

overall_change_target_time = []

for i in range(1,len(last)+1):
  overall_change_target_time.append(first['Mean Target Response Time'][i]-last['Mean Target Response Time'][i])

#print(overall_change_target_time)

a = sp.norm.interval(alpha=0.95, loc=np.mean(overall_change_target_time), scale=sp.sem(overall_change_target_time))
b=np.mean(overall_change_target_time)
st.write("**There is a 95 percent chance that the confidence interval of {} contains the true population mean overall change in response time hitting the bullseye. And mean change in response time of first cycle and last cycle is {}**".format(a, b))

## For stacked frequency plot on no. of times opened the game

df_plot = df.groupby(['Tracker ID', 'player_id']).size().reset_index().pivot(columns='Tracker ID', index='player_id', values=0).fillna(0)
df_plot['sum_all'] = df_plot.sum(axis=1)
df_plot = df_plot.reindex(df_plot.sort_values(by="sum_all", ascending=False).index)
del(df_plot['sum_all'])

##### BOHOT TIME LETA H LOAD HONE ME

# plt.clf()
# fig, ax = plt.subplots(figsize=(10,10))

# df_plot.plot(kind='bar', stacked=True,legend=None,ax=ax,width=0.8)
# plt.yticks(np.arange(1, max(player_details['no_of_times_played'])+1, 1))
# plt.title('Frequency of playing')

# plt.xlabel('Player ID')
# plt.ylabel('Number of Times Played')
# plt.show()





## For players that preload, consider comparing their response times when they pre-loaded and when they didn’t – did preloading improve reaction speed overall?
df_joined = pd.DataFrame(columns=['Player_no','Explosion_joined','Guess_joined'])

for key, item in df_grouped:   
  df_unique = df_grouped.get_group(key)
  
  expolsion_joined = []
  guess_joined = []

  for i,cycle in df_unique.iterrows():

    expolsion_joined = expolsion_joined + cycle['Explosion Response Times(ms)']
    guess_joined = guess_joined + cycle['Ammo preloaded?(1 = Yes)']

####deletingggggg
  if 1 in guess_joined:
    if (len(expolsion_joined) > len(guess_joined)):
        expolsion_joined = expolsion_joined[:-1*(len(expolsion_joined)-len(guess_joined))]

    df_joined=df_joined.append({'Player_no':key,'Explosion_joined':expolsion_joined,'Guess_joined':guess_joined},ignore_index = True)



total_explosions = []
total_guesses = []


for x in df_joined['Explosion_joined'] :
  total_explosions += x

for y in df_joined['Guess_joined'] :
  total_guesses += y

#total_explosions += [x for x in df_joined['Explosion_joined']]
#print(len(total_explosions))
#len(total_guesses)

# df_joined

# plot total_explosions vs cycle no.  
cycle_no=[]
for i in range(1, len(total_explosions)+1 ):
  cycle_no.append(i)


## Normalize
total_explosions_non_null = [j for j in total_explosions if j != None]

norm = [100*(float(i)/sum(total_explosions_non_null)) if i != None else i for i in total_explosions]

# plt.clf()
# sns.set()
# plt.figure(figsize=(30,30)) 
# plot = sns.lineplot(x=cycle_no, y=norm, hue=total_guesses,palette='hot')
# plt.xticks(np.arange(1, len(total_explosions)+1, 1))
#    # plt.margins(0.05)
# plt.xlabel("Obstacle Number")
#    # ax = plt.axes()
#    # ax.set_facecolor("white")
# plt.show()
mean_response_change= []


for i, player in df_joined.iterrows():

  not_preloaded_time_only = []
  preloaded_time_only = []

  for idx, val in enumerate(player['Guess_joined']):
    if (val == 1) and (player['Explosion_joined'][idx] != None):
      preloaded_time_only.append(player['Explosion_joined'][idx])
    elif (val == 0) and (player['Explosion_joined'][idx] != None):
      not_preloaded_time_only.append(player['Explosion_joined'][idx])
  
  mean_response_change.append(round(np.mean(preloaded_time_only) - np.mean(not_preloaded_time_only),3))


  fig, ax = plt.subplots()
  sns.set() 
  sns.lineplot(x=np.arange(start=1, stop=len(player['Explosion_joined'])+1, step=1), y=player['Explosion_joined'], hue=player['Guess_joined'],style=player['Player_no'],markers=True,palette='hot',legend=False)
  plt.legend(labels=['Not Preloaded', 'Preloaded'])
  # plt.xticks(np.arange(1, len(player['Explosion_joined'])+1, 1))
    # plt.margins(0.05)
  plt.title('Player Number-{}'.format(player['Player_no']))
  plt.ylabel("Explosion Response Time(ms)")
  plt.xlabel("Obstacle Number")
    # ax = plt.axes()
    # ax.set_facecolor("white")
  #st.pyplot(fig)

####### MODEL PREDICTION #######
st.write('**Mean change in response time due to preloading**', np.nanmean(mean_response_change))
st.subheader("**Predictions**")
#sum(df['No_of_correct_guesses'])/sum(df['No_of_times_ammo_preloaded'])*100
df_joined.set_index('Player_no',inplace=True)
x_df = df_joined['Explosion_joined'][22]
x_df = [j for j in x_df if j != None]
explosion_df = pd.DataFrame({'Explosion_response_time' : x_df})

from sklearn.preprocessing import MinMaxScaler

scalar = MinMaxScaler(feature_range=(0,10))
explosion_df = scalar.fit_transform(np.array(explosion_df).reshape(-1,1))
trainig_size = int(len(explosion_df)*0.65)
test_size = len(explosion_df) - trainig_size
train_data,test_data = explosion_df[:trainig_size,:],explosion_df[trainig_size:len(explosion_df),:]

def create_dataset(dataset,time_step=1):
    X,y = [],[]
    for i in range(len(dataset)-time_step-1):
        X.append(dataset[i:(i+time_step),0])
        y.append(dataset[i+time_step,0])
    return np.array(X), np.array(y)

time_step = 30
X_train,y_train = create_dataset(train_data,time_step)
X_test,y_test = create_dataset(test_data,time_step)

## reshape input to be [samples, time steps, features/units in one input] which is required for LSTM (3 DIMENSION data)
X_train = X_train.reshape(X_train.shape[0],X_train.shape[1],1)
X_test = X_test.reshape(X_test.shape[0],X_test.shape[1],1)

from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense, LSTM

model = Sequential()
model.add(LSTM(50,return_sequences=True,input_shape=(30,1)))
model.add(LSTM(50,return_sequences=True))
model.add(LSTM(50))
model.add(Dense(1))
model.compile(loss='mean_squared_error',optimizer='adam')

model.fit(X_train,y_train,validation_data=(X_test,y_test),epochs=100,batch_size=64,verbose=1)
train_predict = model.predict(X_train)
test_predict = model.predict(X_test)

## For getting actual answers

train_predict = scalar.inverse_transform(train_predict)
test_predict = scalar.inverse_transform(test_predict)

import math
from sklearn.metrics import mean_squared_error

x_input=test_data[21:].reshape(1,-1)
temp_input=list(x_input)
temp_input=temp_input[0].tolist()

lst_output=[]
n_steps=30
i=0
while(i<2):
    
    if(len(temp_input)>30):
        #print(temp_input)
        x_input=np.array(temp_input[1:])  ## shape - (100,)
        # print("{} day input- {}".format(i,x_input),"\n")
        x_input=x_input.reshape(1,-1)  ## shape - (,100)
        x_input = x_input.reshape((1, n_steps, 1)) ## shape(1,100,1)
        #print(x_input)
        yhat = model.predict(x_input, verbose=0)
        #st.write("{} day output {}".format(i,yhat[0]))
        temp_input.extend(yhat[0].tolist())
        temp_input=temp_input[1:]
        #print(temp_input)
        lst_output.extend(yhat.tolist())
        i=i+1
    else:
        x_input = x_input.reshape((1, n_steps,1))
        yhat = model.predict(x_input, verbose=0)
       # print(yhat[0])
        temp_input.extend(yhat[0].tolist())
        #print(len(temp_input))
        lst_output.extend(yhat.tolist())
        i=i+1
st.write("Mean squared Error in test prediction",math.sqrt(mean_squared_error(y_test,test_predict)))
for i in lst_output:
  st.write("{} Predicted time: {}".format(lst_output.index(i)+1,i[0]*1000))








