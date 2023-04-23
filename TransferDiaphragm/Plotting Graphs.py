# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 19:59:36 2023

@author: aguter
"""
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)

x=5

df = pd.read_excel('H:\\Data.xlsx', sheet_name = None)
location = df['Base Model - 24 Transfer Slab'].iloc[1:101,1].to_numpy()
shear1 = df['Base Model - 24 Transfer Slab'].iloc[1:101,2].to_numpy()
shear2 = df['12 Transfer 50% Stiffness'].iloc[1:101,2].to_numpy()
shear3 = df['Base Model - With Hole'].iloc[1:101,2].to_numpy()
shear4 = df['Fpx'].iloc[1:101,2].to_numpy()

moment1 = df['Base Model - 24 Transfer Slab'].iloc[1:101,3].to_numpy()
moment2 = df['12 Transfer 50% Stiffness'].iloc[1:101,3].to_numpy()
moment3 = df['Base Model - With Hole'].iloc[1:101,3].to_numpy()
moment4 = df['Fpx'].iloc[1:101,3].to_numpy()



plt.plot(location, shear1, label = "Base Model 24", linestyle = '--', linewidth = 3, color = "black" )   
plt.plot(location, shear2, label = "12in Transfer", linestyle = '--', linewidth = 3, color = "orange" )   
plt.plot(location, shear3, label = "Base Model - Hole", linestyle = '--', linewidth = 3, color = "gold" )
plt.plot(location, shear4, label = "Fpx", linestyle = '--', linewidth = 3, color = "red" )

plt.ylabel('Diaphragm Shear - Kip')
plt.xlabel('Diaphragm Location - Feet')


plt.grid(b=True, which='major', color='#CCCCCC', linestyle='--')
plt.grid(b=True, which='minor', color='#CCCCCC', linestyle=':')
plt.title('Shear Force in the Diaphragm')
plt.minorticks_on()
plt.legend()
           
plt.show()

# plt.plot(location, moment1, label = "Base Model 24", linestyle = '--', linewidth = 3, color = "black" )   
# plt.plot(location, moment2, label = "12in Transfer", linestyle = '--', linewidth = 3, color = "orange" )   
# plt.plot(location, moment3, label = "Base Model - Hole", linestyle = '--', linewidth = 3, color = "gold" )
# plt.plot(location, moment4, label = "Fpx", linestyle = '--', linewidth = 3, color = "red" )

# plt.ylabel('Diaphragm Moment - Kip*ft')
# plt.xlabel('Diaphragm Location - Feet')


# plt.grid(b=True, which='major', color='#CCCCCC', linestyle='--')
# plt.grid(b=True, which='minor', color='#CCCCCC', linestyle=':')
# plt.title('Moment in the Diaphragm')
# plt.minorticks_on()
# plt.legend()
           
# plt.show()