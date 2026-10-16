#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 22:03:17 2026

@author: parisa
"""

import copy
import math
from repair_operators import repair_operators
from calculate_objective import calculate_objective


def destroy_operators():
    
   
    # ------------------------------------------------------------
    # Destroy 1: Remove q% of accepted jobs randomly
    # ------------------------------------------------------------
    def des_1(solution, data, q, rng):
        """
        Randomly removes q% of accepted jobs from the solution.
        q must be between 0 and 1; for example, 0.20 means 20%.
        Solution format: solution[job] = [batch, machine].
        solution[job][0] = batch
        solution[job][1] = machine
        """
        
        if not math.isfinite(q) or not 0 <= q <= 1:
            raise ValueError("q must be a finite fraction between 0 and 1 in des_1.")

        J = data['J']

        # Copy solution
        new_solution = copy.deepcopy(solution)

        # ------------------------------------------------------------
        # Identify accepted jobs
        # ------------------------------------------------------------
        accepted_jobs = [
            job for job in J
            if new_solution[job][0] is not None
            and new_solution[job][1] is not None
        ]

        n_acc = len(accepted_jobs)
        #print('n_acc', n_acc)

        if n_acc == 0:
            info = {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "rep_3_info": None
            }
            return new_solution, info

        # ------------------------------------------------------------
        # Select jobs to remove
        # ------------------------------------------------------------
        n_remove = min(math.ceil(q * n_acc), n_acc)
        

        if n_remove == 0:
            info = {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "rep_3_info": None
            }
            return new_solution, info

        removed_jobs = rng.sample(accepted_jobs, n_remove)
        # print('n_remove', n_remove)
        # print('removed_jobs', removed_jobs)
        
        
        # ------------------------------------------------------------
        # Store old assignments and remove selected jobs
        # ------------------------------------------------------------
        old_assignments = {}

        for job in removed_jobs:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1]
            }

            #print('old_assignments', old_assignments)
            # Remove job from solution
            new_solution[job] = [None, None]

        # ------------------------------------------------------------
        # Reindex batch IDs after removal
        # ------------------------------------------------------------
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)

        info = {
            "n_removed": n_remove,
            "removed_jobs": removed_jobs,
            "old_assignments": old_assignments,
            "rep_3_info": rep_3_info
        }

        return new_solution, info
    
    
    

        
        
        
    
    # ------------------------------------------------------------
    # Destroy 2: Shaw / related removal
    # Remove top q% jobs most related to a random seed job
    # Relatedness uses AM production attributes only
    # ------------------------------------------------------------
    def des_2(solution, data, q, rng, eps=1e-12):
        """
        Relatedness is based on:
            - same raw material
            - similar due date
            - similar ready/release time
            - same machine
            - same batch on the same machine
    
        Solution format:
            solution[job][0] = batch
            solution[job][1] = machine
        """
        
        if not math.isfinite(q) or not 0 <= q <= 1:
            raise ValueError("q must be a finite fraction between 0 and 1 in des_2.")

        if not math.isfinite(eps) or eps <= 0:
            raise ValueError("eps must be finite and positive in des_2.")
            
    
    
        J = data['J']
        job_material = data['job_material']
        d_j = data['d_j']
        r_j = data['r_j']
    
        new_solution = copy.deepcopy(solution)
    
        # ------------------------------------------------------------
        # Identify accepted jobs and their production assignments
        # ------------------------------------------------------------
        accepted_jobs = []
        prod_assign = {}
    
        for job in J:
            batch = new_solution[job][0]
            machine = new_solution[job][1]
    
            if batch is not None and machine is not None:
                accepted_jobs.append(job)
                prod_assign[job] = (machine, batch)
                
        # print('accepted_jobs', accepted_jobs)
        # print('prod_assign', prod_assign)
        
        n_acc = len(accepted_jobs)
        n_remove = min(math.ceil(q * n_acc), n_acc)
        
        if n_remove == 0:
            return new_solution, {
                "n_removed": 0,
                "removed_jobs": [],
                "seed_job": None,
                "relatedness_score": {},
                "old_assignments": {},
                "rep_3_info": None,
            }
    
     
    
        # ------------------------------------------------------------
        # Pick random seed job
        # ------------------------------------------------------------
        seed_job = rng.choice(accepted_jobs)
        # print('seed_job', seed_job)

        # seed attributes
        seed_material = job_material[seed_job]
        seed_due = float(d_j[seed_job])
        seed_ready = float(r_j[seed_job])
        seed_machine, seed_batch = prod_assign[seed_job]
     
    
        # ------------------------------------------------------------
        # Normalize due-date similarity
        # ------------------------------------------------------------
        due_vals = [float(d_j[job]) for job in accepted_jobs]
        due_range = max(due_vals) - min(due_vals)
        # print('due_vals', due_vals)
        # print('due_range', due_range)
    
        if due_range <= eps:
            due_range = 1.0
    
        # ------------------------------------------------------------
        # Normalize ready-time similarity
        # ------------------------------------------------------------
        ready_vals = [float(r_j[job]) for job in accepted_jobs]
        ready_range = max(ready_vals) - min(ready_vals)
        # print('ready_vals', ready_vals)
        # print('ready_range', ready_range)
    
        if ready_range <= eps:
            ready_range = 1.0
    
        # ------------------------------------------------------------
        # Relatedness weights
        # Higher score = more related to seed
        # ------------------------------------------------------------
        w_material = 4.0
        w_due = 2.0
        w_ready = 2.0
        w_machine = 2.0
        w_batch = 3.0
    
        relatedness_score = {}
    
        for job in accepted_jobs:
            # print('job', job)
    
            if job == seed_job:
                relatedness_score[job] = float("inf")
                continue
    
            job_mat = job_material[job]
            job_due = float(d_j[job])
            job_ready = float(r_j[job])
            job_machine, job_batch = prod_assign[job]
         
    
            same_material = 1.0 if job_mat == seed_material else 0.0
            same_machine = 1.0 if job_machine == seed_machine else 0.0
            same_batch = 1.0 if (job_machine == seed_machine and job_batch == seed_batch) else 0.0
    
            due_similarity = max(0.0, 1.0 - abs(job_due - seed_due) / due_range)
            ready_similarity = max(0.0, 1.0 - abs(job_ready - seed_ready) / ready_range)
            # print('due_similarity', due_similarity)
            # print('ready_similarity', ready_similarity)
    
            score = (
                w_material * same_material
                + w_due * due_similarity
                + w_ready * ready_similarity
                + w_machine * same_machine
                + w_batch * same_batch
            )
    
            relatedness_score[job] = score
            # print('relatedness_score', relatedness_score)
    
        # ------------------------------------------------------------
        # Select top related jobs
        # Random shuffle first gives random tie-breaking
        # ------------------------------------------------------------
        candidate_jobs = accepted_jobs.copy()
        rng.shuffle(candidate_jobs)
    
        candidate_jobs.sort(key=lambda job: relatedness_score[job], reverse=True)
        # print('candidate_jobs', candidate_jobs)
    
        removed_jobs = candidate_jobs[:n_remove]
        # print('removed_jobs', removed_jobs)
    
        # ------------------------------------------------------------
        # Store old assignments and remove selected jobs
        # ------------------------------------------------------------
        old_assignments = {}
    
        for job in removed_jobs:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1]
            }
    
            new_solution[job][0] = None
            new_solution[job][1] = None
    
        # ------------------------------------------------------------
        # Reindex batch IDs after removal
        # ------------------------------------------------------------
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)
        
    
        info = {
            "n_removed": n_remove,
            "removed_jobs": removed_jobs,
            "seed_job": seed_job,
            "relatedness_score": relatedness_score,
            "old_assignments": old_assignments,
            "rep_3_info": rep_3_info
        }
    
        return new_solution, info
    
    
    
    
    
    
    
    
    # ------------------------------------------------------------
    # Destroy 3: A priori related removal
    # Remove top q% jobs most related to a randomly chosen seed job
    # Relatedness uses static job data only
    # ------------------------------------------------------------
    def des_3(solution, data, q, rng, apriori_scores):
        """
        This operator uses precomputed static relatedness scores.
        The scores are based only on problem data, not the current solution.

        Relatedness uses:
            - same raw material
            - similar due date
            - similar ready/release time

        Solution format:
            solution[job][0] = batch
            solution[job][1] = machine
        """

        if not (0 <= q <= 1):
            raise ValueError("q must be between 0 and 1 in des_3.")

        J = data['J']

        # Copy solution
        new_solution = copy.deepcopy(solution)

        # ------------------------------------------------------------
        # Identify accepted jobs
        # ------------------------------------------------------------
        accepted_jobs = [
            job for job in J
            if new_solution[job][0] is not None
            and new_solution[job][1] is not None
        ]
        
        n_acc = len(accepted_jobs)
        n_remove = min(math.ceil(q * n_acc), n_acc)
        
        if n_remove == 0:
            return new_solution, {
                "n_removed": 0,
                "removed_jobs": [],
                "seed_job": None,
                "old_assignments": {},
                "rep_3_info": None,
            }
        
    
        

        # ------------------------------------------------------------
        # Pick random seed job
        # ------------------------------------------------------------
        seed_job = rng.choice(accepted_jobs)
        # print('seed_job', seed_job)

        # ------------------------------------------------------------
        # Rank accepted jobs by a priori relatedness to seed
        # ------------------------------------------------------------
        def score_for(job):
            if job == seed_job:
                return float("inf")
            return apriori_scores[(seed_job, job)]

        candidate_jobs = accepted_jobs.copy()

        # Random shuffle gives random tie-breaking
        rng.shuffle(candidate_jobs)

        candidate_jobs.sort(key=score_for, reverse=True)
        removed_jobs = candidate_jobs[:n_remove]
        # print('candidate_jobs', candidate_jobs)
        # print('removed_jobs', removed_jobs)

        # ------------------------------------------------------------
        # Store old assignments and remove selected jobs
        # ------------------------------------------------------------
        old_assignments = {}

        for job in removed_jobs:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1]
            }

            new_solution[job][0] = None
            new_solution[job][1] = None

        # ------------------------------------------------------------
        # Reindex batch IDs after removal
        # ------------------------------------------------------------
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)

        info = {
            "n_removed": n_remove,
            "removed_jobs": removed_jobs,
            "seed_job": seed_job,
            "old_assignments": old_assignments,
            "rep_3_info": rep_3_info
        }

        return new_solution, info
    
    
    
    
    
    # ------------------------------------------------------------
    # Destroy 4: Remove q% of accepted jobs with lowest marginal contribution
    # Cost-minimization version
    # ------------------------------------------------------------
    def des_4(solution, data, q, rng):
        """
        Remove q% of accepted jobs with the lowest marginal contribution.

        Since it is a cost-minimization problem:

            cost_change_j = Cost(S without job j) - Cost(S)

        Interpretation:
            - If cost_change_j is large positive:
                Removing job j increases total cost, so job j is valuable.
            - If cost_change_j is small or negative:
                Removing job j does not hurt or may reduce total cost,
                so job j is a good candidate for removal.

        Therefore, this operator removes jobs with the lowest cost_change_j.

        Solution format:
            solution[job][0] = batch
            solution[job][1] = machine
        """

        if not (0 <= q <= 1):
            raise ValueError("q must be between 0 and 1 in des_4.")

        J = data['J']

        new_solution = copy.deepcopy(solution)

        # ------------------------------------------------------------
        # Identify accepted jobs
        # ------------------------------------------------------------
        accepted_jobs = [
            job for job in J
            if new_solution[job][0] is not None
            and new_solution[job][1] is not None
        ]

        #print('accepted_jobs', accepted_jobs)

        if not accepted_jobs:
            return new_solution, {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "job_cost_change": {},
                "rep_3_info": None
            }

        # ------------------------------------------------------------
        # Base cost
        # ------------------------------------------------------------
        base_cost = float(calculate_objective(new_solution, data)[0])
        #print('base_cost', base_cost)

        # ------------------------------------------------------------
        # Marginal cost change for each accepted job
        # ------------------------------------------------------------
        job_cost_change = {}

        for job in accepted_jobs:
            #print('job', job)
            s_wo = copy.deepcopy(new_solution)

            # Remove job
            s_wo[job][0] = None
            s_wo[job][1] = None

            # Reindex batches before objective calculation
            # This avoids non-sequential batch issues.
            repairs = repair_operators()
            s_wo, _  = repairs["rep_3"](s_wo, data)

            cost_without_job = float(calculate_objective(s_wo, data)[0])
            #print('cost_without_job', cost_without_job)

            # Lower value means this job is a better candidate for removal
            job_cost_change[job] = cost_without_job - base_cost
            #print('job_cost_change', job_cost_change)

        # ------------------------------------------------------------
        # Select q% jobs with lowest marginal contribution
        # ------------------------------------------------------------
        
        n_acc = len(accepted_jobs)
        n_remove = min(math.ceil(q * n_acc), n_acc)
        
        if n_remove == 0:
            return new_solution, {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "job_cost_change": {},
                "rep_3_info": None,
            }



        # Random tie-breaking before sorting
        candidate_jobs = accepted_jobs.copy()
        rng.shuffle(candidate_jobs)

        candidate_jobs.sort(key=lambda job: job_cost_change[job])

        removed_jobs = candidate_jobs[:n_remove]
      

        # ------------------------------------------------------------
        # Store old assignments and remove selected jobs
        # ------------------------------------------------------------
        old_assignments = {}

        for job in removed_jobs:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1]
            }

            new_solution[job][0] = None
            new_solution[job][1] = None

        # ------------------------------------------------------------
        # Reindex batch IDs after removal
        # ------------------------------------------------------------
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)
        

        info = {
            "n_removed": n_remove,
            "removed_jobs": removed_jobs,
            "old_assignments": old_assignments,
            "job_cost_change": job_cost_change,
            "base_cost": base_cost,
            "rep_3_info": rep_3_info
        }

        return new_solution, info
    
    
    
    
    
    
    
    
    
    # ------------------------------------------------------------
    # Destroy 5: Pick one machine and one batch randomly,
    # then remove all jobs in that batch
    # ------------------------------------------------------------
    def des_5(solution, data, rng):
        """
        Randomly selects one machine with at least one active batch,
        then randomly selects one batch on that machine,
        and removes all jobs assigned to that batch.

        Solution format:
            solution[job][0] = batch
            solution[job][1] = machine
        """

        J = data['J']
        I = data['I']

        new_solution = copy.deepcopy(solution)

        # ------------------------------------------------------------
        # Find machines with at least one assigned job
        # ------------------------------------------------------------
        candidate_machines = []

        for machine in I:
            has_assigned_job = any(
                new_solution[job][1] == machine
                and new_solution[job][0] is not None
                for job in J
            )

            if has_assigned_job:
                candidate_machines.append(machine)

        # print('candidate_machines', candidate_machines)

        if not candidate_machines:
            info = {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "machine": None,
                "batch": None,
                "rep_3_info": None
            }
            return new_solution, info

        # ------------------------------------------------------------
        # Pick one machine randomly
        # ------------------------------------------------------------
        selected_machine = rng.choice(candidate_machines)
        # print('selected_machine', selected_machine)

        # ------------------------------------------------------------
        # Find active batches on selected machine
        # ------------------------------------------------------------
        active_batches = sorted(set(
            new_solution[job][0]
            for job in J
            if new_solution[job][1] == selected_machine
            and new_solution[job][0] is not None
        ))

        # print('active_batches', active_batches)

        if not active_batches:
            info = {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "machine": selected_machine,
                "batch": None,
                "rep_3_info": None
            }
            return new_solution, info

        # ------------------------------------------------------------
        # Pick one batch randomly
        # ------------------------------------------------------------
        selected_batch = rng.choice(active_batches)
        # print('selected_batch', selected_batch)

        # ------------------------------------------------------------
        # Find all jobs in selected machine-batch pair
        # ------------------------------------------------------------
        removed_jobs = [
            job for job in J
            if new_solution[job][1] == selected_machine
            and new_solution[job][0] == selected_batch
        ]
        # print('removed_jobs', removed_jobs)

        # ------------------------------------------------------------
        # Store old assignments and remove jobs
        # ------------------------------------------------------------
        old_assignments = {}

        for job in removed_jobs:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1]
            }

            new_solution[job][0] = None
            new_solution[job][1] = None

        # ------------------------------------------------------------
        # Reindex batch IDs after removal
        # ------------------------------------------------------------
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)
        

        info = {
            "n_removed": len(removed_jobs),
            "removed_jobs": removed_jobs,
            "old_assignments": old_assignments,
            "machine": selected_machine,
            "batch": selected_batch,
            "rep_3_info": rep_3_info
        }

        return new_solution, info
    
    
    
    
    # ------------------------------------------------------------
    # Destroy 6: Remove one batch with highest tardiness score
    # ------------------------------------------------------------
    def des_6(solution, data, rng):
        """
        Remove the batch with the highest tardiness score.

        Batch tardiness score:
            score_(i,b) = sum_{j in batch(i,b)} c_j_late[j] * T_j

        Higher score = worse batch.

        Solution format:
            solution[job][0] = batch
            solution[job][1] = machine
        """

        J = data['J']
        I = data['I']
        c_j_late = data['c_j_late']

        new_solution = copy.deepcopy(solution)

        # ------------------------------------------------------------
        # Build list of active machine-batch pairs
        # ------------------------------------------------------------
        used_batches = []

        for machine in I:
            active_batches = sorted(set(
                new_solution[job][0]
                for job in J
                if new_solution[job][1] == machine
                and new_solution[job][0] is not None
            ))

            # print('active_batches', active_batches)

            for batch in active_batches:
                used_batches.append((machine, batch))

        # print('used_batches', used_batches)

        if not used_batches:
            info = {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "selected_batch": None,
                "batch_tardiness_score": {},
                "rep_3_info": None
            }
            return new_solution, info

        # ------------------------------------------------------------
        # Calculate objective and get job tardiness
        # ------------------------------------------------------------
        obj = calculate_objective(new_solution, data)
        # print('obj', obj)

        # In your calculate_objective return tuple:
        # obj[12] = job_tardiness
        job_tardiness = obj[12]
        # print('job_tardiness', job_tardiness)

        # ------------------------------------------------------------
        # Compute tardiness score for each active batch
        # ------------------------------------------------------------
        batch_tardiness_score = {}
        batch_to_jobs = {}

        for machine, batch in used_batches:
            # print('machine, batch', machine, batch)

            jobs_in_batch = [
                job for job in J
                if new_solution[job][1] == machine
                and new_solution[job][0] == batch
            ]

            batch_to_jobs[(machine, batch)] = jobs_in_batch
            # print('batch_to_jobs', batch_to_jobs)

            score = sum(
                float(c_j_late[job]) * float(job_tardiness.get(job, 0))
                for job in jobs_in_batch)

            batch_tardiness_score[(machine, batch)] = score
            # print('batch_tardiness_score', batch_tardiness_score)

        # ------------------------------------------------------------
        # Select batch with highest tardiness score
        # Random shuffle first gives random tie-breaking
        # ------------------------------------------------------------
        rng.shuffle(used_batches)
        

        used_batches.sort(
            key=lambda machine_batch: batch_tardiness_score[machine_batch],
            reverse=True)

        # print('used_batches', used_batches)

        selected_machine, selected_batch = used_batches[0]

        removed_jobs = batch_to_jobs[(selected_machine, selected_batch)]
        # print('selected_machine, selected_batch', selected_machine, selected_batch)
        # print('removed_jobs', removed_jobs)

        # ------------------------------------------------------------
        # Store old assignments and remove selected jobs
        # ------------------------------------------------------------
        old_assignments = {}

        for job in removed_jobs:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1]
            }

            new_solution[job][0] = None
            new_solution[job][1] = None

        # ------------------------------------------------------------
        # Reindex batch IDs after removal
        # ------------------------------------------------------------
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)

        info = {
            "n_removed": len(removed_jobs),
            "removed_jobs": removed_jobs,
            "old_assignments": old_assignments,
            "selected_batch": (selected_machine, selected_batch),
            "batch_tardiness_score": batch_tardiness_score,
            "rep_3_info": rep_3_info
        }

        return new_solution, info
    
    
    
    
    
    
    
   

        
        
        
        
    
    # ------------------------------------------------------------
    # Destroy 7: Remove q% of jobs with highest individual tardiness cost
    # ------------------------------------------------------------
    def des_7(solution, data, q, rng):
        """
        
        Individual tardiness cost:
            score_j = c_j_late[j] * max(0, completion_time_j - D_j)
    
        Higher score = worse individual job contribution to tardiness.
    
        Solution format:
            solution[job][0] = batch
            solution[job][1] = machine
        """
        
        if not (0 <= q <= 1):
            raise ValueError("q must be between 0 and 1 in des_7.")

        J = data['J']
        c_j_late = data['c_j_late']
        
        new_solution = copy.deepcopy(solution)

        # Identify accepted jobs.
        assigned_jobs = [
            job for job in J
            if new_solution[job][0] is not None
            and new_solution[job][1] is not None
        ]

        n_remove = min(
            math.ceil(q * len(assigned_jobs)),
            len(assigned_jobs)
        )

        if n_remove == 0:
            info = {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "job_tardiness_score": {},
                "q": q,
                "rep_3_info": None,
            }
            return new_solution, info

        # obj[12] contains job tardiness.
        obj = calculate_objective(new_solution, data)
        job_tardiness = obj[12]

        job_tardiness_score = {}

    
        for job in assigned_jobs:
            score = float(c_j_late[job]) * float(job_tardiness.get(job, 0))
            job_tardiness_score[job] = score
    
        # ------------------------------------------------------------
        # Select top q% jobs by tardiness score
        # Random shuffle first gives random tie-breaking
        # ------------------------------------------------------------
        rng.shuffle(assigned_jobs)
        
        assigned_jobs.sort(
            key=lambda job: job_tardiness_score[job],
            reverse=True
        )

        removed_jobs = assigned_jobs[:n_remove]

    
        # ------------------------------------------------------------
        # Store old assignments and remove selected jobs
        # ------------------------------------------------------------
        old_assignments = {}
    
        for job in removed_jobs:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1]}
    
            new_solution[job][0] = None
            new_solution[job][1] = None
    
        # ------------------------------------------------------------
        # Reindex batch IDs after removal
        # ------------------------------------------------------------
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)
    
        info = {
            "n_removed": len(removed_jobs),
            "removed_jobs": removed_jobs,
            "old_assignments": old_assignments,
            "job_tardiness_score": job_tardiness_score,
            "q": q,
            "rep_3_info": rep_3_info}
    
        return new_solution, info
    
    
    
    
    
    
    
    
    # ------------------------------------------------------------
    # Destroy 8: Randomly split a batch, remove ceil(size/2) jobs
    # ------------------------------------------------------------
    def des_8(solution, data, rng):
        """
        Select a batch randomly (weighted by batch size — larger batches
        more likely). Randomly split it: remove a random subset of
        ceil(size/2) jobs from the batch. Removed jobs become unassigned.
    
        Batch selection probability:
            P(batch) = size(batch) / sum of all batch sizes
    
        Solution format:
            solution[job][0] = batch
            solution[job][1] = machine
        """
        
        J = data['J']
        I = data['I']

        new_solution = copy.deepcopy(solution)

        # Build active machine-batch pairs and their jobs.
        batch_to_jobs = {}

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
                batch_to_jobs[(machine, batch)] = jobs_in_batch

        if not batch_to_jobs:
            info = {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "selected_batch": None,
                "batch_sizes": {},
                "rep_3_info": None,
            }
            return new_solution, info

        # Select a batch with probability proportional to its job count.
        used_batches = list(batch_to_jobs.keys())
        batch_sizes = [
            len(batch_to_jobs[mb])
            for mb in used_batches
        ]

        selected_machine, selected_batch = rng.choices(
            used_batches,
            weights=batch_sizes,
            k=1
        )[0]

        jobs_in_selected_batch = batch_to_jobs[
            (selected_machine, selected_batch)
        ]

        # Randomly remove ceil(size / 2) jobs.
        n_remove = math.ceil(len(jobs_in_selected_batch) / 2)

        jobs_shuffled = list(jobs_in_selected_batch)
        rng.shuffle(jobs_shuffled)
        removed_jobs = jobs_shuffled[:n_remove]

        old_assignments = {}

        for job in removed_jobs:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1],
            }

            new_solution[job][0] = None
            new_solution[job][1] = None

        # Reindex batch IDs after removal.
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)

        batch_sizes_info = {
            mb: len(jobs)
            for mb, jobs in batch_to_jobs.items()
        }

        info = {
            "n_removed": len(removed_jobs),
            "removed_jobs": removed_jobs,
            "old_assignments": old_assignments,
            "selected_batch": (selected_machine, selected_batch),
            "batch_sizes": batch_sizes_info,
            "rep_3_info": rep_3_info,
        }

        return new_solution, info
    
    
    
    
    
    
    
    def des_9(solution, data, q, rng):
        """
        Randomly select a material represented among accepted jobs,
        then randomly remove a fraction q of those jobs.

        q must be between 0 and 1; for example, 0.20 means 20%.
        Solution format: solution[job] = [batch, machine].
        """

        if not (0 <= q <= 1):
            raise ValueError("q must be between 0 and 1 in des_9.")

        new_solution = copy.deepcopy(solution)
        material_jobs = {}

        for job in data["J"]:
            batch, machine = new_solution[job]

            if batch is not None and machine is not None:
                material = data["job_material"][job]
                material_jobs.setdefault(material, []).append(job)

        if not material_jobs or q == 0:
            return new_solution, {
                "n_removed": 0,
                "removed_jobs": [],
                "old_assignments": {},
                "selected_material": None,
                "jobs_to_remove": [],
                "rep_3_info": None,
            }

        selected_material = rng.choice(list(material_jobs.keys()))
        jobs = material_jobs[selected_material]

        n_remove = min(math.ceil(q * len(jobs)), len(jobs))
        jobs_to_remove = rng.sample(jobs, n_remove)

        old_assignments = {}

        for job in jobs_to_remove:
            old_assignments[job] = {
                "batch": new_solution[job][0],
                "machine": new_solution[job][1],
            }
            new_solution[job] = [None, None]

        # Reindex once after all selected jobs have been removed.
        repairs = repair_operators()
        new_solution, rep_3_info = repairs["rep_3"](new_solution, data)

        info = {
            "n_removed": len(jobs_to_remove),
            "removed_jobs": jobs_to_remove,
            "old_assignments": old_assignments,
            "selected_material": selected_material,
            "jobs_to_remove": jobs_to_remove,
            "rep_3_info": rep_3_info,
        }

        return new_solution, info
    
    
       
            
    
    destroy_ops = {
        "des_1": des_1,
        "des_2": des_2,
        "des_3": des_3,
        "des_4": des_4,
        "des_5": des_5,
        "des_6": des_6,
        "des_7": des_7,
        "des_8": des_8,
        "des_9": des_9,
        
    }
    
    
    
    return destroy_ops






