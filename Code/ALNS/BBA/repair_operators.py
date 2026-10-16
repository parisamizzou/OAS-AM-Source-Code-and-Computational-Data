#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 09:54:26 2026

@author: parisa
"""

import copy
import math

from helpers import (get_rejected_jobs, build_batch_loads, feasible_batch_after_insertion,
                     build_remaining_material, get_same_material_batches)

from feasibility import (
    feasibility_1, feasibility_2, feasibility_4,
    feasibility_5, feasibility_6, feasibility_7,
)

from calculate_objective import calculate_objective




def repair_operators():
    
    
    
    # -------------------------------------
    # Repair 3: Reindex batch IDs on each machine
    # -------------------------------------
    def rep_3(solution, data):
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
    
        new_solution = copy.deepcopy(solution)
        fixed_machines = []
    
        for machine in I:
    
            # Find active batch labels on this machine
            active_batches = sorted(set(
                new_solution[job][0]
                for job in J
                if new_solution[job][1] == machine and new_solution[job][0] is not None
            ))
    
            if not active_batches:
                continue
    
            #print('active_batches', active_batches)
    
            k = len(active_batches)
            expected_batches = list(range(1, k + 1))
            #print('k', k)
            #print('expected_batches', expected_batches)
    
            # If already consecutive, do nothing
            if active_batches == expected_batches:
                continue
    
            # Build relabel map: old batch -> new batch
            batch_map = {
                old_batch: new_batch
                for new_batch, old_batch in enumerate(active_batches, start=1)
            }
    
            #print('batch_map', batch_map)
    
            # Apply relabeling
            for job in J:
                if new_solution[job][1] == machine and new_solution[job][0] is not None:
                    old_batch = new_solution[job][0]
                    new_solution[job][0] = batch_map[old_batch]
    
            fixed_machines.append({
                "machine": machine,
                "old_labels": active_batches,
                "new_labels": expected_batches,
                "batch_map": batch_map
            })
    
        info = {
            "fixed_machines": fixed_machines,
            "num_fixed_machines": len(fixed_machines)
        }
    
        return new_solution, info
    
    
    
    
    
    
    # Repair 1: Random feasible insertion of a fraction p of rejected jobs.
    def rep_1(solution, data, p, rng):
        if not (0 <= p <= 1):
            raise ValueError("p must be between 0 and 1 in rep_1.")

        J = data['J']
        I = data['I']
        B_i = data['B_i']
        job_material = data['job_material']
        s_j_prime = data['s_j_prime']
        el_ir = data['el_ir']

        new_solution = copy.deepcopy(solution)
        inserted_jobs = []
        still_rejected = []

        rejected_jobs = get_rejected_jobs(new_solution, data)
        rng.shuffle(rejected_jobs)
        n_select = min(math.ceil(p * len(rejected_jobs)), len(rejected_jobs))
        selected_jobs = rejected_jobs[:n_select]

        batch_volume, batch_weight, batch_material, batch_height = (
            build_batch_loads(new_solution, data)
        )
        remaining_material = build_remaining_material(new_solution, data)

        for job in selected_jobs:
            raw_material = job_material[job]

            if remaining_material[raw_material] + 1e-6 < s_j_prime[job]:
                still_rejected.append(job)
                continue

            eligible_machines = [
                machine for machine in I
                if el_ir[machine][raw_material] == 1
            ]
            rng.shuffle(eligible_machines)
            assigned = False

            for machine in eligible_machines:
                candidate_batches = get_same_material_batches(
                    new_solution, data, machine, raw_material
                )
                active_batches = sorted(set(
                    new_solution[j][0] for j in J
                    if new_solution[j][1] == machine
                    and new_solution[j][0] is not None
                ))
                
                next_batch = max(active_batches) + 1 if active_batches else 1

                if next_batch in B_i[machine]:
                    candidate_batches.append(next_batch)

                candidate_batches = list(dict.fromkeys(candidate_batches))
                rng.shuffle(candidate_batches)
                
                for batch in candidate_batches:
                    current_volume = batch_volume[machine][batch - 1]
                    current_height = batch_height[machine][batch - 1]

                    if not feasible_batch_after_insertion(
                        data, job, machine, current_volume, current_height
                    ):
                        continue

                    candidate_solution = copy.deepcopy(new_solution)
                    candidate_solution[job] = [batch, machine]
                    
                    # Validate the complete candidate using the shared BBA rules.
                    if not (
                        feasibility_5(data, candidate_solution)
                        and feasibility_7(data, candidate_solution)
                        and feasibility_4(data, candidate_solution)
                        and feasibility_6(data, candidate_solution)
                        and feasibility_1(data, candidate_solution)
                        and feasibility_2(data, candidate_solution)
                    ):
                        continue

                    new_solution = candidate_solution
                    inserted_jobs.append(job)
                    batch_volume[machine][batch - 1] += data['v_j_BB'][job]
                    batch_weight[machine][batch - 1] += s_j_prime[job]
                    batch_material[machine][batch - 1] = raw_material
                    batch_height[machine][batch - 1] = max(
                        current_height,
                        data['H_j_part'][job],
                        batch_volume[machine][batch - 1] / (
                            data['packing_density']
                            * data['L_i'][machine]
                            * data['W_i'][machine]
                        ),
                    )
                    remaining_material[raw_material] -= s_j_prime[job]
                    assigned = True
                    break

                if assigned:
                    break

            if not assigned:
                still_rejected.append(job)

        new_solution, rep_3_info = rep_3(new_solution, data)
        return new_solution, {
            "selected_jobs": selected_jobs,
            "inserted_jobs": inserted_jobs,
            "still_rejected": still_rejected,
            "rep_3_info": rep_3_info,
        }
                
                
                
                
    
    
    # ------------------------------------------------------------
    # Repair 2: Greedy feasible insertion
    # Consider a fraction p of rejected jobs and insert each
    # at its lowest-cost feasible position only if cost improves.
    # ------------------------------------------------------------
    def rep_2(solution, data, p, rng, eps=1e-12):
        """
        Process selected rejected jobs in random order.
    
        For each job, evaluate existing same-material batches and
        the next new batch on every eligible machine.
    
        p is a fraction between 0 and 1.
        Solution format: solution[job] = [batch, machine].
        """
        
        if not (0 <= p <= 1):
            raise ValueError("p must be between 0 and 1 in rep_2.")
    
        if not math.isfinite(eps) or eps < 0:
            raise ValueError("eps must be finite and nonnegative in rep_2.")
    
        J = data['J']
        I = data['I']
        B_i = data['B_i']
        job_material = data['job_material']
        el_ir = data['el_ir']
        s_j_prime = data['s_j_prime']
    
        new_solution = copy.deepcopy(solution)
        inserted_jobs = []
        still_rejected = []
    
        rejected_jobs = get_rejected_jobs(new_solution, data)
        rng.shuffle(rejected_jobs)
    
        n_select = min(math.ceil(p * len(rejected_jobs)), len(rejected_jobs))
        selected_jobs = rejected_jobs[:n_select]
        
        for job in selected_jobs:
            raw_material = job_material[job]
            remaining_material = build_remaining_material(new_solution, data)
    
            if remaining_material[raw_material] + 1e-6 < s_j_prime[job]:
                still_rejected.append(job)
                continue
    
            current_cost = float(calculate_objective(new_solution, data)[0])
            best_job_cost = float("inf")
            best_job_move = None
    
            batch_volume, batch_weight, batch_material, batch_height = (
                build_batch_loads(new_solution, data)
            )
    
            eligible_machines = [
                machine for machine in I
                if el_ir[machine][raw_material] == 1
            ]
            rng.shuffle(eligible_machines)
            
            for machine in eligible_machines:
                candidate_batches = get_same_material_batches(
                    new_solution, data, machine, raw_material
                )
    
                active_batches = sorted(set(
                    new_solution[j][0]
                    for j in J
                    if new_solution[j][1] == machine
                    and new_solution[j][0] is not None
                ))
                next_batch = max(active_batches) + 1 if active_batches else 1
    
                if next_batch in B_i[machine]:
                    candidate_batches.append(next_batch)
    
                candidate_batches = list(dict.fromkeys(candidate_batches))
                rng.shuffle(candidate_batches)
                
                for batch in candidate_batches:
                    current_volume = batch_volume[machine][batch - 1]
                    current_height = batch_height[machine][batch - 1]
    
                    if not feasible_batch_after_insertion(
                        data, job, machine, current_volume, current_height
                    ):
                        continue
    
                    candidate_solution = copy.deepcopy(new_solution)
                    candidate_solution[job] = [batch, machine]
                    
                    if not (
                        feasibility_5(data, candidate_solution)
                        and feasibility_7(data, candidate_solution)
                        and feasibility_4(data, candidate_solution)
                        and feasibility_6(data, candidate_solution)
                        and feasibility_1(data, candidate_solution)
                        and feasibility_2(data, candidate_solution)
                    ):
                        continue
    
                    candidate_cost = float(
                        calculate_objective(candidate_solution, data)[0]
                    )
    
                    if candidate_cost < best_job_cost:
                        best_job_cost = candidate_cost
                        best_job_move = candidate_solution
    
            if (
                best_job_move is not None
                and best_job_cost < current_cost - eps
            ):
                new_solution = best_job_move
                new_solution, _ = rep_3(new_solution, data)
                inserted_jobs.append(job)
            else:
                still_rejected.append(job)
    
        new_solution, rep_3_info = rep_3(new_solution, data)
    
        info = {
            "selected_jobs": selected_jobs,
            "inserted_jobs": inserted_jobs,
            "still_rejected": still_rejected,
            "rep_3_info": rep_3_info,
        }
    
        return new_solution, info
        
        
        
    
        
    
    
    
    # ------------------------------------------------------------
    # Repair 4: Best feasible insertion, even if cost increases
    # ------------------------------------------------------------
    def rep_4(solution, data, p, rng, eps=1e-12):
        """
        Consider a fraction p of rejected jobs in random order.
        Insert each at its lowest-cost feasible position, even if
        the insertion does not improve the objective.
    
        p must be between 0 and 1.
        Solution format: solution[job] = [batch, machine].
        """
        
        if not (0 <= p <= 1):
            raise ValueError("p must be between 0 and 1 in rep_4.")
    
        J = data['J']
        I = data['I']
        B_i = data['B_i']
        job_material = data['job_material']
        el_ir = data['el_ir']
        s_j_prime = data['s_j_prime']
    
        new_solution = copy.deepcopy(solution)
        inserted_jobs = []
    
        rejected_jobs = get_rejected_jobs(new_solution, data)
        rng.shuffle(rejected_jobs)
    
        n_select = min(math.ceil(p * len(rejected_jobs)), len(rejected_jobs))
        selected_jobs = rejected_jobs[:n_select]
        
        for job in selected_jobs:
            raw_material = job_material[job]
            remaining_material = build_remaining_material(new_solution, data)
    
            if remaining_material[raw_material] + 1e-6 < s_j_prime[job]:
                continue
    
            batch_volume, batch_weight, batch_material, batch_height = (
                build_batch_loads(new_solution, data)
            )
    
            best_job_cost = float("inf")
            best_job_move = None
    
            eligible_machines = [
                machine for machine in I
                if el_ir[machine][raw_material] == 1
            ]
            rng.shuffle(eligible_machines)
            
            for machine in eligible_machines:
                candidate_batches = get_same_material_batches(
                    new_solution, data, machine, raw_material
                )
    
                active_batches = sorted(set(
                    new_solution[j][0]
                    for j in J
                    if new_solution[j][1] == machine
                    and new_solution[j][0] is not None
                ))
                next_batch = max(active_batches) + 1 if active_batches else 1
    
                if next_batch in B_i[machine]:
                    candidate_batches.append(next_batch)
    
                candidate_batches = list(dict.fromkeys(candidate_batches))
                rng.shuffle(candidate_batches)
                
                for batch in candidate_batches:
                    current_volume = batch_volume[machine][batch - 1]
                    current_height = batch_height[machine][batch - 1]
    
                    if not feasible_batch_after_insertion(
                        data, job, machine, current_volume, current_height
                    ):
                        continue
    
                    candidate_solution = copy.deepcopy(new_solution)
                    candidate_solution[job] = [batch, machine]
                    
                    if not (
                        feasibility_5(data, candidate_solution)
                        and feasibility_7(data, candidate_solution)
                        and feasibility_4(data, candidate_solution)
                        and feasibility_6(data, candidate_solution)
                        and feasibility_1(data, candidate_solution)
                        and feasibility_2(data, candidate_solution)
                    ):
                        continue
    
                    candidate_cost = float(
                        calculate_objective(candidate_solution, data)[0]
                    )
    
                    if candidate_cost < best_job_cost:
                        best_job_cost = candidate_cost
                        best_job_move = candidate_solution
    
            if best_job_move is not None:
                new_solution = best_job_move
                new_solution, _ = rep_3(new_solution, data)
                inserted_jobs.append(job)
    
        new_solution, rep_3_info = rep_3(new_solution, data)
        still_rejected = get_rejected_jobs(new_solution, data)
    
        info = {
            "selected_jobs": selected_jobs,
            "inserted_jobs": inserted_jobs,
            "still_rejected": still_rejected,
            "rep_3_info": rep_3_info,
        }
    
        return new_solution, info
        
        
    
    
    
    
    # ------------------------------------------------------------
    # Repair 5: EDD-based best feasible insertion
    # ------------------------------------------------------------
    def rep_5(solution, data, p, rng, eps=1e-12):
        """
        Select a fraction p of rejected jobs by earliest due date.
        Insert each at its lowest-cost feasible position, even if
        the insertion does not improve the objective.
    
        Equal due dates are ordered by job ID.
        Solution format: solution[job] = [batch, machine].
        """
        
        if not (0 <= p <= 1):
           raise ValueError("p must be between 0 and 1 in rep_5.")
           
        J = data['J']
        I = data['I']
        B_i = data['B_i']
        job_material = data['job_material']
        el_ir = data['el_ir']
        d_j = data['d_j']
        s_j_prime = data['s_j_prime']
    
        new_solution = copy.deepcopy(solution)
        inserted_jobs = []
    
        rejected_jobs = sorted(
            get_rejected_jobs(new_solution, data),
            key=lambda job: (float(d_j[job]), job)
        )
    
        n_select = min(math.ceil(p * len(rejected_jobs)), len(rejected_jobs))
        selected_jobs = rejected_jobs[:n_select]
        
        for job in selected_jobs:
            raw_material = job_material[job]
            remaining_material = build_remaining_material(new_solution, data)
    
            if remaining_material[raw_material] + 1e-6 < s_j_prime[job]:
                continue
    
            batch_volume, batch_weight, batch_material, batch_height = (
                build_batch_loads(new_solution, data)
            )
    
            best_job_cost = float("inf")
            best_job_move = None
    
            eligible_machines = [
                machine for machine in I
                if el_ir[machine][raw_material] == 1
            ]
            rng.shuffle(eligible_machines)
            
            for machine in eligible_machines:
                candidate_batches = get_same_material_batches(
                    new_solution, data, machine, raw_material
                )
    
                active_batches = sorted(set(
                    new_solution[j][0]
                    for j in J
                    if new_solution[j][1] == machine
                    and new_solution[j][0] is not None
                ))
                next_batch = max(active_batches) + 1 if active_batches else 1
    
                if next_batch in B_i[machine]:
                    candidate_batches.append(next_batch)
    
                candidate_batches = list(dict.fromkeys(candidate_batches))
                
                for batch in candidate_batches:
                    current_volume = batch_volume[machine][batch - 1]
                    current_height = batch_height[machine][batch - 1]
    
                    if not feasible_batch_after_insertion(
                        data, job, machine, current_volume, current_height
                    ):
                        continue
    
                    candidate_solution = copy.deepcopy(new_solution)
                    candidate_solution[job] = [batch, machine]
                    
                    if not (
                        feasibility_5(data, candidate_solution)
                        and feasibility_7(data, candidate_solution)
                        and feasibility_4(data, candidate_solution)
                        and feasibility_6(data, candidate_solution)
                        and feasibility_1(data, candidate_solution)
                        and feasibility_2(data, candidate_solution)
                    ):
                        continue
    
                    candidate_cost = float(
                        calculate_objective(candidate_solution, data)[0]
                    )
    
                    if candidate_cost < best_job_cost:
                        best_job_cost = candidate_cost
                        best_job_move = candidate_solution
    
            if best_job_move is not None:
                new_solution = best_job_move
                new_solution, _ = rep_3(new_solution, data)
                inserted_jobs.append(job)
    
        new_solution, rep_3_info = rep_3(new_solution, data)
        still_rejected = get_rejected_jobs(new_solution, data)
    
        info = {
            "selected_jobs": selected_jobs,
            "inserted_jobs": inserted_jobs,
            "still_rejected": still_rejected,
            "rep_3_info": rep_3_info,
        }
    
        return new_solution, info
   
       
   
    
   
    
    # ------------------------------------------------------------
    # Repair 6: Regret-k insertion
    # ------------------------------------------------------------
    def rep_6(solution, data, p, rng, eps=1e-12, k_regret=2):
        """
        Insert up to ceil(p * initial rejected jobs) jobs.
    
        Recalculate feasible insertion positions after each insertion.
        Select the job with the largest regret, breaking ties by
        lower best insertion cost.
    
        Regret = sum(cost_l - cost_1 for l = 2, ..., k_regret).
        If fewer than k_regret positions exist, repeat the worst
        available cost. A single feasible position gives zero regret.
    
        Insertions may increase total cost.
        Solution format: solution[job] = [batch, machine].
        """
        
        if not (0 <= p <= 1):
            raise ValueError("p must be between 0 and 1 in rep_6.")
    
        if (
            isinstance(k_regret, bool)
            or not isinstance(k_regret, int)
            or k_regret < 2
        ):
            raise ValueError("k_regret must be an integer of at least 2.")
    
        if not math.isfinite(eps) or eps < 0:
            raise ValueError("eps must be finite and nonnegative in rep_6.")
    
        J = data['J']
        I = data['I']
        B_i = data['B_i']
        job_material = data['job_material']
        el_ir = data['el_ir']
        s_j_prime = data['s_j_prime']
    
        new_solution = copy.deepcopy(solution)
        inserted_jobs = []
        
        initial_rejected = get_rejected_jobs(new_solution, data)
        max_insertions = min(
            math.ceil(p * len(initial_rejected)),
            len(initial_rejected)
        )
    
        while len(inserted_jobs) < max_insertions:
            rejected_jobs = get_rejected_jobs(new_solution, data)
    
            if not rejected_jobs:
                break
    
            batch_volume, batch_weight, batch_material, batch_height = (
                build_batch_loads(new_solution, data)
            )
            remaining_material = build_remaining_material(new_solution, data)
    
            best_job_to_insert = None
            best_job_regret = -float("inf")
            best_job_best_cost = float("inf")
            best_job_best_move = None
            
            for job in rejected_jobs:
                raw_material = job_material[job]
    
                if remaining_material[raw_material] + 1e-6 < s_j_prime[job]:
                    continue
    
                feasible_moves = []
                eligible_machines = [
                    machine for machine in I
                    if el_ir[machine][raw_material] == 1
                ]
    
                for machine in eligible_machines:
                    candidate_batches = get_same_material_batches(
                        new_solution, data, machine, raw_material
                    )
    
                    active_batches = sorted(set(
                        new_solution[j][0]
                        for j in J
                        if new_solution[j][1] == machine
                        and new_solution[j][0] is not None
                    ))
                    next_batch = (
                        max(active_batches) + 1 if active_batches else 1
                    )
    
                    if next_batch in B_i[machine]:
                        candidate_batches.append(next_batch)
    
                    candidate_batches = list(dict.fromkeys(candidate_batches))
                    
                    for batch in candidate_batches:
                        current_volume = batch_volume[machine][batch - 1]
                        current_height = batch_height[machine][batch - 1]
    
                        if not feasible_batch_after_insertion(
                            data, job, machine, current_volume, current_height
                        ):
                            continue
    
                        candidate_solution = copy.deepcopy(new_solution)
                        candidate_solution[job] = [batch, machine]
    
                        if not (
                            feasibility_5(data, candidate_solution)
                            and feasibility_7(data, candidate_solution)
                            and feasibility_4(data, candidate_solution)
                            and feasibility_6(data, candidate_solution)
                            and feasibility_1(data, candidate_solution)
                            and feasibility_2(data, candidate_solution)
                        ):
                            continue
    
                        candidate_cost = float(
                            calculate_objective(candidate_solution, data)[0]
                        )
    
                        feasible_moves.append({
                            "cost": candidate_cost,
                            "machine": machine,
                            "batch": batch,
                            "solution_after": candidate_solution,
                        })
    
                if not feasible_moves:
                    continue
                
                feasible_moves.sort(key=lambda move: move["cost"])
                best_move = feasible_moves[0]
                best_cost = best_move["cost"]
    
                top_costs = [
                    move["cost"]
                    for move in feasible_moves[:k_regret]
                ]
                while len(top_costs) < k_regret:
                    top_costs.append(top_costs[-1])
    
                regret_value = sum(
                    cost - best_cost for cost in top_costs[1:]
                )
    
                if (
                    best_job_to_insert is None
                    or regret_value > best_job_regret + eps
                    or (
                        abs(regret_value - best_job_regret) <= eps
                        and best_cost < best_job_best_cost - eps
                    )
                ):
                    best_job_to_insert = job
                    best_job_regret = regret_value
                    best_job_best_cost = best_cost
                    best_job_best_move = best_move
    
            if best_job_to_insert is None:
                break
            
            new_solution = best_job_best_move["solution_after"]
            new_solution, _ = rep_3(new_solution, data)
            inserted_jobs.append(best_job_to_insert)
    
        new_solution, rep_3_info = rep_3(new_solution, data)
        still_rejected = get_rejected_jobs(new_solution, data)
    
        info = {
            "inserted_jobs": inserted_jobs,
            "still_rejected": still_rejected,
            "k_regret": k_regret,
            "rep_3_info": rep_3_info,
        }
    
        return new_solution, info
        
        
        
        
        
    
    # ------------------------------------------------------------
    # Repair 7: Merge same-material batches on the same machine
    # ------------------------------------------------------------
    def rep_7(solution, data, rng):
        """
        Randomly select a same-machine, same-material batch pair.
        Move jobs from the batch with fewer jobs into the larger batch,
        one at a time, while preserving BVC feasibility.
    
        A partial merge is allowed. Objective improvement is not required.
        Solution format: solution[job] = [batch, machine].
        """
        
        J = data['J']
        I = data['I']
        job_material = data['job_material']
    
        new_solution = copy.deepcopy(solution)
    
        batch_volume, batch_weight, batch_material, batch_height = (
            build_batch_loads(new_solution, data)
        )
    
        batch_jobs = {}
        candidate_pairs = []
    
        for machine in I:
            active_batches = sorted(set(
                new_solution[job][0]
                for job in J
                if new_solution[job][1] == machine
                and new_solution[job][0] is not None
            ))
    
            batches_by_material = {}
            
            for batch in active_batches:
                jobs_in_batch = [
                    job for job in J
                    if new_solution[job][1] == machine
                    and new_solution[job][0] == batch
                ]
                batch_jobs[(machine, batch)] = jobs_in_batch
                material = job_material[jobs_in_batch[0]]
    
                if any(
                    job_material[job] != material
                    for job in jobs_in_batch
                ):
                    raise ValueError(
                        f"Batch ({machine}, {batch}) has mixed materials "
                        "in rep_7."
                    )
    
                batches_by_material.setdefault(material, []).append(batch)
    
            for material, batch_list in batches_by_material.items():
                for idx1 in range(len(batch_list)):
                    for idx2 in range(idx1 + 1, len(batch_list)):
                        candidate_pairs.append((
                            machine, material,
                            batch_list[idx1], batch_list[idx2],
                        ))
    
        if not candidate_pairs:
            new_solution, rep_3_info = rep_3(new_solution, data)
            return new_solution, {
                "moved_jobs": [],
                "n_moved": 0,
                "source_batch": None,
                "target_batch": None,
                "machine": None,
                "material": None,
                "old_assignments": {},
                "rep_3_info": rep_3_info,
                "meta": {
                    "note": "No same-machine same-material batch pairs available."
                },
            }
    
        selected_machine, selected_material, batch_1, batch_2 = (
            rng.choice(candidate_pairs)
        )
        
        if (
            len(batch_jobs[(selected_machine, batch_1)])
            >= len(batch_jobs[(selected_machine, batch_2)])
        ):
            target_batch, source_batch = batch_1, batch_2
        else:
            target_batch, source_batch = batch_2, batch_1
    
        source_jobs = list(batch_jobs[(selected_machine, source_batch)])
        rng.shuffle(source_jobs)
    
        moved_jobs = []
        old_assignments = {}
    
        for job in source_jobs:
            current_target_volume = (
                batch_volume[selected_machine][target_batch - 1]
            )
            current_target_height = (
                batch_height[selected_machine][target_batch - 1]
            )
    
            if not feasible_batch_after_insertion(
                data, job, selected_machine,
                current_target_volume, current_target_height
            ):
                continue
    
            old_batch, old_machine = new_solution[job]
            candidate_solution = copy.deepcopy(new_solution)
            candidate_solution[job] = [target_batch, selected_machine]
    
            source_empty = not any(
                candidate_solution[j][1] == selected_machine
                and candidate_solution[j][0] == source_batch
                for j in J
            )
    
            # Close the gap before checking consecutive batch numbering.
            if source_empty:
                candidate_solution, _ = rep_3(candidate_solution, data)
    
            if not (
                feasibility_5(data, candidate_solution)
                and feasibility_7(data, candidate_solution)
                and feasibility_4(data, candidate_solution)
                and feasibility_6(data, candidate_solution)
                and feasibility_1(data, candidate_solution)
                and feasibility_2(data, candidate_solution)
            ):
                continue
    
            new_solution = candidate_solution
            old_assignments[job] = {
                "batch": old_batch,
                "machine": old_machine,
            }
            moved_jobs.append(job)
    
            # Reindexing may have changed the original batch labels.
            if source_empty:
                break
    
            batch_volume, batch_weight, batch_material, batch_height = (
                build_batch_loads(new_solution, data)
            )
    
        new_solution, rep_3_info = rep_3(new_solution, data)
        
        info = {
            "moved_jobs": moved_jobs,
            "n_moved": len(moved_jobs),
            "source_batch": source_batch,
            "target_batch": target_batch,
            "machine": selected_machine,
            "material": selected_material,
            "old_assignments": old_assignments,
            "rep_3_info": rep_3_info,
        }
    
        return new_solution, info
            
            
    
    
    # ------------------------------------------------------------
    # Repair 8: Swap two active batches
    # ------------------------------------------------------------
    def rep_8(solution, data, rng):
        """
        Swap two complete batches on the same or different machines.
        Materials may be the same or different.
    
        Prefer cross-machine, different-material swaps, then other
        cross-machine swaps, then same-machine swaps.
        Return the first feasible swap.
    
        Solution format: solution[job] = [batch, machine].
        """
        
        J = data['J']
        I = data['I']
        job_material = data['job_material']
        el_ir = data['el_ir']
    
        new_solution = copy.deepcopy(solution)
        batch_jobs = {}
        batch_mat = {}
    
        for machine in I:
            active_batches = sorted(set(
                new_solution[job][0]
                for job in J
                if new_solution[job][1] == machine
                and new_solution[job][0] is not None
            ))
    
            for batch in active_batches:
                jobs_in_batch = [
                    job for job in J
                    if new_solution[job][1] == machine
                    and new_solution[job][0] == batch
                ]
    
                material = job_material[jobs_in_batch[0]]
                
                if any(
                    job_material[job] != material
                    for job in jobs_in_batch
                ):
                    raise ValueError(
                        f"Batch ({machine}, {batch}) has mixed materials."
                    )
    
                batch_jobs[(machine, batch)] = jobs_in_batch
                batch_mat[(machine, batch)] = material
    
        active_batch_keys = list(batch_jobs.keys())
        candidate_pairs = []
        
        for idx1 in range(len(active_batch_keys)):
            for idx2 in range(idx1 + 1, len(active_batch_keys)):
                machine_1, batch_1 = active_batch_keys[idx1]
                machine_2, batch_2 = active_batch_keys[idx2]
                material_1 = batch_mat[(machine_1, batch_1)]
                material_2 = batch_mat[(machine_2, batch_2)]
    
                if machine_1 != machine_2:
                    if (
                        el_ir[machine_1][material_2] != 1
                        or el_ir[machine_2][material_1] != 1
                    ):
                        continue
    
                if machine_1 != machine_2 and material_1 != material_2:
                    strength = 3
                elif machine_1 != machine_2:
                    strength = 2
                else:
                    strength = 1
    
                candidate_pairs.append((
                    strength,
                    machine_1, batch_1, material_1,
                    machine_2, batch_2, material_2,
                ))
    
        rng.shuffle(candidate_pairs)
        candidate_pairs.sort(key=lambda pair: pair[0], reverse=True)
        
        for (
            strength,
            machine_1, batch_1, material_1,
            machine_2, batch_2, material_2,
        ) in candidate_pairs:
            jobs_1 = batch_jobs[(machine_1, batch_1)]
            jobs_2 = batch_jobs[(machine_2, batch_2)]
            candidate_solution = copy.deepcopy(new_solution)
            old_assignments = {}
    
            for job in jobs_1:
                old_assignments[job] = {
                    "batch": new_solution[job][0],
                    "machine": new_solution[job][1],
                }
                candidate_solution[job] = [batch_2, machine_2]
    
            for job in jobs_2:
                old_assignments[job] = {
                    "batch": new_solution[job][0],
                    "machine": new_solution[job][1],
                }
                candidate_solution[job] = [batch_1, machine_1]
    
            if not (
                feasibility_5(data, candidate_solution)
                and feasibility_7(data, candidate_solution)
                and feasibility_4(data, candidate_solution)
                and feasibility_6(data, candidate_solution)
                and feasibility_1(data, candidate_solution)
                and feasibility_2(data, candidate_solution)
            ):
                continue
    
            candidate_solution, rep_3_info = rep_3(candidate_solution, data)
            
            swapped_jobs = jobs_1 + jobs_2
            new_assignments = {
                job: {
                    "batch": candidate_solution[job][0],
                    "machine": candidate_solution[job][1],
                }
                for job in swapped_jobs
            }
    
            info = {
                "swapped_batches": [
                    {
                        "machine": machine_1,
                        "batch": batch_1,
                        "material": material_1,
                    },
                    {
                        "machine": machine_2,
                        "batch": batch_2,
                        "material": material_2,
                    },
                ],
                "swapped_jobs": swapped_jobs,
                "old_assignments": old_assignments,
                "new_assignments": new_assignments,
                "rep_3_info": rep_3_info,
                "meta": {
                    "same_material": material_1 == material_2,
                    "swap_type": (
                        "different_machine"
                        if machine_1 != machine_2
                        else "same_machine_different_batch"
                    ),
                    "strength": strength,
                },
            }
            return candidate_solution, info
    
        new_solution, rep_3_info = rep_3(new_solution, data)
        
        if len(active_batch_keys) < 2:
            note = "fewer than 2 active batches"
        elif not candidate_pairs:
            note = "no eligible batch pairs found"
        else:
            note = "no feasible batch swap found"
    
        return new_solution, {
            "swapped_batches": [],
            "swapped_jobs": [],
            "old_assignments": {},
            "new_assignments": {},
            "rep_3_info": rep_3_info,
            "meta": {"note": note},
        }
                
                
                
              
        
        
        
    
    # ------------------------------------------------------------
    # Repair 9: Fast accepted-job relocation
    # ------------------------------------------------------------
    def rep_9(solution, data, p, rng, eps=1e-12):
        """
        Examine at most five randomly selected accepted jobs.
        Return immediately upon finding an improving feasible relocation.
    
        p is retained for call compatibility and is unused.
        Solution format: solution[job] = [batch, machine].
        """
        
        if not math.isfinite(eps) or eps < 0:
            raise ValueError("eps must be finite and nonnegative in rep_9.")
    
        J = data['J']
        I = data['I']
        B_i = data['B_i']
        job_material = data['job_material']
        el_ir = data['el_ir']
    
        new_solution = copy.deepcopy(solution)
    
        accepted_jobs = [
            job for job in J
            if new_solution[job][0] is not None
            and new_solution[job][1] is not None
        ]
    
        if not accepted_jobs:
            new_solution, rep_3_info = rep_3(new_solution, data)
            return new_solution, {
                "moved_job": None,
                "improved": False,
                "rep_3_info": rep_3_info,
            }
    
        rng.shuffle(accepted_jobs)
        max_jobs_to_check = min(5, len(accepted_jobs))
        selected_jobs = accepted_jobs[:max_jobs_to_check]
        
        base_obj = float(calculate_objective(new_solution, data)[0])
    
        for job in selected_jobs:
            old_batch, old_machine = new_solution[job]
            raw_material = job_material[job]
    
            # Remove the job temporarily and close any batch-numbering gap.
            temp_solution = copy.deepcopy(new_solution)
            temp_solution[job] = [None, None]
            temp_solution, _ = rep_3(temp_solution, data)
    
            batch_volume, batch_weight, batch_material, batch_height = (
                build_batch_loads(temp_solution, data)
            )
    
            eligible_machines = [
                machine for machine in I
                if el_ir[machine][raw_material] == 1
            ]
            rng.shuffle(eligible_machines)
    
            for machine in eligible_machines:
                candidate_batches = get_same_material_batches(
                    temp_solution, data, machine, raw_material
                )
    
                active_batches = sorted(set(
                    temp_solution[j][0]
                    for j in J
                    if temp_solution[j][1] == machine
                    and temp_solution[j][0] is not None
                ))
                next_batch = max(active_batches) + 1 if active_batches else 1
    
                if next_batch in B_i[machine]:
                    candidate_batches.append(next_batch)
    
                candidate_batches = list(dict.fromkeys(candidate_batches))
                rng.shuffle(candidate_batches)
                
                for batch in candidate_batches:
                    current_volume = batch_volume[machine][batch - 1]
                    current_height = batch_height[machine][batch - 1]
    
                    if not feasible_batch_after_insertion(
                        data, job, machine, current_volume, current_height
                    ):
                        continue
    
                    candidate_solution = copy.deepcopy(temp_solution)
                    candidate_solution[job] = [batch, machine]
    
                    if not (
                        feasibility_5(data, candidate_solution)
                        and feasibility_7(data, candidate_solution)
                        and feasibility_4(data, candidate_solution)
                        and feasibility_6(data, candidate_solution)
                        and feasibility_1(data, candidate_solution)
                        and feasibility_2(data, candidate_solution)
                    ):
                        continue
    
                    candidate_obj = float(
                        calculate_objective(candidate_solution, data)[0]
                    )
    
                    if candidate_obj < base_obj - eps:
                        candidate_solution, rep_3_info = rep_3(
                            candidate_solution, data
                        )
                        new_batch, new_machine = candidate_solution[job]
                        
                        return candidate_solution, {
                            "moved_job": job,
                            "old_assignment": {
                                "batch": old_batch,
                                "machine": old_machine,
                            },
                            "new_assignment": {
                                "batch": new_batch,
                                "machine": new_machine,
                            },
                            "old_objective": base_obj,
                            "new_objective": candidate_obj,
                            "improved": True,
                            "rep_3_info": rep_3_info,
                        }
                    
        new_solution, rep_3_info = rep_3(new_solution, data)
    
        return new_solution, {
            "moved_job": None,
            "improved": False,
            "old_objective": base_obj,
            "new_objective": base_obj,
            "rep_3_info": rep_3_info,
        }
        
        
        
    
    
    repair_ops = {
        "rep_1": rep_1,
        "rep_2": rep_2,
        "rep_3": rep_3,
        "rep_4": rep_4,
        "rep_5": rep_5,
        "rep_6": rep_6,
        "rep_7": rep_7,
        "rep_8": rep_8,
        "rep_9": rep_9,
   
    }
    
        
    
    
    
    return repair_ops



    








