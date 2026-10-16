#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 18:46:23 2024

@author: parisa
"""





# Check for sequential batch assignment
def feasibility_6 (data, solution, machines=None):
    I = machines if machines is not None else data['I']
    J = data['J']  
    for machine in I:
        assigned_batches = list(set([solution[job][0] for job in J if solution[job][1] == machine and solution[job][0] is not None]))
        # Check if the assigned_batch is not empty
        if assigned_batches:
            for batch in assigned_batches:
                # Check if a batch is formed, its previous batch aslso should be formed
                if batch != 1:
                    previous_batches = list(range(1, batch))
                    for b in previous_batches:
                        if b not in assigned_batches:
                            #print(f"Feasibility check failed: Machine {machine} has missing batch before {batch}.")
                            return False
    return True


#feasibility_6 (data, solution, machines= [1, 2])   

                   


# Check machine eligibility for the job's raw material
def feasibility_5 (data, solution, machines=None, jobs=None):
    valid_machines = set(data['I'])
    machines_to_check = (valid_machines if machines is None else set(machines))
    jobs_to_check = data['J'] if jobs is None else jobs

    m_jr = data['m_jr']
    el_ir = data['el_ir']
    R = data['R']
    
    for job in jobs_to_check:
        batch, machine = solution[job]

        # Rejected job
        if batch is None and machine is None:
            continue

        # Accepted jobs require both values
        if batch is None or machine is None:
            # print(
            #     f"Feasibility check failed: Job {job} "
            #     f"has an incomplete assignment."
            # )
            return False

        # Invalid machines must never be ignored
        if machine not in valid_machines:
            # print(
            #     f"Feasibility check failed: Job {job} "
            #     f"is assigned to invalid machine {machine}."
            # )
            return False

        # Skip valid machines outside a requested local scope
        if machine not in machines_to_check:
            continue

        # Derive material from m_jr, which is what the MILP uses
        job_materials = [
            raw_material
            for raw_material in R
            if m_jr[job][raw_material] == 1
        ]

        if len(job_materials) != 1:
            # print(
            #     f"Feasibility check failed: Job {job} must have exactly "
            #     f"one raw material, but has {job_materials}."
            # )
            return False

        raw_material = job_materials[0]

        if el_ir[machine][raw_material] != 1:
            # print(
            #     f"Feasibility check failed: Machine {machine} cannot process "
            #     f"raw material {raw_material} for job {job}."
            # )
            return False

    return True

#feasibility_5 (data, solution, [1,2], [1,5,6])   




    
    


# # for TPA only
# # Check total volume feasibility for each batch
# def feasibility_24 (data, solution, machines=None, batches=None):
#     I = machines if machines is not None else data['I']
#     J = data['J']
#     B_i = data['B_i']
#     v_j_part = data['v_j_part']
#     v_i_ma = data['v_i_ma']
#     packing_density = data['packing_density']
    
#     for machine in I:
#         if batches is None:
#             assigned_batches = {
#                 solution[job][0]
#                 for job in J
#                 if solution[job][1] == machine and solution[job][0] is not None
#             }
#         else:
#             assigned_batches = set(batches)

#         for batch in assigned_batches:
#             if batch not in B_i[machine]:
#                 # print(
#                 #     f"Feasibility check failed: Batch {batch} "
#                 #     f"is not allowed on machine {machine}."
#                 # )
#                 return False

#             batch_volume = sum(
#                 v_j_part[job]
#                 for job in J
#                 if solution[job][1] == machine and solution[job][0] == batch
#             )

#             capacity = packing_density * v_i_ma[machine]

#             if batch_volume > capacity + 1e-6:
#                 # print(
#                 #     f"Feasibility check failed: Batch {batch} on machine {machine} "
#                 #     f"exceeds volume capacity. Used {batch_volume}, capacity {capacity}."
#                 # )
#                 return False

#     return True
                       
# #feasibility_24 (data, solution, machines=[1,3], batches = [1])  








# for BBA only
# Check total volume feasibility for each batch
def feasibility_1 (data, solution, machines=None, batches=None):
    I = machines if machines is not None else data['I']
    J = data['J']
    v_j_BB = data['v_j_BB']
    v_i_ma = data['v_i_ma']
    packing_density = data['packing_density']
    
    for machine in I:
        if batches is None:
            assigned_batches = {
                solution[job][0]
                for job in J
                if solution[job][1] == machine
                and solution[job][0] is not None}
        else:
            assigned_batches = set(batches)

        for batch in assigned_batches:
            if batch not in data['B_i'][machine]:
                return False
            batch_volume = 0

            for job in J:
                if (solution[job][1] == machine and solution[job][0] == batch):
                    batch_volume += v_j_BB[job]

            if batch_volume > packing_density * v_i_ma[machine] + 1e-6:
                # print(
                #     f"Feasibility check failed: Batch {batch} "
                #     f"exceeds the volume capacity of machine {machine} "
                #     f"at packing density {packing_density}."
                # )
                return False

    return True
                    
#feasibility_1 (data, solution, machines=[1,3], batches = [1])    




   
 # Check raw material consistency within the batch
def feasibility_4 (data, solution, machines=None, batches=None):
    I = machines if machines is not None else data['I']
    J = data['J']
    job_material = data['job_material']
    B_i = data['B_i']
    
    for machine in I:
        if batches is None:
            assigned_batches = {
                solution[job][0]
                for job in J
                if solution[job][1] == machine
                and solution[job][0] is not None}
        else:
            assigned_batches = set(batches)

        for batch in assigned_batches:
            if batch not in B_i[machine]:
                # print(
                #     f"Feasibility check failed: Batch {batch} "
                #     f"is not allowed on machine {machine}."
                # )
                return False

            materials_in_batch = {
                job_material[job]
                for job in J
                if solution[job][1] == machine and solution[job][0] == batch
            }

            if len(materials_in_batch) > 1:
                # print(
                #     f"Feasibility check failed: Batch {batch} "
                #     f"on machine {machine} contains different raw materials."
                # )
                return False

    return True

#feasibility_4 (data, solution, machines=[1,3], batches = [1])  
  


                
# # for BVC only
# # Check the height feasibility of each batch
# def feasibility_26(data, solution, machines=None, batches=None):
#     I = machines if machines is not None else data['I']
#     J = data['J']
#     B_i = data['B_i']
#     v_j_part = data['v_j_part']
#     H_j_part = data['H_j_part']
#     L_i = data['L_i']
#     W_i = data['W_i']
#     H_i = data['H_i']
#     packing_density = data['packing_density']
    
#     for machine in I:
#         if batches is None:
#             assigned_batches = {
#                 solution[job][0]
#                 for job in J
#                 if solution[job][1] == machine
#                 and solution[job][0] is not None
#             }
#         else:
#             assigned_batches = set(batches)

#         for batch in assigned_batches:
#             if batch not in B_i[machine]:
#                 return False

#             batch_volume = 0
#             tallest_part = 0

#             for job in J:
#                 if (solution[job][1] == machine and solution[job][0] == batch):
#                     batch_volume += v_j_part[job]
#                     tallest_part = max(tallest_part, H_j_part[job])

#             volume_based_height = batch_volume / (packing_density * L_i[machine] * W_i[machine])

#             batch_height = max(volume_based_height, tallest_part)
#             capacity_height = H_i[machine]
            
#             if batch_height > capacity_height + 1e-6:
#                 # print(
#                 #     f"Feasibility check failed: Batch {batch} on machine {machine} "
#                 #     f"exceeds height capacity. Required {batch_height}, "
#                 #     f"capacity {capacity_height}."
#                 # )
#                 return False

#     return True
# # feasibility_26(data, solution, machines=[1, 3], batches=[1])
    
    
    
        

# for BBA only
# Check the height feasibility of each batch
def feasibility_2(data, solution, machines=None, batches=None):
    I = machines if machines is not None else data['I']
    J = data['J']
    B_i = data['B_i']
    v_j_BB = data['v_j_BB']
    H_j_part = data['H_j_part']
    L_i = data['L_i']
    W_i = data['W_i']
    H_i = data['H_i']
    packing_density = data['packing_density']

    for machine in I:
        if batches is None:
            assigned_batches = {
                solution[job][0]
                for job in J
                if solution[job][1] == machine and solution[job][0] is not None
            }
        else:
            assigned_batches = set(batches)

        for batch in assigned_batches:
            if batch not in B_i[machine]:
                # print(
                #     f"Feasibility check failed: Batch {batch} "
                #     f"is not allowed on machine {machine}."
                # )
                return False

            batch_volume = 0
            tallest_part = 0

            for job in J:
                if solution[job][1] == machine and solution[job][0] == batch:
                    batch_volume += v_j_BB[job]
                    tallest_part = max(tallest_part, H_j_part[job])

            volume_based_height = (
                batch_volume / (packing_density * L_i[machine] * W_i[machine])
            )
            batch_height = max(volume_based_height, tallest_part)
            
            if batch_height > H_i[machine] + 1e-6:
                # print(
                #     f"Feasibility check failed: Batch {batch} on machine {machine} "
                #     f"exceeds height capacity. Required {batch_height}, "
                #     f"capacity {H_i[machine]}."
                # )
                return False

    return True
            
            




# # for TPA only
# # Check the height feasibility of each batch
# def feasibility_3(data, solution, machines=None, batches=None):
#     I = machines if machines is not None else data['I']
#     J = data['J']
#     B_i = data['B_i']
#     H_j_part = data['H_j_part']
#     H_i = data['H_i']

#     for machine in I:
#         if batches is None:
#             assigned_batches = {
#                 solution[job][0]
#                 for job in J
#                 if solution[job][1] == machine
#                 and solution[job][0] is not None
#             }
#         else:
#             assigned_batches = set(batches)

#         for batch in assigned_batches:
#             if batch not in B_i[machine]:
#                 # print(
#                 #     f"Feasibility check failed: Batch {batch} "
#                 #     f"is not allowed on machine {machine}."
#                 # )
#                 return False

#             batch_height = 0

#             for job in J:
#                 if solution[job][1] == machine and solution[job][0] == batch:
#                     batch_height = max(batch_height, H_j_part[job])

#             if batch_height > H_i[machine] + 1e-6:
#                 # print(
#                 #     f"Feasibility check failed: Batch {batch} on machine {machine} "
#                 #     f"exceeds height capacity. Required {batch_height}, "
#                 #     f"capacity {H_i[machine]}."
#                 # )
#                 return False

#     return True
            
            
        




# # TPA: Check total footprint area of each batch
# def feasibility_8(data, solution, machines=None, batches=None):
#     I = machines if machines is not None else data['I']
#     J = data['J']
#     B_i = data['B_i']
#     A_j_part = data['A_j_part']
#     L_i = data['L_i']
#     W_i = data['W_i']
#     packing_density = data['packing_density']

#     for machine in I:
#         if batches is None:
#             assigned_batches = {
#                 solution[job][0]
#                 for job in J
#                 if solution[job][1] == machine
#                 and solution[job][0] is not None
#             }
#         else:
#             assigned_batches = set(batches)

#         for batch in assigned_batches:
#             if batch not in B_i[machine]:
#                 # print(
#                 #     f"Feasibility check failed: Batch {batch} "
#                 #     f"is not allowed on machine {machine}."
#                 # )
#                 return False

#             batch_area = sum(
#                 A_j_part[job]
#                 for job in J
#                 if solution[job][1] == machine and solution[job][0] == batch
#             )

#             platform_area = L_i[machine] * W_i[machine]

#             if batch_area > (packing_density * platform_area) + 1e-6:
#                 # print(
#                 #     f"Feasibility check failed: Batch {batch} on machine {machine} "
#                 #     f"exceeds platform area. Required {batch_area}, "
#                 #     f"capacity {platform_area}."
#                 # )
#                 return False

#     return True
            
           




 # Check the feasibility available raw material
def feasibility_7 (data, solution):
    I = data['I']
    J = data['J']
    R = data['R']
    B_i = data['B_i']
    s_j_prime = data['s_j_prime']
    IL_r = data['IL_r']
    job_material = data['job_material']

    used_material = {r: 0 for r in R}

    for job in J:
        batch = solution[job][0]
        machine = solution[job][1]

        # Rejected jobs consume no material
        if batch is None and machine is None:
            continue

        # Accepted jobs need both a batch and a machine
        if batch is None or machine is None:
            # print(
            #     f"Feasibility check failed: Job {job} "
            #     f"has an incomplete assignment."
            # )
            return False

        if machine not in I:
            # print(
            #     f"Feasibility check failed: Job {job} "
            #     f"is assigned to invalid machine {machine}."
            # )
            return False

        if batch not in B_i[machine]:
            # print(
            #     f"Feasibility check failed: Batch {batch} "
            #     f"is not allowed on machine {machine}."
            # )
            return False

        raw_material = job_material[job]

        if raw_material not in R:
            # print(
            #     f"Feasibility check failed: Job {job} "
            #     f"has invalid raw material {raw_material}."
            # )
            return False

        used_material[raw_material] += s_j_prime[job]

    for raw_material in R:
        if used_material[raw_material] > IL_r[raw_material] + 1e-6:
            # print(
            #     f"Feasibility check failed: Raw material {raw_material} "
            #     f"consumption exceeds inventory. Used {used_material[raw_material]}, "
            #     f"available {IL_r[raw_material]}."
            # )
            return False

    return True
            
        
            
    
    
    

                     



