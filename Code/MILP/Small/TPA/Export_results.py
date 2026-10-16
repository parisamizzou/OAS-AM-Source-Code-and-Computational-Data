#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 13:50:42 2024

@author: parisa
"""



# export_results.py

import pandas as pd
from gurobipy import GRB



def export_results(data, variables, model, filename="results.xlsx"):
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Export each parameter to a separate sheet
        
        

        # Export objective function value
        pd.DataFrame([{'Objective Value': round(model.ObjVal, 5)}]).to_excel(writer, sheet_name='Objective', index=False)

        # Export optimality gap
        pd.DataFrame([{'MIP Gap (%)': round(model.MIPGap * 100, 5)}]).to_excel(writer, sheet_name='Optimality_Gap', index=False)
        
        # **Export Optimality Status**
        # Check if the model status is optimal
        if model.Status == GRB.OPTIMAL:
            optimality_status = 'Optimal'
        else:
            optimality_status = 'Not Optimal'

        # Export the optimality status to a new sheet
        pd.DataFrame([{'Optimality Status': optimality_status}]).to_excel(writer, sheet_name='Optimality_Status', index=False)

     

        pd.DataFrame([data['n']], columns=['n']).to_excel(writer, sheet_name='n', index=False)
        pd.DataFrame([data['m']], columns=['m']).to_excel(writer, sheet_name='m', index=False)
        pd.DataFrame([data['w']], columns=['w']).to_excel(writer, sheet_name='w', index=False)
        
        # Export the m_jr 
        m_jr_df = pd.DataFrame(data['m_jr']).T  # Transpose to match the expected format
        m_jr_df.to_excel(writer, sheet_name='m_jr', index=True)
        
        el_ir_df = pd.DataFrame(data['el_ir']).T  # Transpose for better formatting
        el_ir_df.to_excel(writer, sheet_name='el_ir', index=True)
        
        pd.DataFrame([data['bigM']], columns=['bigM']).to_excel(writer, sheet_name='bigM', index=False)
        pd.DataFrame(data['s_j'].items(), columns=['j', 's_j']).to_excel(writer, sheet_name='s_j', index=False)
        pd.DataFrame(data['s_j_prime'].items(), columns=['j', 's_j_prime']).to_excel(writer, sheet_name='s_j_prime', index=False)
        pd.DataFrame(data['rho_r'].items(), columns=['r', 'rho_r']).to_excel(writer, sheet_name='rho_r', index=False)
        pd.DataFrame(data['H_j_part'].items(), columns=['j', 'H_j_part']).to_excel(writer, sheet_name='H_j_part', index=False)
        pd.DataFrame(data['A_j_part'].items(), columns=['j', 'A_j_part']).to_excel(writer, sheet_name='A_j_part', index=False)
        pd.DataFrame(data['phi_j'].items(), columns=['j', 'phi_j']).to_excel(writer, sheet_name='phi_j', index=False)

        # Export v_j_part (Volume of part j)
        pd.DataFrame(data['v_j_part'].items(), columns=['j', 'v_j_part']).to_excel(writer, sheet_name='v_j_part', index=False)
        
        pd.DataFrame(data['v_j_BB'].items(), columns=['j', 'v_j_BB']).to_excel(writer, sheet_name='v_j_BB', index=False)


        # Export job_material dictionary
        job_material_df = pd.DataFrame(list(data['job_material'].items()), columns=['Job', 'Material'])
        job_material_df.to_excel(writer, sheet_name='job_material', index=False)

        pd.DataFrame(data['IL_r'].items(), columns=['r', 'IL_r']).to_excel(writer, sheet_name='IL_r', index=False)

        # Export SET
        pd.DataFrame([data['SET']], columns=['SET']).to_excel(writer, sheet_name='SET', index=False)
        
        pd.DataFrame([data['packing_density']], columns=['packing_density']).to_excel(writer, sheet_name='packing_density', index=False)


        pd.DataFrame([data['material_coef']], columns=['material_coef']).to_excel(writer, sheet_name='material_coef', index=False)


        # Export st (sequence-dependent setup time)
        st_df = pd.DataFrame(data['st']).T  # Transpose for better formatting
        st_df.to_excel(writer, sheet_name='st', index=True)
        
        # Export a_i (Machine availability time)
        pd.DataFrame(data['a_i'].items(), columns=['i', 'a_i']).to_excel(writer, sheet_name='a_i', index=False)
        
        # Export r_j (Release time of part j)
        pd.DataFrame(data['r_j'].items(), columns=['j', 'r_j']).to_excel(writer, sheet_name='r_j', index=False)
        
        # Export d_j (Due date of part j)
        pd.DataFrame(data['d_j'].items(), columns=['j', 'd_j']).to_excel(writer, sheet_name='d_j', index=False)
        
        
        pd.DataFrame(data['L_i'].items(), columns=['i', 'L_i']).to_excel(writer, sheet_name='L_i', index=False)
        pd.DataFrame(data['W_i'].items(), columns=['i', 'W_i']).to_excel(writer, sheet_name='W_i', index=False)
        pd.DataFrame(data['H_i'].items(), columns=['i', 'H_i']).to_excel(writer, sheet_name='H_i', index=False)
        
        # Export v_i_ma (Volume of machine i)
        pd.DataFrame(data['v_i_ma'].items(), columns=['i', 'v_i_ma']).to_excel(writer, sheet_name='v_i_ma', index=False)
        
        # Export pi_ir (Printing time of machine i for a unit volume of raw material r)
        pi_ir_df = pd.DataFrame(data['pi_ir']).T  # Transpose for better formatting
        pi_ir_df.to_excel(writer, sheet_name='pi_ir', index=True)
        
        # Export tau_ir (Recoating time of machine i for a layer of raw material r)
        tau_ir_df = pd.DataFrame(data['tau_ir']).T  # Transpose for better formatting
        tau_ir_df.to_excel(writer, sheet_name='tau_ir', index=True)
        
        # Export LT_i (Layer thickness)
        pd.DataFrame(data['LT_i'].items(), columns=['i', 'LT_i']).to_excel(writer, sheet_name='LT_i', index=False)
        
        # Export c_j_prod (Production costs for each unit of time)
        pd.DataFrame(data['c_j_prod'].items(), columns=['j', 'c_j_prod']).to_excel(writer, sheet_name='c_j_prod', index=False)
        
        # Export c_j_late (Lateness costs for each unit of time)
        pd.DataFrame(data['c_j_late'].items(), columns=['j', 'c_j_late']).to_excel(writer, sheet_name='c_j_late', index=False)
        
        # Export c_j_rej (Unit rejection cost of part j)
        pd.DataFrame([data['c_j_rej']], columns=['c_j_rej']).to_excel(writer, sheet_name='c_j_rej', index=False)
        
        # Export c_emp (Penalty cost for unused capacity of any machine)
        pd.DataFrame([data['c_emp']], columns=['c_emp']).to_excel(writer, sheet_name='c_emp', index=False)
        
        # Export B_i (Batches for each machine)
        B_i_df = pd.DataFrame({i: pd.Series(b) for i, b in data['B_i'].items()})
        B_i_df.to_excel(writer, sheet_name='B_i', index=False)


        
        # Export decision variables (X)
        X_df = pd.DataFrame([{**{'i': i, 'b': b, 'j': j, 'r': r}, 'value': variables['X'][i][b][j][r].X}
                             for i in data['I'] for b in data['B_i'][i] for j in data['J'] for r in data['R']
                             if variables['X'][i][b][j][r].X != 0])
        X_df.to_excel(writer, sheet_name='X_variables', index=False)
        
        
        # Export decision variables (Y)
        Y_df = pd.DataFrame([{**{'i': i, 'b': b, 'r': r}, 'value': variables['Y'][i][b][r].X}
                             for i in data['I'] for b in data['B_i'][i] for r in data['R']
                             if variables['Y'][i][b][r].X != 0])
        Y_df.to_excel(writer, sheet_name='Y_variables', index=False)
        
        
        # Export decision variables (Q)
        Q_df = pd.DataFrame([{**{'i': i, 'b_prev': b-1, 'r_prime': r_prime, 'b': b, 'r': r}, 'value': variables['Q'][i][b-1][r_prime][b][r].X}
                              for i in data['I'] for b in range(2, len(data['B_i'][i]) + 1) 
                              for r_prime in data['R'] for r in data['R']
                              if r != r_prime and variables['Q'][i][b-1][r_prime][b][r].X != 0])
        Q_df.to_excel(writer, sheet_name='Q_variables', index=False)

        # Export completion times (C_batch)
        C_batch_df = pd.DataFrame([{**{'i': i, 'b': b}, 'value': variables['C_batch'][i][b].X}
                                   for i in data['I'] for b in data['B_i'][i]])
        C_batch_df.to_excel(writer, sheet_name='C_batch', index=False)



        # Export job completion times (C_job)
        C_job_df = pd.DataFrame([{**{'j': j}, 'value': variables['C_job'][j].X} for j in data['J']])
        C_job_df.to_excel(writer, sheet_name='C_job', index=False)

        # Export lateness (T)
        T_df = pd.DataFrame([{**{'j': j}, 'value': variables['T'][j].X} for j in data['J']])
        T_df.to_excel(writer, sheet_name='T', index=False)

        # Export processing times (P)
        P_df = pd.DataFrame([{**{'i': i, 'b': b}, 'value': variables['P'][i][b].X}
                             for i in data['I'] for b in data['B_i'][i]])
        P_df.to_excel(writer, sheet_name='P', index=False)
        
        
        # Export batch heights (H)
        H_df = pd.DataFrame([{**{'i': i, 'b': b}, 'value': variables['H'][i][b].X}
                             for i in data['I'] for b in data['B_i'][i]])
        H_df.to_excel(writer, sheet_name='H', index=False)

        # Export unused capacity (E)
        E_df = pd.DataFrame([{**{'i': i, 'b': b}, 'value': variables['E'][i][b].X}
                             for i in data['I'] for b in data['B_i'][i]])
        E_df.to_excel(writer, sheet_name='E', index=False)


        

    print(f"Results successfully exported to {filename}")






    









