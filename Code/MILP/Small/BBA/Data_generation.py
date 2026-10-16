#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 10:27:47 2024

@author: parisa
"""

# data_generation.py

import random
import numpy as np
import math

def generate_data(seed):
    random.seed(seed)
    np.random.seed(seed)

    # Number of parts
    n = 10
    J = list(range(1, n + 1))  # Set of parts indexed by j

    # Number of machines
    m = 3
    I = list(range(1, m + 1))  # Set of machines indexed by i

    # Number of raw materials
    w = 3
    R = list(range(1, w + 1))  # Set of raw materials indexed by r

    # Define the material type for each part
    m_jr = {j: {r: 0 for r in R} for j in J}
    for j in J:
        r = random.choice(R)  # Randomly select one raw material for each part
        m_jr[j][r] = 1

    # Define machine eligibility el_ir
    el_ir = {i: {r: 0 for r in R} for i in I}
    # Ensure each machine is eligible to process at least one raw material
    for i in I:
        eligible_r = random.choice(R)  # Randomly select one raw material for each machine
        el_ir[i][eligible_r] = 1
    # Ensure each raw material is assigned to at least one machine
    for r in R:
        eligible_i = random.choice(I)  # Randomly select one machine for each raw material
        el_ir[eligible_i][r] = 1
    # Randomly assign eligibility for remaining machine-raw material pairs
    for i in I:
        for r in R:
            if el_ir[i][r] == 0:  # If not already assigned
                el_ir[i][r] = random.choice([0, 1])

    bigM = 10 ** 6
    
    packing_density = 0.4
    material_coef = 2

    s_j = {j: random.randint(50, 500) for j in J}  # Weight of part j after printing (gram)
    s_j_prime = {j: round(material_coef * s_j[j]) for j in J}  # Weight of raw material required for part j (grams)
    rho_r = {r: round(random.uniform(1, 1.5), 2) for r in R}  # Densities of sintered material (gr/cm^3)

    # Inventory of raw material r
    job_material = {job: next(r for r, val in raw_materials.items() if val == 1) for job, raw_materials in m_jr.items()}
    IL_r = {}
    for r in R:
        sum_of_weight = 0
        for j in J:
            if job_material[j] == r:
                sum_of_weight += s_j_prime[j]
        coef = random.uniform(0.8 , 1.2)
        IL_r[r] = round(coef * sum_of_weight)

    # Fixed setup time for all machines
    SET = random.randint(60, 120)

    # Sequence-dependent setup time between two consecutive batches with raw material r and r'
    st = {r: {r_prime: 0 if r == r_prime else random.randint(180, 240) for r_prime in R} for r in R}

    # Machine availability time
    a_i = {i: random.randint(0, 120) for i in I}

    # Release time of part j: r_j
    r_j = {j: random.randint(0, 240) for j in J}
    

    # Due date of part j
    d_j = {j: random.randint(1440, 4320) for j in J}

    # Calculate the volume of part j (cm^3)
    v_j_part = {}
    for j in J:
        density = sum(m_jr[j][r] * rho_r[r] for r in R)
        v_j_part[j] = s_j[j] / density

    L_i = {i: random.randint(20, 30) for i in I}  # Length of machine i (cm)
    W_i = {i: random.randint(20, 30) for i in I}  # Width of machine i (cm)
    H_i = {i: random.randint(20, 40) for i in I}  # Height of machine i (cm)
    v_i_ma = {i: L_i[i] * W_i[i] * H_i[i] for i in I}  # Volume of machine i (cm^3)

    # Printing time of machine i for a unit volume of raw material r (minutes): π_ir
    pi_ir = {i: {r: round(random.uniform(0.2, 1), 2) for r in R} for i in I}

    # Recoating time of machine i for a layer of raw material r: τ_ir (minutes)
    tau_ir = {i: {r: round(random.uniform(0.1, 0.2), 2) for r in R} for i in I}

    # Layer thickness
    LT_i = {i: round(random.uniform(0.005, 0.01),4) for i in I}

    # Unit costs for part j: c_j^{prod}, c_j^{late}, c_j^{rej}
    c_j_prod = {j: round(random.uniform(0.8, 1.3), 2) for j in J}  # Production costs for each unit of time
    c_j_late = {j: round(random.uniform(0.5, 1), 2) for j in J}  # Lateness costs for each unit of time
    c_j_rej = 5000 # Unit rejection cost of part j

   # Dollars per unit of unused-capacity fraction per active batch: c^{emp}
    #c_emp = round(random.uniform(0.1, 0.5), 2)  # dollar per cm^3
    c_emp = 10000

    
    
    
    # part shape factor U(0.2, 1): phi_j = actual solid volume / bounding-box volume
    phi_j = {j: round(random.uniform(0.20, 1), 2) for j in J}
    
    # Bounding-box volume for BBA (cm^3)
    v_j_BB = {
        j: v_j_part[j] / phi_j[j]
        for j in J}
    
    
    
    # Generate height
    H_j_part = {j: random.uniform(2, 20) for j in J}
    
    # Calculate bounding-box base area
    A_j_part = {j: v_j_BB[j] / H_j_part[j] for j in J}
    

    
    
    #Define B_i
    B_i = {}
    for i in I:
        #max_W_ir = max(W_ir[i][r] for r in R)
        total_volume = sum(v_j_part[j] for j in J)
        approx_batches = math.ceil(total_volume / (0.4 * v_i_ma[i]))
        B_i[i] = list(range(1, approx_batches + 1))
        
   
        
        
        

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
        'packing_density': packing_density,
        'material_coef': material_coef,
        'phi_j': phi_j,
        'v_j_BB': v_j_BB,
        'H_j_part': H_j_part,
        'A_j_part': A_j_part
        
    }
    
    


    return data






