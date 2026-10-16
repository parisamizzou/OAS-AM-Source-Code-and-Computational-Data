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
    v_j_BB = data['v_j_BB']
    s_j_prime = data['s_j_prime']
    H_j_part = data['H_j_part']
    L_i = data['L_i']
    W_i = data['W_i']
    packing_density = data['packing_density']

    batch_volume = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_weight = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_material = {machine: [None] * len(B_i[machine]) for machine in I}
    batch_height = {machine: [0] * len(B_i[machine]) for machine in I}
    batch_tallest_part = {machine: [0] * len(B_i[machine]) for machine in I}

    for job in J:
        batch = solution[job][0]
        machine = solution[job][1]

        if batch is None or machine is None:
            continue

        batch_volume[machine][batch - 1] += v_j_BB[job]
        batch_weight[machine][batch - 1] += s_j_prime[job]
        batch_material[machine][batch - 1] = job_material[job]
        batch_tallest_part[machine][batch - 1] = max(
            batch_tallest_part[machine][batch - 1],
            H_j_part[job]
        )

    for machine in I:
        for batch in B_i[machine]:
            volume_based_height = (
                batch_volume[machine][batch - 1]
                / (packing_density * L_i[machine] * W_i[machine])
            )

            batch_height[machine][batch - 1] = max(
                volume_based_height,
                batch_tallest_part[machine][batch - 1])

    return batch_volume, batch_weight, batch_material, batch_height



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
def feasible_batch_after_insertion(data, job, machine, current_volume, current_height):
    v_j_BB = data['v_j_BB']
    H_j_part = data['H_j_part']
    L_i = data['L_i']
    W_i = data['W_i']
    H_i = data['H_i']
    packing_density = data['packing_density']

    new_volume = current_volume + v_j_BB[job]

    volume_based_height = (
        new_volume
        / (packing_density * L_i[machine] * W_i[machine])
    )

    new_height = max(
        current_height,
        H_j_part[job],
        volume_based_height
    )

    if new_height > H_i[machine] + 1e-6:
        return False

    return True
    
    
    





