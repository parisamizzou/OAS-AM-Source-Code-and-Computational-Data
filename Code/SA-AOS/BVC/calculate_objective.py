#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 15:53:59 2024

@author: parisa
"""





# Calculate the objective function for BVC
def calculate_objective(solution, data):
    J = data['J']
    I = data['I']
    B_i = data['B_i']
    c_j_rej = data['c_j_rej']
    r_j = data['r_j']
    job_material = data['job_material']
    s_j_prime = data['s_j_prime']
    v_j_part = data['v_j_part']
    H_j_part = data['H_j_part']
    L_i = data['L_i']
    W_i = data['W_i']
    pi_ir = data['pi_ir']
    tau_ir = data['tau_ir']
    LT_i = data['LT_i']
    a_i = data['a_i']
    SET = data['SET']
    st = data['st']
    d_j = data['d_j']
    c_j_prod = data['c_j_prod']
    c_j_late = data['c_j_late']
    c_emp = data['c_emp']
    v_i_ma = data['v_i_ma']
    packing_density = data['packing_density']
    
    total_production_cost = 0
    total_lateness_cost = 0
    total_rejection_cost = 0
    total_unused_capacity_cost = 0
    total_rejected_jobs = 0

    job_completion_time = {j: 0 for j in J}
    job_tardiness = {j: 0 for j in J}
    
    batch_completion_time = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_processing_time = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_material = {machine: [None] * len(B_i[machine]) for machine in I}
    batch_weight = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_volume = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_height = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_unused_capacity = {machine: [0] * len(B_i[machine]) for machine in I}
    
    
  
    
    # Calculate rejection cost and check assignment validity
    for job in J:
        batch = solution[job][0]
        machine = solution[job][1]

        if batch is None and machine is None:
            total_rejected_jobs += 1 
            total_rejection_cost += c_j_rej
            continue
        
        if batch is None or machine is None:
            raise ValueError(f"Job {job} has an incomplete assignment.")


        if machine not in I:
            raise ValueError(f"Job {job} is assigned to invalid machine {machine}.")
            
        if batch not in B_i[machine]:
            raise ValueError(f"Batch {batch} is not allowed on machine {machine}.")
            
    # Acceptance rate as a percentage
    total_jobs = len(J)
    total_accepted_jobs = total_jobs - total_rejected_jobs
    
   
    acceptance_rate = (
        100 * (total_accepted_jobs / total_jobs)
        if total_jobs > 0
        else 0.0)
            
    for machine in I:
        for batch in sorted(B_i[machine]):
            # List of parts assigned to the batch b of machine i
            # Get unique jobs assigned to this machine and batch
            assigned_jobs = [
                job for job in J
                if solution[job][1] == machine
                and solution[job][0] == batch]

            if not assigned_jobs:
                continue

            # All jobs in a batch must have the same material
            raw_material = job_material[assigned_jobs[0]]
            
            if any(job_material[job] != raw_material for job in assigned_jobs):
                raise ValueError(
                    f"Batch {batch} on machine {machine} "
                    f"contains different materials.")

            batch_material[machine][batch - 1] = raw_material
            max_r_j = max(r_j[job] for job in assigned_jobs)  # Find the maximum release time of jobs
            batch_weight[machine][batch - 1] = sum(s_j_prime[job] for job in assigned_jobs)
            batch_volume[machine][batch - 1] = sum(v_j_part[job] for job in assigned_jobs)
            
            
            # BVC: Minimum height satisfying both height lower bounds
            volume_based_height = (
                batch_volume[machine][batch - 1]
                / (packing_density * L_i[machine] * W_i[machine]))

            tallest_part = max(H_j_part[job] for job in assigned_jobs)

            batch_height[machine][batch - 1] = max(volume_based_height, tallest_part)
            
            # Processing time
            processing_time = (
                tau_ir[machine][raw_material]
                * batch_height[machine][batch - 1]
                / LT_i[machine]
                + pi_ir[machine][raw_material]
                * batch_volume[machine][batch - 1]
            )

            batch_processing_time[machine][batch - 1] = processing_time
            
            # Completion time
            # First batch
            if batch == 1:
                completion_time = max(a_i[machine] + SET, max_r_j) + processing_time
            else:
                # for other batches
                previous_material = batch_material[machine][batch - 2] # raw material of previous batch
                
                if previous_material is None:
                    raise ValueError(
                        f"Machine {machine} has an empty batch "
                        f"immediately before active batch {batch}.")

                # The MILP adds a changeover only for different materials
                changeover_time = (
                    st[previous_material][raw_material]
                    if previous_material != raw_material
                    else 0)

                completion_time = max(batch_completion_time[machine][batch - 2] + SET + changeover_time, max_r_j) + processing_time

            batch_completion_time[machine][batch - 1] = completion_time
            
            # Completion and tardiness costs of accepted jobs
            for job in assigned_jobs:
                job_completion_time[job] = completion_time
                job_tardiness[job] = max(0, completion_time - d_j[job])
                total_production_cost += (c_j_prod[job] * completion_time)
                total_lateness_cost += (c_j_late[job] * job_tardiness[job])

            # Unused-capacity fraction for an active batch: 1 - E_ib
            utilization = (batch_volume[machine][batch - 1]/ (packing_density * v_i_ma[machine]))
            batch_unused_capacity[machine][batch - 1] = (1 - utilization)
            total_unused_capacity_cost += (c_emp * batch_unused_capacity[machine][batch - 1]) 
    Total_cost = (
        total_production_cost
        + total_lateness_cost
        + total_rejection_cost
        + total_unused_capacity_cost
    )
    
    return (
        Total_cost,
        total_production_cost,
        total_lateness_cost,
        total_rejection_cost,
        total_unused_capacity_cost,
        job_completion_time,
        batch_completion_time,
        batch_processing_time,
        batch_weight,
        batch_volume,
        batch_height,
        batch_unused_capacity,
        job_tardiness,
        total_rejected_jobs,
        acceptance_rate
    )
    
    
    
    


                 
                

