#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 11:44:02 2024

@author: parisa
"""

# model_setup.py

from gurobipy import Model, GRB, quicksum

def setup_model(data):
    # Create a new model
    model = Model("Additive_Manufacturing_Scheduling")


    # Extract parameters from data
    J = data['J']
    I = data['I']
    R = data['R']
    m_jr = data['m_jr']
    el_ir = data['el_ir']
    bigM = data['bigM']
    s_j_prime = data['s_j_prime']
    IL_r = data['IL_r']
    SET = data['SET']
    st = data['st']
    a_i = data['a_i']
    r_j = data['r_j']
    d_j = data['d_j']
    v_j_part = data['v_j_part']
    L_i = data['L_i']
    W_i = data['W_i']
    H_i = data['H_i']
    v_i_ma = data['v_i_ma']
    pi_ir = data['pi_ir']
    tau_ir = data['tau_ir']
    LT_i = data['LT_i']
    c_j_prod = data['c_j_prod']
    c_j_late = data['c_j_late']
    c_j_rej = data['c_j_rej']
    c_emp = data['c_emp']
    B_i = data['B_i']
    H_j_part = data['H_j_part']
    packing_density = data['packing_density']
    A_j_part = data['A_j_part']
   
    
   
    
    

    # Decision Variables
    # Define the binary decision variable X_ijbr
    X = {}
    for i in I:
        X[i] = {}
        for b in B_i[i]:
            X[i][b] = {}
            for j in J:
                X[i][b][j] = {}
                for r in R:
                    X[i][b][j][r] = model.addVar(vtype=GRB.BINARY, name=f"X_{i}_{b}_{j}_{r}")

    # Add constraints to fix X_ibjr to 0 for jobs that machine i is not eligible to process raw material r of job j
    # or part j is not with material r
    for i in I:
        for j in J:
            for b in B_i[i]:
                for r in R:
                    if m_jr[j][r] == 0:
                        X[i][b][j][r].setAttr(GRB.Attr.LB, 0)
                        X[i][b][j][r].setAttr(GRB.Attr.UB, 0)
                    elif m_jr[j][r] == 1 and el_ir[i][r] == 0:
                        X[i][b][j][r].setAttr(GRB.Attr.LB, 0)
                        X[i][b][j][r].setAttr(GRB.Attr.UB, 0)

    # Define the binary decision variable Y_ibr
    Y = {}
    for i in I:
        Y[i] = {}
        for b in B_i[i]:
            Y[i][b]={}
            for r in R:
                Y[i][b][r] = model.addVar(vtype=GRB.BINARY, name=f"Y_{i}_{b}_{r}")

    # Add constraints to fix Y_ibr to 0 for batches that machine i is not eligible to process raw material r
    for i in I:
        for b in B_i[i]:
            for r in R:
                if el_ir[i][r] == 0:
                    Y[i][b][r].setAttr(GRB.Attr.LB, 0)
                    Y[i][b][r].setAttr(GRB.Attr.UB, 0)

    # Initialize Q with zeros for all possible indices
    Q = {}
    for i in I:
        Q[i] = {}
        for b in B_i[i]:
            if b > 1:  # Only for batches b > 1
                Q[i][b-1] = {}
                for r_prime in R:
                    Q[i][b-1][r_prime] = {}
                    Q[i][b-1][r_prime][b] = {}
                    for r in R:
                        if r != r_prime:
                            Q[i][b-1][r_prime][b][r] = model.addVar(vtype=GRB.BINARY, name=f"Q_{i}_{b-1}_{r_prime}_{b}_{r}")

    # Fix Q if machine i is not eligible to process r or r_prime
    for i in I:
        for b in B_i[i]:
            if b > 1:  # Only for batches b > 1
                for r in R:
                    for r_prime in R:
                        if r != r_prime:
                            if el_ir[i][r] == 0 or el_ir[i][r_prime] == 0:
                                Q[i][b-1][r_prime][b][r].setAttr(GRB.Attr.LB, 0)
                                Q[i][b-1][r_prime][b][r].setAttr(GRB.Attr.UB, 0)

    # Define the completion time of batch b on machine i: C_batch{ib}
    C_batch = {}
    for i in I:
        C_batch [i] = {}
        for b in B_i[i]:
            C_batch [i][b] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"C_batch_{i}_{b}")

    # Define the completion time of part j on machine i: C_job{ij}
    C_job = {}
    for j in J:
        C_job[j] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"C_job_{j}")

    # Define the lateness of part j: T_j
    T = {}
    for j in J:
        T[j] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"T_{j}")

    # Define the variable processing time for batch b processed on machine i:  P_{ib}
    P = {}
    for i in I:
        P[i]={}
        for b in B_i[i]:
            P[i][b]= model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"P_{i}_{b}")

    # Define the height of the b-th batch on machine i: H_{ib}
    H = {}
    for i in I:
        H[i]={}
        for b in B_i[i]:
            H[i][b] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"H_{i}_{b}")

    # Fraction of usable machine height utilized:  E_{ib}
    E = {}
    for i in I:
        E[i]={}
        for b in B_i[i]:
            E[i][b]= model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1, name=f"E_{i}_{b}")

    model.update()  # Integrate new variables

    ################################################### Constraints ##########################################

    # Define constraint new2
    for j in J:
        model.addConstr(quicksum(X[i][b][j][r] for i in I for r in R for b in B_i[i]) <= 1,
                        name=f"Constraint_2_{j}")
        
        
    

             
    # Define constraint (3)
    for i in I:
        for b in B_i[i]:
            for r in R:
                # lower part of constraint
                cons3_l = Y[i][b][r] <= quicksum(X[i][b][j][r] for j in J)
                model.addConstr(cons3_l,  name = f"LowerBound_Constraint_3l_{i}_{b}_{r}")
                #print(f"Added LowerBound_Constraint_3l_{i}_{b}_{r}: Y[{i}][{b}][{r}] <= quicksum(X[{i}][j][{b}][{r}] for j in J)")
               
                
                # upper part of constraint
                max_parts = sum(m_jr[j][r] for j in J)
                cons3_u = quicksum(X[i][b][j][r] for j in J) <= max_parts * Y[i][b][r]
                model.addConstr(cons3_u,  name = f"UpperBound_Constraint_3u_{i}_{b}_{r}")   
                #print(f"Added UpperBound_Constraint_3u_{i}_{b}_{r}: quicksum(X[{i}][j][{b}][{r}] for j in J) <= {M} * Y[{i}][{b}][{r}]")

                  
                        
     # Define constraint (4)                   
    for i in I:
        for b in B_i[i]:
            cons4 = quicksum(Y[i][b][r] for r in R) <= 1
            model.addConstr(cons4, name=f"Constraint_4_{i}_{b}")
                                    
                                                                      
                
    # Define constraint (5)       
    for i in I:
        for b in B_i[i]:
            if b > 1:
                model.addConstr(
                    quicksum(Y[i][b][r] for r in R)
                    <= quicksum(Y[i][b-1][r] for r in R),
                    name=f"Constraint_5_{i}_{b}"
                )



    # Define constraint (6)
    for r in R:
        cons6 = IL_r[r] >= quicksum(s_j_prime[j] * X[i][b][j][r] for i in I for j in J for b in B_i[i])
        model.addConstr(cons6, name = f"Constraint_6_{r}")
        
        
                          
    # Define constraint (7)
    for i in I:
        for b in B_i[i]:
            if b > 1:  # Skip the first batch since there's no previous batch
                for r in R:
                    for r_prime in R:
                        if r != r_prime:
                            cons7 = Q[i][b-1][r_prime][b][r] >= Y[i][b][r] + Y[i][b-1][r_prime]- 1
                            model.addConstr(cons7, name = f"constraint_7_{i}_{b-1}_{r_prime}_{b}_{r}")
                                               

    # Define constraint (8)
    for i in I:
        for b in B_i[i]:
            if b > 1:  # Skip the first batch since there's no previous batch
                for r in R:
                    for r_prime in R:
                        if r != r_prime:
                            cons8 = Q[i][b-1][r_prime][b][r] <= Y[i][b][r]
                            model.addConstr(cons8, name = f"Constraint_8_{i}_{b}_{r}_{r_prime}")
                          
                            
                  

    # Define constraint (9)
    for i in I:
        for b in B_i[i]:
            if b != 1:  # Skip the first batch since there's no previous batch
                for r in R:
                    for r_prime in R:
                        if r != r_prime:
                            cons9 =  Q[i][b-1][r_prime][b][r] <= Y[i][b-1][r_prime]
                            model.addConstr(cons9, name=f"Constraint_9_{i}_{b}_{r}_{r_prime}")
                           



              
   # for TPA only             
    # Define constraint (10)  
    for i in I:
        for b in B_i[i]:
            cons10 = quicksum(v_j_part[j] * X[i][b][j][r] for j in J for r in R) <= packing_density * v_i_ma[i]
            model.addConstr(cons10, name=f"Constraint_10_{i}_{b}")
            
            
            
            
            
   #   # for BVC and BBA only           
   #  # Define constraint (11)
   #  for i in I:
   #      for b in B_i[i]:
   #          cons11= H[i][b] >= quicksum(v_j_part[j] * X[i][b][j][r] for r in R for j in J) / (packing_density * L_i[i] * W_i[i])
   #          model.addConstr(cons11, name=f"Constraint_11_{i}_{b}")
            
   # #model.update()
            
            
             
                      
    # Define constraint (12): H[i][b] >= H_j^P * X[i][b][j][r] for all j, r
    for i in I:
        for b in B_i[i]:
            for j in J:
                cons12 = H[i][b] >= H_j_part[j] * quicksum(X[i][b][j][r] for r in R)
                model.addConstr(cons12, name=f"Constraint_12_{i}_{b}_{j}")
       
        
          

             
                
    # # Define constraint (13)
    # for i in I:
    #     for b in B_i[i]:
    #         cons26 =  H[i][b] <= H_i[i] + bigM * (1 - quicksum(Y[i][b][r] for r in R))
    #         model.addConstr(cons26, name=f"Constraint_26_{i}_{b}")
            
            
    # Define constraint (13)
    for i in I:
        for b in B_i[i]:
            cons13 =  H[i][b] <= H_i[i] * quicksum(Y[i][b][r] for r in R)
            model.addConstr(cons13, name=f"Constraint_13_{i}_{b}")
            
            

    
    
    # #Define constraint (14)
    
    for i in I:
        for b in B_i[i]:
            model.addConstr(
                E[i][b] == quicksum(v_j_part[j] * X[i][b][j][r] for j in J for r in R) / (packing_density * v_i_ma[i]),
                name=f"Constraint_14_{i}_{b}")
            
    model.update()
    
    
    
    
    # Define constraint (15)
    for i in I:
        for b in B_i[i]:
            for r in R:
                cons15 = P[i][b] >= (tau_ir[i][r] * (H[i][b] / LT_i[i])) + pi_ir[i][r] * quicksum(X[i][b][j][r] * v_j_part[j] for j in J) - \
                bigM * (1 - Y[i][b][r])
                model.addConstr(cons15, name=f"Constraint_15_{i}_{b}_{r}")
                
                # cons21_b = P[i][b] <= (tau_ir[i][r] * (H[i][b] / LT_i[i])) + pi_ir[i][r] * quicksum(X[i][b][j][r] * v_j_part[j] for j in J)
                # model.addConstr(cons21_b, name=f"Constraint_21_b_{i}_{b}_{r}")

  

                            
    # Define constraint (16)
    for i in I:
        cons16 = C_batch[i][1] >= a_i[i] + P[i][1] + SET - bigM * (1 - quicksum(Y[i][1][r] for r in R))
        model.addConstr(cons16, name=f"Constraint_16_{i}_{1}")
    
    
            
            
    # Define constraint (17)
    for i in I:
        for b in B_i[i]:
            if b > 1:
                model.addConstr(
                    C_batch[i][b] >=
                    C_batch[i][b-1]
                    + P[i][b]
                    + SET
                    + quicksum(
                        st[r_prime][r] * Q[i][b-1][r_prime][b][r]
                        for r_prime in R
                        for r in R
                        if r != r_prime
                    )
                    - bigM * (
                        1 - quicksum(Y[i][b][r] for r in R)
                    ),
                    name=f"Constraint_17_{i}_{b}"
                )
                   
                         
            
    # Define constraint (18)
    for i in I:
        for j in J:
            for b in B_i[i]:
                cons18 = C_batch[i][b] >= r_j[j] + P[i][b] - bigM * (1 - quicksum(X[i][b][j][r] for r in R))
                model.addConstr(cons18,  name=f"Constraint_18_{i}_{j}_{b}")
                

            
        
    # Define constraint (19)
    for i in I:
        for j in J:
            for b in B_i[i]:
                cons19 = C_job[j] >= C_batch[i][b] - bigM * (1 - quicksum(X[i][b][j][r] for r in R))
                model.addConstr(cons19, name=f"Constraint_19_{i}_{j}_{b}")   
                



    # Define constraint (20)
    # Define tardiness
    for j in J:
        
        cons20 = T[j] >=  C_job[j] - d_j[j]
        model.addConstr(cons20 , name=f"cons20_{j}")
        
        
        
        
    # for TPA only
    # Constraint (21)
    for i in I:
        for b in B_i[i]:
            cons21 = quicksum(A_j_part[j] * X[i][b][j][r] for j in J for r in R) <= (packing_density * L_i[i] * W_i[i])
            model.addConstr(cons21 , name=f"Constraint_21_{i}_{b}")
                         
            
        
    ################################################### Objective Function ####################################

    # Define the objective function components
    term1 = quicksum(c_j_prod[j] * C_job[j] for j in J)
    term2 = quicksum(c_j_late[j] * T[j] for j in J)
    term3 = quicksum((c_j_rej * (1- quicksum(X[i][b][j][r] for i in I for r in R for b in B_i[i])))for j in J)
    term4 = c_emp * quicksum(quicksum(Y[i][b][r] for r in R) - E[i][b] for i in I for b in B_i[i])
    
    

    # Set the objective function
    model.setObjective(term1 + term2 + term3 + term4, GRB.MINIMIZE)

    model.update()  # Integrate new variables

    # Return the model and variables
    variables = {
        'X': X,
        'Y': Y,
        'Q': Q,
        'C_batch': C_batch,
        'C_job': C_job,
        'T': T,
        'P': P,
        'H': H,
        'E': E,
    }
    return model, variables







