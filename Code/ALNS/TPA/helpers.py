#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 14:22:46 2026

@author: parisa
"""


import copy


# ------------------------------------------------------------
# Helper: get rejected jobs
# ------------------------------------------------------------
def get_rejected_jobs(solution, data):
    J = data['J']

    rejected_jobs = [
        job for job in J
        if solution[job][0] is None or solution[job][1] is None]

    return rejected_jobs




# ------------------------------------------------------------
# Helper: build current batch loads
# ------------------------------------------------------------
def build_batch_loads(solution, data):
    J = data['J']
    I = data['I']
    B_i = data['B_i']
    job_material = data['job_material']
    v_j_part = data['v_j_part']
    A_j_part = data['A_j_part']
    s_j_prime = data['s_j_prime']
    H_j_part = data['H_j_part']

    batch_volume = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_weight = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_material = {machine: [None] * len(B_i[machine]) for machine in I}
    batch_height = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_area = {machine: [0] * len(B_i[machine]) for machine in I}
    
    for job in J:
        batch = solution[job][0]
        machine = solution[job][1]

        if batch is None or machine is None:
            continue

        batch_volume[machine][batch - 1] += v_j_part[job]
        batch_area[machine][batch - 1] += A_j_part[job]
        batch_weight[machine][batch - 1] += s_j_prime[job]
        batch_material[machine][batch - 1] = job_material[job]
        batch_height[machine][batch - 1] = max(
            batch_height[machine][batch - 1],
            H_j_part[job]
        )

    return batch_volume, batch_weight, batch_material, batch_height, batch_area





# ------------------------------------------------------------
# Helper: build remaining raw material inventory
# ------------------------------------------------------------
def build_remaining_material(solution, data):
    J = data['J']
    IL_r = data['IL_r']
    job_material = data['job_material']
    s_j_prime = data['s_j_prime']

    remaining_material = copy.deepcopy(IL_r)

    for job in J:
        batch = solution[job][0]
        machine = solution[job][1]

        if batch is None or machine is None:
            continue

        raw_material = job_material[job]
        remaining_material[raw_material] -= s_j_prime[job]

    return remaining_material




# ------------------------------------------------------------
# Helper: get same-material active batches on a machine
# ------------------------------------------------------------
def get_same_material_batches(solution, data, machine, raw_material):
    J = data['J']
    job_material = data['job_material']

    same_material_batches = []

    active_batches = sorted(set(
        solution[job][0]
        for job in J
        if solution[job][1] == machine and solution[job][0] is not None
    ))

    for batch in active_batches:
        jobs_in_batch = [
            job for job in J
            if solution[job][1] == machine and solution[job][0] == batch
        ]

        if not jobs_in_batch:
            continue

        batch_material = job_material[jobs_in_batch[0]]

        if batch_material == raw_material:
            same_material_batches.append(batch)

    return same_material_batches




# ------------------------------------------------------------
# Helper: check BVC batch feasibility after inserting one job
# ------------------------------------------------------------
def feasible_batch_after_insertion(
    data, job, machine, current_volume, current_height, current_area
):
    v_j_part = data['v_j_part']
    A_j_part = data['A_j_part']
    H_j_part = data['H_j_part']
    L_i = data['L_i']
    W_i = data['W_i']
    H_i = data['H_i']
    v_i_ma = data['v_i_ma']
    packing_density = data['packing_density']

    new_volume = current_volume + v_j_part[job]
    new_area = current_area + A_j_part[job]
    new_height = max(current_height, H_j_part[job])
    tolerance = 1e-6

    if new_volume > packing_density * v_i_ma[machine] + tolerance:
        return False

    if new_height > H_i[machine] + tolerance:
        return False

    if new_area > packing_density * L_i[machine] * W_i[machine] + tolerance:
        return False

    return True





    





