import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class ProjectPersonel:
    def __init__(self, name, hrs, employee_type, cost):
        self.name = name
        self.hrs = hrs
        
        self.emloyee_type = employee_type
        self.cost = cost
        
        
names = ['Project Manager',
        'Proj Eng 1',
'Draft Help',
'Eng Help',
'Main Drafter',
'Eng Leave Mid Project',
'Principal',
'Main Proj Eng',
'Help Proj Eng 1',
'QAQC Eng',
'Help Eng 2',
'Drafter QAQC',
'Proj Eng 3',
'Proj Eng 4',
]


Hours = [743.25,
3,
12.5,
4,
880.5,
704.5,
274.5,
10,
983.5,
132.25,
15,
10,
4.5,
130,
19.5,
]


Cost = [32488.84,
135.47,
611.13,
212.12,
35771.19,
27503.50,
16704.31,
258.4,
30757.38,
4104.71,
954.6,
452.4,
278.69,
5041.40,
922.28,
]

EmployeeType = ['Engineer',
'Engineer',
'Drafter',
'Engineer',
'Drafter',
'Engineer',
'QA/QC',
'Drafter',
'Engineer',
'Engineer',
'QA/QC',
'Engineer',
'QA/QC',
'Engineer',
'Engineer',

]


list_people = []

for person, hr, emp_type, cost in zip(names, Hours, EmployeeType, Cost):
    x = ProjectPersonel(person, hr, emp_type, cost)
    list_people.append(x)

hrs_eng = 0
hrs_QAQC = 0
hrs_Draft = 0

eng_list = {}
drafter_list = {}
qa_qc_list = {}


for person in list_people:
    if person.emloyee_type == "Engineer":
        hrs_eng= hrs_eng + person.hrs
        eng_list[person.name] = person.hrs
        
    elif person.emloyee_type == "QA/QC":
        hrs_QAQC= hrs_QAQC + person.hrs
        qa_qc_list[person.name] = person.hrs
    else:
        hrs_Draft= hrs_Draft + person.hrs
        drafter_list[person.name] = person.hrs
        
        
total_hrs = hrs_Draft+hrs_QAQC+hrs_eng
percent_hrs_eng = hrs_eng/total_hrs
percent_hrs_draft = hrs_Draft/total_hrs
percent_hrs_QAQC = hrs_QAQC/total_hrs


People = {}
for person in list_people:
    if person.emloyee_type == "Engineer":
        
        result = [person.hrs, 0, 0]
        People[person.name] = result
        
    elif person.emloyee_type == "QA/QC":
        result = [0, person.hrs, 0]
        People[person.name] = result
    else:
        result = [0, 0, person.hrs]
        People[person.name] = result
        
total_hrs = hrs_Draft+hrs_QAQC+hrs_eng
percent_hrs_eng = hrs_eng/total_hrs
percent_hrs_draft = hrs_Draft/total_hrs
percent_hrs_QAQC = hrs_QAQC/total_hrs  
# ############################## Cost ###########################################

cost_eng = 0
cost_QAQC = 0
cost_Draft = 0

eng_list_cost = {}
drafter_list_cost = {}
qa_qc_list_cost = {}


for person in list_people:
    if person.emloyee_type == "Engineer":
        cost_eng= cost_eng + person.cost
        eng_list_cost[person.name] = person.cost
        
    elif person.emloyee_type == "QA/QC":
        cost_QAQC= cost_QAQC + person.cost
        qa_qc_list_cost[person.name] = person.cost
    else:
        cost_Draft= cost_Draft + person.cost
        drafter_list_cost[person.name] = person.cost
        

total_cost = cost_eng+cost_QAQC+cost_Draft
percent_cost_eng = cost_eng/total_cost
percent_cost_draft = cost_Draft/total_cost
percent_cost_QAQC = cost_QAQC/total_cost

PeopleCost = {}
for person in list_people:
    if person.emloyee_type == "Engineer":
        
        result = [person.cost, 0, 0]
        PeopleCost[person.name] = result
        
    elif person.emloyee_type == "QA/QC":
        result = [0, person.cost, 0]
        PeopleCost[person.name] = result
    else:
        result = [0, 0, person.cost]
        PeopleCost[person.name] = result
  
        
############################# Hours Spent ####################################

species = (
    "Engineer\n " + str(percent_hrs_eng),
    "QA/QC\n " + str(percent_hrs_QAQC),
    "Drafting\n " + str(percent_hrs_draft),
)

width = 0.5

fig, ax = plt.subplots()
bottom = np.zeros(3)



for boolean, test_person in People.items():
    p = ax.bar(species, test_person, width, label=boolean, bottom=bottom)
    bottom += test_person
    
ax.set_title("Hours Spent on Project")
ax.legend(loc="upper right")


############################# Hours Spent ####################################


############################# Cost Spent ####################################


species2 = (
    "Engineer\n " + str(percent_cost_eng),
    "QA/QC\n " + str(percent_cost_QAQC),
    "Drafting\n " + str(percent_cost_draft),
)

width = 0.5

fig, ax = plt.subplots()
bottom = np.zeros(3)



for boolean, test_person in PeopleCost.items():
    p = ax.bar(species2, test_person, width, label=boolean, bottom=bottom)
    bottom += test_person
    
ax.set_title("Cost Spent on Project")
ax.legend(loc="upper right")

############################# Cost Spent ####################################

## Time Plots


### Multiple Plots

df_all = pd.read_excel('H:\\MyGenericProject.xlsx', sheet_name = 'HoursForProject')
names = df_all.iloc[:,0]

my_column_changes = names.shift() != names        
index_change = [i for i, x in enumerate(my_column_changes) if x]

PersonHrs = {}
PersonDate = {}

for i in range(len(index_change)):
    if i == len(index_change)-1:
        print(i)
        PersonHrs[names[index_change[i]+1]] = df_all.iloc[index_change[i]+1:,2]
        PersonDate[names[index_change[i]+1]] = df_all.iloc[index_change[i]+1:,1]
        
    else: ###grabs the last person in the list
        print(i)
        PersonHrs[names[index_change[i]+1]] = df_all.iloc[index_change[i]+1:index_change[i+1],2]
        PersonDate[names[index_change[i]+1]] = df_all.iloc[index_change[i]+1:index_change[i+1],1]
    
        
sum_time = []
for i in PersonHrs.values():
    indiv_sum = []
    indiv_time = 0
    for time in i:
        indiv_time += time
        indiv_sum.append(indiv_time)
    sum_time.append(indiv_sum)
    
for indiv_person_hrs, indiv_person_date in zip(sum_time, PersonDate.values()):
    DF = pd.DataFrame()
    DF['value'] = indiv_person_hrs
    
    person_date = pd.to_datetime(indiv_person_date) 
    DF = DF.set_index(person_date)
    
        
    plt.plot(DF)
    plt.gcf().autofmt_xdate()

plt.legend(PersonDate.keys())
plt.show()
    
    

        
        