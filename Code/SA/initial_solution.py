#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 14:45:40 2024

@author: parisa
"""




import random


# Generate an initial feasible solution for BVC
def initial_solution(data, seed):
    # Local generator: does not reset global random state
    rng = random.Random(seed)

    J = data['J']
    I = data['I']
    B_i = data['B_i']
    IL_r = data['IL_r']
    job_material = data['job_material']
    s_j_prime = data['s_j_prime']
    el_ir = data['el_ir']

    v_j_part = data['v_j_part']
    H_j_part = data['H_j_part']
    v_i_ma = data['v_i_ma']
    L_i = data['L_i']
    W_i = data['W_i']
    H_i = data['H_i']
    packing_density = data['packing_density']

    tolerance = 1e-6
    
    # Rejected/unassigned jobs remain [None, None]
    solution = {job: [None, None] for job in J}

    # Copy inventory so the original data are not modified
    remaining_material = IL_r.copy()

    job_list = list(J)
    rng.shuffle(job_list)
    
    # Initialize batch tracking structures
    batch_volume = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_weight = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_height = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_material = {machine: [None] * len(B_i[machine]) for machine in I}
    
    # Machine assignment to jobs
    for job in job_list:
        raw_material = job_material[job]

        if remaining_material[raw_material] + tolerance < s_j_prime[job]:
            continue

        eligible_machines = [
            machine for machine in I
            if el_ir[machine][raw_material] == 1
        ]

        rng.shuffle(eligible_machines)

        if not eligible_machines:
            continue

        assigned = False
        
        # First try assigning the job to existing batches
        for machine in eligible_machines:
            assigned_batches = list(set(
                solution[j][0]
                for j in J
                if solution[j][1] == machine
                and solution[j][0] is not None
            ))

            rng.shuffle(assigned_batches)
            
            # Try assigning the job to an existing batch
            for batch in assigned_batches:
                if batch_material[machine][batch - 1] != raw_material:
                    continue

                new_volume = v_j_part[job] + batch_volume[machine][batch - 1]
                # Previous height already covers existing parts
                new_height = max(
                    batch_height[machine][batch - 1],
                    H_j_part[job],
                    new_volume / (
                        packing_density
                        * L_i[machine]
                        * W_i[machine]
                    )
                )

                if (new_volume <= packing_density * v_i_ma[machine] + tolerance and new_height <= H_i[machine] + tolerance):
                    # Assign job to the batch and machine
                    solution[job] = [batch, machine]

                    batch_volume[machine][batch - 1] = new_volume
                    batch_weight[machine][batch - 1] += s_j_prime[job]
                    batch_height[machine][batch - 1] = new_height
                    batch_material[machine][batch - 1] = raw_material

                    remaining_material[raw_material] -= s_j_prime[job]
                    assigned = True
                    break

            if assigned:
                break

        # If not assigned, try opening a new batch on every eligible machine
        if not assigned:
            for chosen_machine in eligible_machines:
                active_batches = list(set(
                    solution[j][0]
                    for j in J
                    if solution[j][1] == chosen_machine
                    and solution[j][0] is not None
                ))

                if active_batches:
                    new_batch = max(active_batches) + 1
                else:
                    new_batch = 1

                if new_batch not in B_i[chosen_machine]:
                    continue

                new_volume = v_j_part[job]
                
                new_height = max(
                    H_j_part[job],
                    new_volume / (
                        packing_density
                        * L_i[chosen_machine]
                        * W_i[chosen_machine]
                    )
                )

                if (new_volume <= packing_density * v_i_ma[chosen_machine] + tolerance and new_height <= H_i[chosen_machine] + tolerance):
                    solution[job] = [new_batch, chosen_machine]

                    batch_volume[chosen_machine][new_batch - 1] = new_volume
                    batch_weight[chosen_machine][new_batch - 1] = s_j_prime[job]
                    batch_height[chosen_machine][new_batch - 1] = new_height
                    batch_material[chosen_machine][new_batch - 1] = raw_material

                    remaining_material[raw_material] -= s_j_prime[job]
                    assigned = True
                    break

    return solution





