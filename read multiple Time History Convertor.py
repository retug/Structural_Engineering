# -*- coding: utf-8 -*-
"""
@author: aguter

Project recreates Newmarks method, constant acceleration method, as outlined
in Section 5.4 of Chopra
"""
import matplotlib.pyplot as plt
import numpy as np
import math

#these are the BSE-2E records provided to us
file_paths= ["RSN 171 - FN.txt", "RSN 171 - FP.txt","RSN 266 - FN.txt","RSN 266 - FP.txt","RSN 778 - FN.txt","RSN 778 - FP.txt",
             "RSN 1116 - FN.txt","RSN 1116 - FP.txt", "RSN 1141 - FN.txt", "RSN 1602 - FN.txt", "RSN 1602 - FP.txt",
             "RSN 4880 - FN.txt", "RSN 4880 - FP.txt", "RSN 6888 - FN.txt", "RSN 6888 - FP.txt", "RSN 6890 - FN.txt",
             "RSN 6890 - FP.txt", "RSN 8066 - FN Fixed.txt", "RSN 8066 - FP Fixed.txt", "RSN 8130 - FN Fixed.txt" ,"RSN 8130 - FP.txt"
             ]
             

main_path ="I:\Projects\\..."

##This function generates the PSA Values for a given earthquake record

def calc_acceleration(acceleration,time,T):
    
#====================================================
#   Calculations for Time Step One
#====================================================
    bldg_accel = []
    veloc = []
    disp = []
    PSA = []
    
    vel_0 = 0
    u0 = 0
    P0 = 0
    g = 386.4 #in/s^2
    beta = 1 / 4
    Gamma = 1 / 2
    dt = time[1]-time[0]
    
    zeta = 0.05 #damping ratio
    m = 0.2588  #Assume a generic mass
    wn = 2 * math.pi / T # Compute natural circular frequency
    k = m * wn * wn        # Compute stiffness corresponding to the given mass
    c = 2 * zeta * wn * m  # Compute the damping coefficient
    
    bldg_accel.append((P0 - c * vel_0 - k * u0) / m)
    veloc.append(0)
    disp.append(0)
    PSA.append(disp[0]*wn*wn)
    a1 = 1/(beta*dt**2)*m+Gamma/(beta*dt)*c
    a2 = 1/(beta*dt)*m+(Gamma/beta-1)*c
    a3 = (1/(2*beta)-1)*m+dt*(Gamma/2*beta-1)*c
    k_hat = k+a1
    p_hat = []
    p_hat.append(0)
    
    
    for i in range(len(acceleration)-1):
        p_hat_fut = acceleration[i+1]*g*m+a1*disp[i]+a2*veloc[i]+a3*bldg_accel[i]
        #p_hat_fut = accel[i+1]
        p_hat.append(p_hat_fut)
        disp_fut = p_hat_fut/k_hat
        veloc_fut= Gamma/(beta*dt)*(disp_fut-disp[i]) + (1-Gamma/beta)*veloc[i] + dt*(1-(Gamma/(2*beta)))*bldg_accel[i]
        accel_fut= (1/(beta*dt**2)*(disp_fut-disp[i])) - 1/(beta*dt)*veloc[i] - (1/(2*beta)-1)*bldg_accel[i]
        disp.append(disp_fut)
        veloc.append(veloc_fut)
        bldg_accel.append(accel_fut)
        PSA.append(disp_fut*wn*wn/g) 
        
    return max(max(PSA),abs(min(PSA)))

##############################################################################




for file_path in file_paths:
    end_path.append(main_path+"\\"+file_path)
    
## This for loop loops over multiple EQ records
PSA_EQs = []
for earthquake_record in end_path:
    with open(earthquake_record,'r') as f:
        contents = f.read()
    
    x = contents.split("\n")
    x.pop(0) #removes first errouneous values
    x.pop(-1) #removes last empty value
    accel = []
    time = []
    for values in x:
        y = values.split('\t')
        accel.append(float(y[1]))
        time.append(float(y[0]))
    Tn_range=np.arange(0,5,0.025)
    Tn=Tn_range[50]
    Pseudo_Spectral_Accel=[]
    #Pseudo_Spectral_Accel.append(0)
    
    for T in Tn_range:
        accel_at_T = calc_acceleration(accel,time,T)
        Pseudo_Spectral_Accel.append(accel_at_T)
    PSA_EQs.append(Pseudo_Spectral_Accel)



for (PSA_EQ,file_path) in zip(PSA_EQs,file_paths):
    plt.plot(Tn_range,PSA_EQ, label=file_path)
plt.xlabel("Period (s)")
plt.ylabel("Acceleration (g)")
plt.title("Ground Motion PSA vs Period")
plt.grid()
plt.legend()
           
plt.show()


