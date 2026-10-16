#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 11:57:03 2024

@author: parisa
"""

# main.py

from Data_generation import generate_data
from Model_setup import setup_model
from Solve_model import solve_model
from Export_results import export_results
import random



#seeds = random.sample(range(1, 1000), 1)
seeds = [37]
for seed in seeds:
    data = generate_data(seed)
    model, variables = setup_model(data)
    
    # Set the time limit to 600 seconds
    model.setParam('TimeLimit', 7200)
    
    model, var_values = solve_model(model, variables, data)
    
    export_results(data, variables, model, filename=f"TPA{seed}.xlsx")
    





