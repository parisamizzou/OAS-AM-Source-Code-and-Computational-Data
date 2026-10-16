#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 12:06:50 2024

@author: parisa
"""


import pandas as pd




def generate_data(file_name):
    
    
    # Number of parts
    df = pd.read_excel(file_name, 'n', header = None)
    n = int(df.iloc[1, 0])
    J = list(range(1, n + 1))  # Set of parts indexed by j
    
    
    
    # Number of machines
    df = pd.read_excel(file_name, 'm', header = None)
    m = int(df.iloc[1, 0])
    I = list(range(1, m + 1))  # Set of machines indexed by i
   
    
    # Number of raw materials
    df = pd.read_excel(file_name, 'w', header = None)
    w = int(df.iloc[1, 0])
    R = list(range(1, w + 1))  # Set of raw materials indexed by r
   
    
    
    # Big M
    df = pd.read_excel(file_name, 'bigM', header = None)
    bigM = df.iloc[1,0]

    
    
    # Define the material type for each part: m_jr
    df = pd.read_excel(file_name, 'm_jr', header = None)  
    m_jr = {j: {r: int(df.iloc[j, r]) for r in R} for j in J}

    
   


    
    # Define machine eligibility: el_ir
    df = pd.read_excel(file_name, 'el_ir', header = None)    
    el_ir = {}
    for i in I:
        el_ir[i] = {} 
        for r in R:
            el_ir[i][r] = int(df.iloc[i, r])
           

    
    # Weight of part j after printing (gram): s_j
    df = pd.read_excel(file_name, 's_j', header = None)
    s_j = {}
    for j in J:
        s_j[j] = df.iloc[j,1]
  
    
    
    # Weight of raw material required for part j (grams): s_j_prime
    df = pd.read_excel(file_name, 's_j_prime', header = None)
    s_j_prime = {}
    for j in J:
        s_j_prime[j] = df.iloc[j,1]
   
    
    
    # Densities of raw materials (gr/cm^3): rho_r
    df = pd.read_excel(file_name, 'rho_r', header = None)
    rho_r = {}
    for r in R:
        rho_r[r] = df.iloc[r,1]
   
    
    
    # Job material
    df = pd.read_excel(file_name, 'job_material', header = None)
    job_material = {}
    for j in J:
        job_material[j] = int(df.iloc[j, 1])
   
    
    
    # Inventory of raw material r: IL_r
    df = pd.read_excel(file_name, 'IL_r', header = None)
    IL_r = {}
    for r in R:
        IL_r[r] = df.iloc[r,1]
    
   
    
   
    # Fixed setup time for all machines
    df = pd.read_excel(file_name, 'SET', header = None)
    SET = df.iloc[1,0]
    #print(SET)

    # Sequence-dependent setup time between two consecutive batches with raw material r and r'
    df = pd.read_excel(file_name, 'st', header = None)
    st = {}
    for r in R:
        st[r] = {}
        for r_prime in R:
            st[r][r_prime] = df.iloc[r, r_prime]

            
    
    # Machine availability time
    df = pd.read_excel(file_name, 'a_i', header = None)
    a_i = {}
    for i in I:
        a_i[i] = df.iloc[i, 1]

        
    
    
    # Release time of part j: r_j
    df = pd.read_excel(file_name, 'r_j', header = None)
    r_j = {}
    for j in J:
        r_j[j] = df.iloc[j, 1]
    
    
    
    # Due date of part j
    df = pd.read_excel(file_name, 'd_j', header = None)
    d_j = {}
    for j in J:
        d_j[j] = df.iloc[j, 1]
   
    
    
    # Volume of part j (cm^3)
    df = pd.read_excel(file_name, 'v_j_part', header = None)
    v_j_part = {}
    for j in J:
        v_j_part[j] = df.iloc[j, 1]
   
    
    
    
    # Part shape factor of part j: phi_j
    df = pd.read_excel(file_name, 'phi_j', header = None)
    phi_j = {}
    for j in J:
        phi_j[j] = df.iloc[j, 1]
    
    
    
    # Bounding box Volume of part j (cm^3)
    df = pd.read_excel(file_name, 'v_j_BB', header = None)
    v_j_BB = {}
    for j in J:
        v_j_BB[j] = df.iloc[j, 1]
    
    
    
    # Height of part j (cm)
    df = pd.read_excel(file_name, 'H_j_part', header=None)
    H_j_part = {}
    for j in J:
        H_j_part[j] = df.iloc[j, 1]
   
    
    
    # Bounding-box base area of part j (cm²)
    df = pd.read_excel(file_name, 'A_j_part', header=None)
    A_j_part = {}
    for j in J:
        A_j_part[j] = df.iloc[j, 1]
  
    
    
    
    # packing_density
    df = pd.read_excel(file_name, 'packing_density', header = None)
    packing_density = df.iloc[1,0]
   
    
    
    
    # material_coef
    df = pd.read_excel(file_name, 'material_coef', header = None)
    material_coef = df.iloc[1,0]

    
    
    # Length of machine i (cm)
    df = pd.read_excel(file_name, 'L_i', header = None)
    L_i = {}
    for i in I:
        L_i[i] = df.iloc[i, 1]
   
    
     
    
    # Width of machine i (cm)
    df = pd.read_excel(file_name, 'W_i', header = None)
    W_i = {}
    for i in I:
        W_i[i] = df.iloc[i, 1]
  
    
    
    
    # Height of machine i (cm)
    df = pd.read_excel(file_name, 'H_i', header = None)
    H_i = {}
    for i in I:
        H_i[i] = df.iloc[i, 1]
   
    
    
    
    
    # Volume of machine i (cm^3)
    df = pd.read_excel(file_name, 'v_i_ma', header = None)
    v_i_ma = {}
    for i in I:
        v_i_ma[i] = df.iloc[i, 1]
   
    
    
    # Printing time of machine i for a unit volume of raw material r (minutes): π_ir
    df = pd.read_excel(file_name, 'pi_ir', header = None)    
    pi_ir = {}
    for i in I:
        pi_ir[i] = {} 
        for r in R:
            pi_ir[i][r] = df.iloc[i,r]
  
    

    # Recoating time of machine i for a layer of raw material r: τ_ir (minutes)
    df = pd.read_excel(file_name, 'tau_ir', header = None)    
    tau_ir = {}
    for i in I:
        tau_ir[i] = {} 
        for r in R:
            tau_ir[i][r] = df.iloc[i,r]
  
    
    

    # Layer thickness
    df = pd.read_excel(file_name, 'LT_i', header = None)
    LT_i = {}
    for i in I:
        LT_i[i] = df.iloc[i, 1]
  
    

    
    # Production costs for each unit of time: dollar/min
    df = pd.read_excel(file_name, 'c_j_prod', header = None)
    c_j_prod = {}
    for j in J:
        c_j_prod[j] = df.iloc[j, 1]
   
    
    
    
    # Lateness costs for each unit of time: dollar/min
    df = pd.read_excel(file_name, 'c_j_late', header = None)
    c_j_late = {}
    for j in J:
        c_j_late[j] = df.iloc[j, 1]
   
    
    

    # Unit rejection cost of part j: dollar/part
    df = pd.read_excel(file_name, 'c_j_rej', header = None)
    c_j_rej = df.iloc[1,0]

    
    # Cost per unit of unused-capacity fraction per active batch
    df = pd.read_excel(file_name, 'c_emp', header = None)
    c_emp = df.iloc[1,0]
  
    
    
    # Define B_i
    df = pd.read_excel(file_name, sheet_name='B_i', header=None, dtype=str)
    B_i = {}


    # Loop through each column (representing a machine)
    for col in df.columns:
        # Extract the values below the machine index (column header) and remove NaNs
        batches = df.iloc[1:, col].dropna().astype(int).tolist()
        
        # Store the machine index (col+1 to match 1-based index) and its corresponding batches
        B_i[col+1] = batches

 
        

    
    
    data = {
        'n': n,
        'J': J,
        'm': m,
        'I': I,
        'w': w,
        'R': R,
        'm_jr': m_jr,
        'el_ir': el_ir,
        'bigM': bigM,
        's_j': s_j,
        's_j_prime': s_j_prime,
        'rho_r': rho_r,
        'job_material': job_material,
        'IL_r': IL_r,
        'SET': SET,
        'st': st,
        'a_i': a_i,
        'r_j': r_j,
        'd_j': d_j,
        'v_j_part': v_j_part,
        'L_i': L_i,
        'W_i': W_i,
        'H_i': H_i,
        'v_i_ma': v_i_ma,
        'pi_ir': pi_ir,
        'tau_ir': tau_ir,
        'LT_i': LT_i,
        'c_j_prod': c_j_prod,
        'c_j_late': c_j_late,
        'c_j_rej': c_j_rej,
        'c_emp': c_emp,
        'B_i': B_i,
        'H_j_part': H_j_part,
        'A_j_part': A_j_part,
        'phi_j': phi_j,
        'v_j_BB': v_j_BB,
        'packing_density': packing_density,
        'material_coef': material_coef,
       
    }
    
    
    
    return data
   
    


    
    
    
    