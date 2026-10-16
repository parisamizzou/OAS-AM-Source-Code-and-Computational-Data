#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 18:28:44 2024

@author: parisa
"""


import copy
import numpy as np
import random
import math

from calculate_objective import calculate_objective
from feasibility import feasibility_6
from feasibility import feasibility_5
from feasibility import feasibility_4
from feasibility import feasibility_26
from feasibility import feasibility_7

def generate_neighbor(current_solution, current_objective, iteration, data):
   
 
    J = data['J']
    I = data['I']
    R = data['R']
    B_i = data['B_i']
    job_material = data['job_material']
    el_ir = data['el_ir']
    
    
    
    
    def rep_3(solution, machines=None):
        """
        Reindex machine batch IDs so each machine uses consecutive batch labels 1..k.
    
        Example:
            Machine 1 has active batches [1, 3, 5]
            After rep_3:
            Machine 1 has active batches [1, 2, 3]
    
        Solution format:
            solution[job][0] = batch
            solution[job][1] = machine
        """
    
        J = data['J']
        I = data['I']
        B_i = data['B_i']
        
        valid_machines = set(I)
        machines_to_repair = I if machines is None else list(dict.fromkeys(machines))
    
        for machine in machines_to_repair:
            if machine not in valid_machines:
                raise ValueError(f"Invalid machine {machine} supplied to rep_3.")
    
        new_solution = copy.deepcopy(solution)
        fixed_machines = []
        
        # Validate the assignment representation before repairing labels.
        for job in J:
            if job not in new_solution:
                raise ValueError(f"Job {job} is missing from the solution.")
    
            batch, machine = new_solution[job]
    
        for machine in machines_to_repair:
            allowed_batches = sorted(B_i[machine])
            expected_allowed = list(range(1, len(allowed_batches) + 1))
    
            if allowed_batches != expected_allowed:
                raise ValueError(
                    f"B_i[{machine}] must contain consecutive batch IDs "
                    f"starting at 1; found {allowed_batches}."
                )
    
            active_batches = sorted({
                new_solution[job][0]
                for job in J
                if new_solution[job][1] == machine
            })
    
            if not active_batches:
                continue
    
            if len(active_batches) > len(allowed_batches):
                raise ValueError(
                    f"Machine {machine} has {len(active_batches)} active batches, "
                    f"but only {len(allowed_batches)} batches are allowed."
                )
    
            expected_batches = list(range(1, len(active_batches) + 1))
    
            if active_batches == expected_batches:
                continue
    
            batch_map = {
                old_batch: new_batch
                for new_batch, old_batch in enumerate(active_batches, start=1)
            }
    
            for job in J:
                batch, assigned_machine = new_solution[job]
    
                if assigned_machine == machine:
                    new_solution[job][0] = batch_map[batch]
    
            fixed_machines.append({
                'machine': machine,
                'old_labels': active_batches,
                'new_labels': expected_batches,
                'batch_map': batch_map,
            })
    
        info = {
            'fixed_machines': fixed_machines,
            'num_fixed_machines': len(fixed_machines),
        }
    
        return new_solution, info
    
    
    
    
     
    
    
    
    # Operator 1: Swap the batch and machine assignments of two jobs
    # Operator 1: Swap the assignments of two accepted jobs
    def op_1(current_solution):
        J = data['J']
        job_material = data['job_material']
        el_ir = data['el_ir']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
    
        assigned_jobs = [
            job
            for job in J
            if current_solution[job][0] is not None
            and current_solution[job][1] is not None
        ]
    
        if len(assigned_jobs) < 2:
            return current_solution
    
        jobs_by_batch = {}
        
        for job in assigned_jobs:
            batch, machine = current_solution[job]
            jobs_by_batch.setdefault((machine, batch), []).append(job)
    
        # Swapping jobs in the same batch would not change the solution.
        candidate_pairs = [
            (job1, job2)
            for index, job1 in enumerate(assigned_jobs)
            for job2 in assigned_jobs[index + 1:]
            if current_solution[job1] != current_solution[job2]
        ]
    
        if not candidate_pairs:
            return current_solution
    
        np.random.shuffle(candidate_pairs)
        
        for job1, job2 in candidate_pairs:
            batch1, machine1 = current_solution[job1]
            batch2, machine2 = current_solution[job2]
    
            affected_batches = (
                (machine1, batch1),
                (machine2, batch2),
            )
    
            swap_is_feasible = True
    
            for machine, batch in affected_batches:
                proposed_jobs = []
    
                for job in jobs_by_batch[(machine, batch)]:
                    if job == job1:
                        proposed_jobs.append(job2)
                    elif job == job2:
                        proposed_jobs.append(job1)
                    else:
                        proposed_jobs.append(job)
    
                proposed_materials = {
                    job_material[job]
                    for job in proposed_jobs
                }
    
                # Each batch may contain only one material.
                if len(proposed_materials) != 1:
                    swap_is_feasible = False
                    break
    
                raw_material = next(iter(proposed_materials))
    
                if el_ir[machine][raw_material] != 1:
                    swap_is_feasible = False
                    break
    
                proposed_volume = sum(
                    v_j_part[job]
                    for job in proposed_jobs
                )
    
                utilization = (
                    proposed_volume
                    / (packing_density * v_i_ma[machine])
                )
    
                # Enforce the MILP bound E[i,b] <= 1.
                if utilization > 1 + tolerance:
                    swap_is_feasible = False
                    break
    
                volume_based_height = (
                    proposed_volume
                    / (
                        packing_density
                        * L_i[machine]
                        * W_i[machine]
                    )
                )
    
                tallest_part = max(
                    H_j_part[job]
                    for job in proposed_jobs
                )
    
                proposed_height = max(
                    volume_based_height,
                    tallest_part,
                )
    
                if proposed_height > H_i[machine] + tolerance:
                    swap_is_feasible = False
                    break
    
            if not swap_is_feasible:
                continue
    
            neighbor_1 = copy.deepcopy(current_solution)
    
            neighbor_1[job1], neighbor_1[job2] = (
                neighbor_1[job2],
                neighbor_1[job1],
            )
    
            return neighbor_1
    
        return current_solution
    
    
    
  
   

   

    

   
    
    # Operator 11: Select two jobs with the same raw material and swap their batch and machine
    def op_11(current_solution):
        J = data['J']
        job_material = data['job_material']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
    
        assigned_jobs = [
            job
            for job in J
            if current_solution[job][0] is not None
            and current_solution[job][1] is not None
        ]
    
        if len(assigned_jobs) < 2:
            return current_solution
    
        jobs_by_batch = {}
    
        for job in assigned_jobs:
            batch, machine = current_solution[job]
            jobs_by_batch.setdefault((machine, batch), []).append(job)
    
        # Same-material pairs in different batch-machine assignments.
        candidate_pairs = [
            (job1, job2)
            for index, job1 in enumerate(assigned_jobs)
            for job2 in assigned_jobs[index + 1:]
            if job_material[job1] == job_material[job2]
            and current_solution[job1] != current_solution[job2]
        ]
    
        if not candidate_pairs:
            return current_solution
    
        np.random.shuffle(candidate_pairs)
    
        for job1, job2 in candidate_pairs:
            batch1, machine1 = current_solution[job1]
            batch2, machine2 = current_solution[job2]
    
            affected_batches = (
                (machine1, batch1),
                (machine2, batch2),
            )
    
            swap_is_feasible = True
    
            for machine, batch in affected_batches:
                proposed_jobs = []
    
                for job in jobs_by_batch[(machine, batch)]:
                    if job == job1:
                        proposed_jobs.append(job2)
                    elif job == job2:
                        proposed_jobs.append(job1)
                    else:
                        proposed_jobs.append(job)
    
                proposed_volume = sum(
                    v_j_part[job]
                    for job in proposed_jobs
                )
    
                utilization = (
                    proposed_volume
                    / (packing_density * v_i_ma[machine])
                )
    
                if utilization > 1 + tolerance:
                    swap_is_feasible = False
                    break
    
                volume_based_height = (
                    proposed_volume
                    / (
                        packing_density
                        * L_i[machine]
                        * W_i[machine]
                    )
                )
    
                tallest_part = max(
                    H_j_part[job]
                    for job in proposed_jobs
                )
    
                proposed_height = max(
                    volume_based_height,
                    tallest_part,
                )
    
                if proposed_height > H_i[machine] + tolerance:
                    swap_is_feasible = False
                    break
    
            if not swap_is_feasible:
                continue
    
            neighbor_11 = copy.deepcopy(current_solution)
    
            neighbor_11[job1], neighbor_11[job2] = (
                neighbor_11[job2],
                neighbor_11[job1],
            )
    
            return neighbor_11
    
        return current_solution
            
        
        
        
        
        
    # Operator 2: Remove one accepted job
    def op_2(current_solution):
        J = data['J']
    
        assigned_jobs = [
            job
            for job in J
            if current_solution[job][0] is not None
            and current_solution[job][1] is not None
        ]
    
        if not assigned_jobs:
            return current_solution
    
        job_to_remove = np.random.choice(assigned_jobs)
        _, affected_machine = current_solution[job_to_remove]
    
        neighbor_2 = copy.deepcopy(current_solution)
        neighbor_2[job_to_remove] = [None, None]
    
        neighbor_2, _ = rep_3(
            neighbor_2,
            machines=[affected_machine],
        )

        return neighbor_2








        
    # Operator 12: Remove 10% of accepted jobs
    def op_12(current_solution):
        J = data['J']
    
        assigned_jobs = [
            job
            for job in J
            if current_solution[job][0] is not None
            and current_solution[job][1] is not None
        ]
    
        if not assigned_jobs:
            return current_solution
    
        num_jobs_to_remove = math.ceil(0.1 * len(assigned_jobs))
    
        jobs_to_remove = np.random.choice(
            assigned_jobs,
            size=num_jobs_to_remove,
            replace=False,
        )
    
        affected_machines = {
            current_solution[job][1]
            for job in jobs_to_remove
        }
    
        neighbor_12 = copy.deepcopy(current_solution)
        
        for job in jobs_to_remove:
            neighbor_12[job] = [None, None]
    
        neighbor_12, _ = rep_3(
            neighbor_12,
            machines=affected_machines,
        )
    
        return neighbor_12
    
    
    
    
    
    
 
    
    
    
    # Operator 3: Insert one rejected job into a feasible batch
    def op_3(current_solution):
        J = data['J']
        I = data['I']
        R = data['R']
        B_i = data['B_i']
    
        job_material = data['job_material']
        el_ir = data['el_ir']
        s_j_prime = data['s_j_prime']
        IL_r = data['IL_r']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
        
        unassigned_jobs = []
        used_material = {raw_material: 0 for raw_material in R}
        jobs_by_batch = {}
        active_batches_by_machine = {
            machine: []
            for machine in I
        }
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                unassigned_jobs.append(job)
                continue
    
            if batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
    
            raw_material = job_material[job]
            used_material[raw_material] += s_j_prime[job]
    
            key = (machine, batch)
            jobs_by_batch.setdefault(key, []).append(job)
    
        if not unassigned_jobs:
            return current_solution
        
        for machine, batch in jobs_by_batch:
            active_batches_by_machine[machine].append(batch)
    
        for machine in I:
            active_batches_by_machine[machine] = sorted(
                set(active_batches_by_machine[machine])
            )
    
        batch_material = {}
        batch_volume = {}
        batch_tallest_part = {}
    
        for key, jobs in jobs_by_batch.items():
            batch_material[key] = job_material[jobs[0]]
    
            batch_volume[key] = sum(
                v_j_part[job]
                for job in jobs
            )
    
            batch_tallest_part[key] = max(
                H_j_part[job]
                for job in jobs
            )
    
        np.random.shuffle(unassigned_jobs)
        
        for job_to_insert in unassigned_jobs:
            material = job_material[job_to_insert]
    
            if (
                used_material[material] + s_j_prime[job_to_insert]
                > IL_r[material] + tolerance
            ):
                continue
    
            feasible_positions = []
    
            eligible_machines = [
                machine
                for machine in I
                if el_ir[machine][material] == 1
            ]
    
            for machine in eligible_machines:
                active_batches = active_batches_by_machine[machine]

                # Try existing batches with the same material.
                for batch in active_batches:
                    key = (machine, batch)
    
                    if batch_material[key] != material:
                        continue
    
                    new_volume = (
                        batch_volume[key]
                        + v_j_part[job_to_insert]
                    )
    
                    utilization = (
                        new_volume
                        / (packing_density * v_i_ma[machine])
                    )
    
                    if utilization > 1 + tolerance:
                        continue
    
                    new_tallest_part = max(
                        batch_tallest_part[key],
                        H_j_part[job_to_insert],
                    )
    
                    volume_based_height = (
                        new_volume
                        / (
                            packing_density
                            * L_i[machine]
                            * W_i[machine]
                        )
                    )
    
                    new_height = max(
                        new_tallest_part,
                        volume_based_height,
                    )
    
                    if new_height <= H_i[machine] + tolerance:
                        feasible_positions.append((batch, machine))
    
                # Try the next sequential batch.
                new_batch = (
                    max(active_batches) + 1
                    if active_batches
                    else 1
                )
    
                if new_batch not in B_i[machine]:
                    continue
    
                new_volume = v_j_part[job_to_insert]
    
                utilization = (
                    new_volume
                    / (packing_density * v_i_ma[machine])
                )
    
                if utilization > 1 + tolerance:
                    continue
    
                volume_based_height = (
                    new_volume
                    / (
                        packing_density
                        * L_i[machine]
                        * W_i[machine]
                    )
                )
    
                new_height = max(
                    H_j_part[job_to_insert],
                    volume_based_height,
                )
    
                if new_height <= H_i[machine] + tolerance:
                    feasible_positions.append((new_batch, machine))
    
            if not feasible_positions:
                continue
    
            position_index = np.random.randint(len(feasible_positions))
            new_batch, new_machine = feasible_positions[position_index]
    
            neighbor_3 = copy.deepcopy(current_solution)
            neighbor_3[job_to_insert] = [new_batch, new_machine]
    
            return neighbor_3
    
        return current_solution
    
    
    
    
    
    
    
    
    
    # Operator 13: Insert approximately 25% of rejected jobs
    def op_13(current_solution):
        J = data['J']
        I = data['I']
        R = data['R']
        B_i = data['B_i']
    
        job_material = data['job_material']
        el_ir = data['el_ir']
        s_j_prime = data['s_j_prime']
        IL_r = data['IL_r']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
        insertion_fraction = 0.25
    
        unassigned_jobs = []
        used_material = {raw_material: 0 for raw_material in R}
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                unassigned_jobs.append(job)
            elif batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
            else:
                material = job_material[job]
                used_material[material] += s_j_prime[job]
    
        if not unassigned_jobs:
            return current_solution
    
        if len(unassigned_jobs) == 1:
            target_insertions = 1
        else:
            target_insertions = min(
                len(unassigned_jobs),
                max(
                    1,
                    math.ceil(
                        insertion_fraction * len(unassigned_jobs)
                    ),
                ),
            )
    
        np.random.shuffle(unassigned_jobs)
    
        neighbor_13 = copy.deepcopy(current_solution)
        inserted_jobs = 0
    
        def batch_can_accept(job, machine, batch):
            material = job_material[job]
    
            jobs_in_batch = [
                other_job
                for other_job in J
                if neighbor_13[other_job][0] == batch
                and neighbor_13[other_job][1] == machine
            ]
    
            if jobs_in_batch:
                if any(
                    job_material[other_job] != material
                    for other_job in jobs_in_batch
                ):
                    return False
    
            proposed_volume = (
                sum(v_j_part[other_job] for other_job in jobs_in_batch)
                + v_j_part[job]
            )
    
            utilization = (
                proposed_volume
                / (packing_density * v_i_ma[machine])
            )
    
            if utilization > 1 + tolerance:
                return False
    
            tallest_part = max(
                [H_j_part[job]]
                + [
                    H_j_part[other_job]
                    for other_job in jobs_in_batch
                ]
            )
    
            volume_based_height = (
                proposed_volume
                / (
                    packing_density
                    * L_i[machine]
                    * W_i[machine]
                )
            )
    
            required_height = max(
                tallest_part,
                volume_based_height,
            )
    
            return required_height <= H_i[machine] + tolerance
    
        for job_to_insert in unassigned_jobs:
            if inserted_jobs >= target_insertions:
                break
    
            material = job_material[job_to_insert]
    
            if (
                used_material[material] + s_j_prime[job_to_insert]
                > IL_r[material] + tolerance
            ):
                continue
    
            feasible_positions = []
    
            eligible_machines = [
                machine
                for machine in I
                if el_ir[machine][material] == 1
            ]
    
            for machine in eligible_machines:
                active_batches = sorted({
                    neighbor_13[job][0]
                    for job in J
                    if neighbor_13[job][1] == machine
                    and neighbor_13[job][0] is not None
                })
    
                for batch in active_batches:
                    if batch_can_accept(
                        job_to_insert,
                        machine,
                        batch,
                    ):
                        feasible_positions.append((batch, machine))
    
                new_batch = (
                    max(active_batches) + 1
                    if active_batches
                    else 1
                )
    
                if (
                    new_batch in B_i[machine]
                    and batch_can_accept(
                        job_to_insert,
                        machine,
                        new_batch,
                    )
                ):
                    feasible_positions.append(
                        (new_batch, machine)
                    )
    
            if not feasible_positions:
                continue
    
            position_index = np.random.randint(
                len(feasible_positions)
            )
            new_batch, new_machine = feasible_positions[position_index]
    
            neighbor_13[job_to_insert] = [
                new_batch,
                new_machine,
            ]
    
            used_material[material] += s_j_prime[job_to_insert]
            inserted_jobs += 1
    
        if inserted_jobs == 0:
            return current_solution
    
        return neighbor_13
    
    
    
    
    
    
    
    
    # Operator 4: Swap two complete batches from different machines
    def op_4(current_solution):
        J = data['J']
        job_material = data['job_material']
        el_ir = data['el_ir']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
    
        # Collect jobs in each active batch.
        batch_jobs = {}
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                continue
    
            if batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
    
            batch_jobs.setdefault((machine, batch), []).append(job)
    
        if len(batch_jobs) < 2:
            return current_solution
    
        active_batches = []
    
        for (machine, batch), jobs in batch_jobs.items():
            materials = {
                job_material[job]
                for job in jobs
            }
    
            if len(materials) != 1:
                raise ValueError(
                    f"Batch {batch} on machine {machine} "
                    f"contains different materials."
                )
    
            active_batches.append({
                'machine': machine,
                'batch': batch,
                'material': next(iter(materials)),
                'jobs': jobs,
            })
    
        candidate_swaps = []
    
        for index, first_batch in enumerate(active_batches):
            for second_batch in active_batches[index + 1:]:
                machine1 = first_batch['machine']
                machine2 = second_batch['machine']
    
                if machine1 == machine2:
                    continue
    
                material1 = first_batch['material']
                material2 = second_batch['material']
    
                if el_ir[machine1][material2] != 1:
                    continue
    
                if el_ir[machine2][material1] != 1:
                    continue
    
                candidate_swaps.append(
                    (first_batch, second_batch)
                )
    
        if not candidate_swaps:
            return current_solution
    
        np.random.shuffle(candidate_swaps)
    
        def batch_fits_machine(jobs, machine):
            proposed_volume = sum(
                v_j_part[job]
                for job in jobs
            )
    
            utilization = (
                proposed_volume
                / (packing_density * v_i_ma[machine])
            )
    
            if utilization > 1 + tolerance:
                return False
    
            volume_based_height = (
                proposed_volume
                / (
                    packing_density
                    * L_i[machine]
                    * W_i[machine]
                )
            )
    
            tallest_part = max(
                H_j_part[job]
                for job in jobs
            )
    
            required_height = max(
                volume_based_height,
                tallest_part,
            )
    
            return required_height <= H_i[machine] + tolerance
    
        for first_batch, second_batch in candidate_swaps:
            machine1 = first_batch['machine']
            batch1 = first_batch['batch']
            jobs1 = first_batch['jobs']
    
            machine2 = second_batch['machine']
            batch2 = second_batch['batch']
            jobs2 = second_batch['jobs']
    
            # Batch 2 moves to machine 1 and vice versa.
            if not batch_fits_machine(jobs2, machine1):
                continue
    
            if not batch_fits_machine(jobs1, machine2):
                continue
    
            neighbor_4 = copy.deepcopy(current_solution)
    
            for job in jobs1:
                neighbor_4[job] = [batch2, machine2]
    
            for job in jobs2:
                neighbor_4[job] = [batch1, machine1]
    
            return neighbor_4
    
        return current_solution
    
    
    
    
    
    
    # Operator 7: Swap the order of two batches on the same machine
    def op_7(current_solution):
        J = data['J']
    
        active_batches_by_machine = {}
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                continue
    
            if batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
    
            active_batches_by_machine.setdefault(
                machine,
                set(),
            ).add(batch)
    
        eligible_machines = [
            machine
            for machine, active_batches
            in active_batches_by_machine.items()
            if len(active_batches) >= 2
        ]
    
        if not eligible_machines:
            return current_solution
    
        selected_machine = np.random.choice(
            eligible_machines
        )
    
        active_batches = list(
            active_batches_by_machine[selected_machine]
        )
    
        batch1, batch2 = np.random.choice(
            active_batches,
            size=2,
            replace=False,
        )
    
        neighbor_7 = copy.deepcopy(current_solution)
    
        for job in J:
            batch, machine = neighbor_7[job]
    
            if machine != selected_machine:
                continue
    
            if batch == batch1:
                neighbor_7[job][0] = batch2
            elif batch == batch2:
                neighbor_7[job][0] = batch1
    
        return neighbor_7
    
    
    
    
    
    
    # Operator 6: Replace one accepted job with a rejected
    # job of the same material
    def op_6(current_solution):
        J = data['J']
        R = data['R']
    
        job_material = data['job_material']
        el_ir = data['el_ir']
        s_j_prime = data['s_j_prime']
        IL_r = data['IL_r']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
    
        assigned_jobs = []
        unassigned_jobs = []
        used_material = {
            raw_material: 0
            for raw_material in R
        }
        jobs_by_batch = {}
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                unassigned_jobs.append(job)
                continue
    
            if batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
    
            assigned_jobs.append(job)
    
            material = job_material[job]
            used_material[material] += s_j_prime[job]
    
            jobs_by_batch.setdefault(
                (machine, batch),
                [],
            ).append(job)
    
        if not assigned_jobs or not unassigned_jobs:
            return current_solution
    
        candidate_pairs = [
            (assigned_job, unassigned_job)
            for assigned_job in assigned_jobs
            for unassigned_job in unassigned_jobs
            if (
                job_material[assigned_job]
                == job_material[unassigned_job]
            )
        ]
    
        if not candidate_pairs:
            return current_solution
    
        np.random.shuffle(candidate_pairs)
    
        for assigned_job, unassigned_job in candidate_pairs:
            material = job_material[assigned_job]
            batch, machine = current_solution[assigned_job]
    
            new_used_material = (
                used_material[material]
                - s_j_prime[assigned_job]
                + s_j_prime[unassigned_job]
            )
    
            if new_used_material > IL_r[material] + tolerance:
                continue
    
            if el_ir[machine][material] != 1:
                continue
    
            jobs_after_replacement = [
                (
                    unassigned_job
                    if job == assigned_job
                    else job
                )
                for job in jobs_by_batch[(machine, batch)]
            ]
    
            new_volume = sum(
                v_j_part[job]
                for job in jobs_after_replacement
            )
    
            utilization = (
                new_volume
                / (packing_density * v_i_ma[machine])
            )
    
            if utilization > 1 + tolerance:
                continue
    
            volume_based_height = (
                new_volume
                / (
                    packing_density
                    * L_i[machine]
                    * W_i[machine]
                )
            )
    
            tallest_part = max(
                H_j_part[job]
                for job in jobs_after_replacement
            )
    
            required_height = max(
                volume_based_height,
                tallest_part,
            )
    
            if required_height > H_i[machine] + tolerance:
                continue
    
            neighbor_6 = copy.deepcopy(current_solution)
    
            neighbor_6[unassigned_job] = [
                batch,
                machine,
            ]
            neighbor_6[assigned_job] = [
                None,
                None,
            ]
    
            return neighbor_6
    
        return current_solution
    
    
    
    
    
    
    
    # Operator 8: Exchange approximately 20% of rejected jobs
    # with accepted jobs having the same material
    def op_8(current_solution):
        J = data['J']
        R = data['R']
    
        job_material = data['job_material']
        el_ir = data['el_ir']
        s_j_prime = data['s_j_prime']
        IL_r = data['IL_r']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
        replacement_fraction = 0.20
    
        assigned_jobs = []
        unassigned_jobs = []
        used_material = {
            raw_material: 0
            for raw_material in R
        }
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                unassigned_jobs.append(job)
                continue
    
            if batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
    
            assigned_jobs.append(job)
            material = job_material[job]
            used_material[material] += s_j_prime[job]
    
        if not assigned_jobs or not unassigned_jobs:
            return current_solution
    
        maximum_replacements = min(
            len(assigned_jobs),
            len(unassigned_jobs),
        )
    
        if maximum_replacements == 1:
            target_replacements = 1
        else:
            target_replacements = min(
                maximum_replacements,
                max(
                    1,
                    math.ceil(
                        replacement_fraction
                        * len(unassigned_jobs)
                    ),
                ),
            )
    
        np.random.shuffle(unassigned_jobs)
    
        neighbor_8 = copy.deepcopy(current_solution)
        available_assigned_jobs = set(assigned_jobs)
        replacements_made = 0
    
        for unassigned_job in unassigned_jobs:
            if replacements_made >= target_replacements:
                break
    
            material = job_material[unassigned_job]
    
            candidate_assigned_jobs = [
                assigned_job
                for assigned_job in available_assigned_jobs
                if job_material[assigned_job] == material
            ]
    
            if not candidate_assigned_jobs:
                continue
    
            np.random.shuffle(candidate_assigned_jobs)
    
            for assigned_job in candidate_assigned_jobs:
                batch, machine = neighbor_8[assigned_job]
    
                new_used_material = (
                    used_material[material]
                    - s_j_prime[assigned_job]
                    + s_j_prime[unassigned_job]
                )
    
                if new_used_material > IL_r[material] + tolerance:
                    continue
    
                if el_ir[machine][material] != 1:
                    continue
    
                jobs_after_replacement = [
                    (
                        unassigned_job
                        if job == assigned_job
                        else job
                    )
                    for job in J
                    if (
                        neighbor_8[job][0] == batch
                        and neighbor_8[job][1] == machine
                    )
                ]
    
                new_volume = sum(
                    v_j_part[job]
                    for job in jobs_after_replacement
                )
    
                utilization = (
                    new_volume
                    / (packing_density * v_i_ma[machine])
                )
    
                if utilization > 1 + tolerance:
                    continue
    
                volume_based_height = (
                    new_volume
                    / (
                        packing_density
                        * L_i[machine]
                        * W_i[machine]
                    )
                )
    
                tallest_part = max(
                    H_j_part[job]
                    for job in jobs_after_replacement
                )
    
                required_height = max(
                    volume_based_height,
                    tallest_part,
                )
    
                if required_height > H_i[machine] + tolerance:
                    continue
    
                neighbor_8[unassigned_job] = [
                    batch,
                    machine,
                ]
                neighbor_8[assigned_job] = [
                    None,
                    None,
                ]
    
                used_material[material] = new_used_material
                available_assigned_jobs.remove(assigned_job)
                replacements_made += 1
                break
    
        if replacements_made == 0:
            return current_solution
    
        return neighbor_8
    
    
    
    
    
    
    # Operator 14: Relocate one accepted job
    # Operator 14: Remove one assigned job and reassign it on eligible machines
    
    def op_14(current_solution):
        J = data['J']
        I = data['I']
        B_i = data['B_i']
    
        job_material = data['job_material']
        el_ir = data['el_ir']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
        existing_batch_probability = 0.80
    
        assigned_jobs = []
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                continue
    
            if batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
    
            assigned_jobs.append(job)
    
        if not assigned_jobs:
            return current_solution
    
        np.random.shuffle(assigned_jobs)
    
        def batch_fits_machine(jobs, machine):
            proposed_volume = sum(
                v_j_part[job]
                for job in jobs
            )
    
            utilization = (
                proposed_volume
                / (packing_density * v_i_ma[machine])
            )
    
            if utilization > 1 + tolerance:
                return False
    
            volume_based_height = (
                proposed_volume
                / (
                    packing_density
                    * L_i[machine]
                    * W_i[machine]
                )
            )
    
            tallest_part = max(
                H_j_part[job]
                for job in jobs
            )
    
            required_height = max(
                volume_based_height,
                tallest_part,
            )
    
            return required_height <= H_i[machine] + tolerance
    
        for job_to_move in assigned_jobs:
            material = job_material[job_to_move]
            _, original_machine = current_solution[job_to_move]
    
            removed_solution = copy.deepcopy(current_solution)
            removed_solution[job_to_move] = [None, None]
    
            # Repair a possible gap created by removing a singleton batch.
            repaired_solution, _ = rep_3(
                removed_solution,
                machines=[original_machine],
            )
    
            feasible_existing_positions = []
            feasible_new_positions = []
    
            eligible_machines = [
                machine
                for machine in I
                if el_ir[machine][material] == 1
            ]
    
            for machine in eligible_machines:
                active_batches = sorted({
                    repaired_solution[job][0]
                    for job in J
                    if (
                        repaired_solution[job][1] == machine
                        and repaired_solution[job][0] is not None
                    )
                })
    
                # Existing same-material batches.
                for batch in active_batches:
                    jobs_in_batch = [
                        job
                        for job in J
                        if (
                            repaired_solution[job][0] == batch
                            and repaired_solution[job][1] == machine
                        )
                    ]
    
                    if not jobs_in_batch:
                        continue
    
                    if any(
                        job_material[job] != material
                        for job in jobs_in_batch
                    ):
                        continue
    
                    proposed_jobs = (
                        jobs_in_batch + [job_to_move]
                    )
    
                    if batch_fits_machine(
                        proposed_jobs,
                        machine,
                    ):
                        feasible_existing_positions.append(
                            (batch, machine)
                        )
    
                # Next sequential batch.
                new_batch = (
                    max(active_batches) + 1
                    if active_batches
                    else 1
                )
    
                if new_batch not in B_i[machine]:
                    continue
    
                if batch_fits_machine(
                    [job_to_move],
                    machine,
                ):
                    feasible_new_positions.append(
                        (new_batch, machine)
                    )
    
            # Give existing batches an 80% priority while retaining
            # the ability to open a new batch.
            if (
                feasible_existing_positions
                and feasible_new_positions
            ):
                if (
                    np.random.random()
                    < existing_batch_probability
                ):
                    position_groups = [
                        feasible_existing_positions,
                        feasible_new_positions,
                    ]
                else:
                    position_groups = [
                        feasible_new_positions,
                        feasible_existing_positions,
                    ]
            elif feasible_existing_positions:
                position_groups = [
                    feasible_existing_positions
                ]
            elif feasible_new_positions:
                position_groups = [
                    feasible_new_positions
                ]
            else:
                continue
    
            for feasible_positions in position_groups:
                np.random.shuffle(feasible_positions)
    
                for new_batch, new_machine in feasible_positions:
                    candidate = copy.deepcopy(
                        repaired_solution
                    )
                    candidate[job_to_move] = [
                        new_batch,
                        new_machine,
                    ]
    
                    # Do not return an unchanged reassignment.
                    if candidate == current_solution:
                        continue
    
                    return candidate
    
        return current_solution
    
    
    
    
    
    
    
    
    
    # Operator 9: Split one batch into two nonempty batches and redistribute them
    def op_9(current_solution):
        J = data['J']
        I = data['I']
        B_i = data['B_i']
    
        job_material = data['job_material']
        el_ir = data['el_ir']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
    
        batch_jobs = {}
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                continue
    
            if batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
    
            batch_jobs.setdefault(
                (machine, batch),
                [],
            ).append(job)
    
        splittable_batches = []
    
        for (machine, batch), jobs in batch_jobs.items():
            if len(jobs) < 2:
                continue
    
            materials = {
                job_material[job]
                for job in jobs
            }
    
            if len(materials) != 1:
                raise ValueError(
                    f"Batch {batch} on machine {machine} "
                    f"contains different materials."
                )
    
            splittable_batches.append({
                'machine': machine,
                'batch': batch,
                'material': next(iter(materials)),
                'jobs': jobs,
            })
    
        if not splittable_batches:
            return current_solution
    
        np.random.shuffle(splittable_batches)
    
        def batch_fits_machine(jobs, machine):
            proposed_volume = sum(
                v_j_part[job]
                for job in jobs
            )
    
            utilization = (
                proposed_volume
                / (packing_density * v_i_ma[machine])
            )
    
            if utilization > 1 + tolerance:
                return False
    
            volume_based_height = (
                proposed_volume
                / (
                    packing_density
                    * L_i[machine]
                    * W_i[machine]
                )
            )
    
            tallest_part = max(
                H_j_part[job]
                for job in jobs
            )
    
            required_height = max(
                volume_based_height,
                tallest_part,
            )
    
            return required_height <= H_i[machine] + tolerance
    
        for selected_batch in splittable_batches:
            selected_machine = selected_batch['machine']
            original_batch = selected_batch['batch']
            material = selected_batch['material']
    
            shuffled_jobs = selected_batch['jobs'].copy()
            np.random.shuffle(shuffled_jobs)
    
            split_points = list(
                range(1, len(shuffled_jobs))
            )
            np.random.shuffle(split_points)
    
            for split_point in split_points:
                group_keep = shuffled_jobs[:split_point]
                group_move = shuffled_jobs[split_point:]
    
                feasible_destinations = []
    
                eligible_machines = [
                    machine
                    for machine in I
                    if el_ir[machine][material] == 1
                ]
    
                for destination_machine in eligible_machines:
                    active_batches = sorted({
                        current_solution[job][0]
                        for job in J
                        if (
                            current_solution[job][1]
                            == destination_machine
                            and current_solution[job][0]
                            is not None
                        )
                    })
    
                    new_batch = (
                        max(active_batches) + 1
                        if active_batches
                        else 1
                    )
    
                    if new_batch not in B_i[destination_machine]:
                        continue
    
                    if batch_fits_machine(
                        group_move,
                        destination_machine,
                    ):
                        feasible_destinations.append(
                            (new_batch, destination_machine)
                        )
    
                if not feasible_destinations:
                    continue
    
                np.random.shuffle(feasible_destinations)
                new_batch, new_machine = (
                    feasible_destinations[0]
                )
    
                neighbor_9 = copy.deepcopy(current_solution)
    
                for job in group_keep:
                    neighbor_9[job] = [
                        original_batch,
                        selected_machine,
                    ]
    
                for job in group_move:
                    neighbor_9[job] = [
                        new_batch,
                        new_machine,
                    ]
    
                return neighbor_9
    
        return current_solution
    
    
    
    
    
    # Operator 10: Partially or completely merge two
    # same-material batches
    def op_10(current_solution):
        J = data['J']
    
        job_material = data['job_material']
    
        v_j_part = data['v_j_part']
        H_j_part = data['H_j_part']
        L_i = data['L_i']
        W_i = data['W_i']
        H_i = data['H_i']
        v_i_ma = data['v_i_ma']
        packing_density = data['packing_density']
    
        tolerance = 1e-6
    
        batch_jobs = {}
    
        for job in J:
            batch, machine = current_solution[job]
    
            if batch is None and machine is None:
                continue
    
            if batch is None or machine is None:
                raise ValueError(
                    f"Job {job} has an incomplete assignment."
                )
    
            batch_jobs.setdefault(
                (machine, batch),
                [],
            ).append(job)
    
        if len(batch_jobs) < 2:
            return current_solution
    
        active_batches = []
    
        for (machine, batch), jobs in batch_jobs.items():
            materials = {
                job_material[job]
                for job in jobs
            }
    
            if len(materials) != 1:
                raise ValueError(
                    f"Batch {batch} on machine {machine} "
                    f"contains different materials."
                )
    
            active_batches.append({
                'machine': machine,
                'batch': batch,
                'material': next(iter(materials)),
                'jobs': jobs,
            })
    
        # Each same-material pair is considered in both directions.
        merge_directions = []
    
        for index, first_batch in enumerate(active_batches):
            for second_batch in active_batches[index + 1:]:
                if (
                    first_batch['material']
                    != second_batch['material']
                ):
                    continue
    
                merge_directions.append(
                    (first_batch, second_batch)
                )
                merge_directions.append(
                    (second_batch, first_batch)
                )
    
        if not merge_directions:
            return current_solution
    
        np.random.shuffle(merge_directions)
    
        def batch_fits_machine(jobs, machine):
            proposed_volume = sum(
                v_j_part[job]
                for job in jobs
            )
    
            utilization = (
                proposed_volume
                / (packing_density * v_i_ma[machine])
            )
    
            if utilization > 1 + tolerance:
                return False
    
            volume_based_height = (
                proposed_volume
                / (
                    packing_density
                    * L_i[machine]
                    * W_i[machine]
                )
            )
    
            tallest_part = max(
                H_j_part[job]
                for job in jobs
            )
    
            required_height = max(
                volume_based_height,
                tallest_part,
            )
    
            return required_height <= H_i[machine] + tolerance
    
        for destination_batch, source_batch in merge_directions:
            destination_machine = destination_batch['machine']
            destination_batch_id = destination_batch['batch']
    
            source_machine = source_batch['machine']
            source_jobs = source_batch['jobs'].copy()
    
            destination_jobs = destination_batch['jobs'].copy()
            moved_jobs = []
    
            # Random order gives different partial merges across iterations.
            np.random.shuffle(source_jobs)
    
            for job in source_jobs:
                proposed_destination_jobs = (
                    destination_jobs + [job]
                )
    
                if not batch_fits_machine(
                    proposed_destination_jobs,
                    destination_machine,
                ):
                    continue
    
                destination_jobs.append(job)
                moved_jobs.append(job)
    
            if not moved_jobs:
                continue
    
            neighbor_10 = copy.deepcopy(current_solution)
    
            for job in moved_jobs:
                neighbor_10[job] = [
                    destination_batch_id,
                    destination_machine,
                ]
    
            # Repair batch numbering only if the source batch became empty.
            if len(moved_jobs) == len(source_batch['jobs']):
                neighbor_10, _ = rep_3(
                    neighbor_10,
                    machines=[source_machine],
                )
    
            return neighbor_10
    
        return current_solution
    
    
    
   
    
    # Operator mapping
    operator_functions = {
        1: op_1,
        2: op_2,
        3: op_3,
        4: op_4,
        5: op_6,
        6: op_7,
        7: op_8,
        8: op_9,
        9: op_10,
        10: op_11,
        11: op_12,
        12: op_13,
        13: op_14,
    }
    
    operator_ids = list(operator_functions)
  
    n_opt = min(10, len(operator_ids))
    max_rounds = 2
    
    #max_rounds = 20
    tolerance = 1e-6
    
   
    
    def volume_capacity_is_feasible(solution):
        """
        Check the usable-volume constraint for every active batch.

        This corresponds to:
            total part volume <= packing_density * machine volume
        """

        batch_volumes = {}

        for job in data['J']:
            if job not in solution:
                return False

            batch, machine = solution[job]

            if batch is None and machine is None:
                continue

            if batch is None or machine is None:
                return False

            if machine not in data['I']:
                return False

            if batch not in data['B_i'][machine]:
                return False

            key = (machine, batch)

            batch_volumes[key] = (
                batch_volumes.get(key, 0.0)
                + data['v_j_part'][job]
            )

        for (machine, _), batch_volume in batch_volumes.items():
            usable_capacity = (
                data['packing_density']
                * data['v_i_ma'][machine]
            )

            if batch_volume > usable_capacity + tolerance:
                return False

        return True

    
    
    def candidate_is_feasible(solution):
        """
        Run all BVC feasibility checks on a changed candidate.
        """

        if not feasibility_7(data, solution):
            return False

        if not feasibility_5(
            data,
            solution,
            machines=None,
            jobs=None,
        ):
            return False

        if not feasibility_4(
            data,
            solution,
            machines=None,
            batches=None,
        ):
            return False

        if not feasibility_6(
            data,
            solution,
            machines=None,
        ):
            return False

        if not volume_capacity_is_feasible(solution):
            return False

        if not feasibility_26(
            data,
            solution,
            machines=None,
            batches=None,
        ):
            return False

        return True

    # At each round, select n_opt distinct operators according
    # to their adaptive probabilities. Evaluate every selected
    # operator and return the best feasible candidate.
    for _ in range(max_rounds):
        selected_operators = np.random.choice(
            operator_ids,
            size=n_opt,
            replace=False,
        )

        candidates = []

        for selected_operator in selected_operators:
            operator_id = int(selected_operator)
            operator_function = operator_functions[operator_id]

            neighbor_solution = operator_function(
                current_solution
            )

            # An unchanged solution is not a neighbor.
            if neighbor_solution == current_solution:
                continue

            if not candidate_is_feasible(
                neighbor_solution
            ):
                continue

            objective_values = calculate_objective(
                neighbor_solution,
                data,
            )

            if len(objective_values) != 15:
                raise ValueError(
                    "calculate_objective must return "
                    "exactly 15 values."
                )

            if not math.isfinite(objective_values[0]):
                raise ValueError(
                    "The candidate objective must be finite."
                )

            candidates.append(
                (
                    neighbor_solution,
                    objective_values,
                    operator_id,
                )
            )

        if not candidates:
            continue

        # Select the best candidate generated by the selected
        # operators. It may still be worse than the current
        # solution; the main SA loop applies the Metropolis test.
        (
            best_neighbor,
            best_values,
            best_operator,
        ) = min(
            candidates,
            key=lambda candidate: candidate[1][0],
        )

        (
            best_objective,
            best_production_cost,
            best_lateness_cost,
            best_rejection_cost,
            best_unused_capacity_cost,
            best_job_completion_time,
            best_batch_completion_time,
            best_batch_processing_time,
            best_batch_weight,
            best_batch_volume,
            best_batch_height,
            best_batch_unused_capacity,
            best_job_tardiness,
            best_total_rejected_jobs,
            best_acceptance_rate,
        ) = best_values

        return (
            best_neighbor,
            best_objective,
            best_production_cost,
            best_lateness_cost,
            best_rejection_cost,
            best_unused_capacity_cost,
            best_job_completion_time,
            best_batch_completion_time,
            best_batch_processing_time,
            best_batch_weight,
            best_batch_volume,
            best_batch_height,
            best_batch_unused_capacity,
            best_job_tardiness,
            best_operator,
            best_total_rejected_jobs,
            best_acceptance_rate,
        )

    # No selected operator generated a changed feasible solution.
    return None
        
        
        
        
        
        
        
                
    
        
    
    
    
    
    
    
    