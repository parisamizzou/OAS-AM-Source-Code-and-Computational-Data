#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 11:53:03 2024

@author: parisa
"""

# solve_model.py
from gurobipy import GRB


def solve_model(model, variables, data):
    
    
    # Optimize the model
    model.optimize()
    
   
    
    # Initialize dictionaries to store variable values
    var_values = {
        'X': [],
        'Y': [],
        'Q': [],
        'C_batch': [],
        'C_job': [],
        'T': [],
        'P': [],
        'H': [],
        'E': [],
        'Objective': None,
        'Status': model.Status,
        'Runtime': model.Runtime,
        'MIPGap': None,
    }
    
    
    
    # Only access solution values when a feasible solution exists.
    if model.SolCount == 0:
        print(f"No feasible solution available. Status: {model.Status}")
        print(f"Time taken to solve the model: {model.Runtime:.2f} seconds")
        return model, var_values

    # Retrieve and analyze results
    if model.status == GRB.OPTIMAL:
        print("Optimal solution found.")

        # Store the objective value
        var_values['Objective'] = model.ObjVal
        print(f"Objective Value: {var_values['Objective']}")
        var_values['MIPGap'] = model.MIPGap
        

        # Extract variables for easier access
        X = variables['X']
        Y = variables['Y']
        Q = variables['Q']
        C_batch = variables['C_batch']
        C_job = variables['C_job']
        T = variables['T']
        P = variables['P']
        H = variables['H']
        E = variables['E']

        I = data['I']
        J = data['J']
        R = data['R']
        B_i = data['B_i']
        
        
        
    
       # Collect X variables and print them
        for i in I:
            for b in B_i[i]:
                for j in J:
                    for r in R:
                        if X[i][b][j][r].X > 0.5:
                            var_values['X'].append({'i': i, 'b': b, 'j': j, 'r': r, 'value': X[i][b][j][r].X})
                            print(f"X_{i}_{b}_{j}_{r} = {X[i][b][j][r].X}")
        
        # Collect Y variables and print them
        for i in I:
            for b in B_i[i]:
                for r in R:
                    if Y[i][b][r].X > 0.5:
                        var_values['Y'].append({'i': i, 'b': b, 'r': r, 'value': Y[i][b][r].X})
                        print(f"Y_{i}_{b}_{r} = {Y[i][b][r].X}")
        
        # Collect Q variables and print them
        for i in I:
            for b in B_i[i]:
                if b > 1:
                    for r_prime in R:
                        for r in R:
                            if r != r_prime and Q[i][b-1][r_prime][b][r].X > 0.5:
                                var_values['Q'].append({'i': i, 'b_prev': b-1, 'r_prime': r_prime, 'b': b, 'r': r, 'value': Q[i][b-1][r_prime][b][r].X})
                                print(f"Q_{i}_{b-1}_{r_prime}_{b}_{r} = {Q[i][b-1][r_prime][b][r].X}")



# Collect and print C_batch, C_job, T, P, H, and E variables
        for i in I:
            for b in B_i[i]:
                if C_batch[i][b].X != 0:
                    var_values['C_batch'].append({'i': i, 'b': b, 'value': C_batch[i][b].X})
                    print(f"C_batch_{i}_{b} = {C_batch[i][b].X}")

        for j in J:
            var_values['C_job'].append({'j': j, 'value': C_job[j].X})
            print(f"C_job_{j} = {C_job[j].X}")

        for j in J:
            var_values['T'].append({'j': j, 'value': T[j].X})
            print(f"T_{j} = {T[j].X}")

        for i in I:
            for b in B_i[i]:
                var_values['P'].append({'i': i, 'b': b, 'value': P[i][b].X})
                print(f"P_{i}_{b} = {P[i][b].X}")

        for i in I:
            for b in B_i[i]:
                var_values['H'].append({'i': i, 'b': b, 'value': H[i][b].X})
                print(f"H_{i}_{b} = {H[i][b].X}")

        for i in I:
            for b in B_i[i]:
                var_values['E'].append({'i': i, 'b': b, 'value': E[i][b].X})
                print(f"E_{i}_{b} = {E[i][b].X}")



    else:
        print("No optimal solution found.")
        
    # Print the time taken to solve the model
    print(f"Time taken to solve the model: {model.Runtime} seconds")  
    
    # Print the optimality gap percentage
    print(f"Optimality Gap: {model.MIPGap * 100:.2f}%")
    
    # Store the objective value
    var_values['Objective'] = round(model.ObjVal, 2)
    print(f"Objective Value: {var_values['Objective']}")

    return model, var_values 






                                
                                
          
        
       
       
        
        
        
      
        
        
        
        

