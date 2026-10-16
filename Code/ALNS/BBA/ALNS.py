#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 21:52:08 2026

@author: parisa
"""




import copy
import math
import random
import time
from collections import Counter

import matplotlib.pyplot as plt

from initial_solution import initial_solution
from calculate_objective import calculate_objective
from destroy_operators import destroy_operators
from repair_operators import repair_operators
from compute_apriori_relatedness import compute_apriori_relatedness
from feasibility import (
    feasibility_1, feasibility_2, feasibility_4,
    feasibility_5, feasibility_6, feasibility_7,
)


def compute_operator_probs(phi, epsilon):
    """SA-AOS probabilities with a minimum probability for every operator."""
    total_operators = len(phi)
    if total_operators == 0:
        raise ValueError("At least one operator is required.")
    if not math.isfinite(epsilon) or not 0 < epsilon < 1 / total_operators:
        raise ValueError("epsilon must be between 0 and 1 / operator count.")
    if any(not math.isfinite(score) or score < 0 for score in phi.values()):
        raise ValueError("Operator scores must be finite and nonnegative.")

    total_score = sum(phi.values())
    
    if total_score == 0:
        return {name: 1 / total_operators for name in phi}

    probabilities = {
        name: epsilon + (1 - total_operators * epsilon) * score / total_score
        for name, score in phi.items()
    }
    total_probability = sum(probabilities.values())
    return {
        name: probability / total_probability
        for name, probability in probabilities.items()
    }



def weighted_pick(names, probabilities, rng):
    return rng.choices(
        names, weights=[probabilities[name] for name in names], k=1
    )[0]


def is_feasible(data, solution):
    return (
        feasibility_5(data, solution)
        and feasibility_7(data, solution)
        and feasibility_4(data, solution)
        and feasibility_6(data, solution)
        and feasibility_1(data, solution)
        and feasibility_2(data, solution)
    )


def run_alns(data, seed=None, verbose=True, plot=True, time_limit=None):
    
    n = data["n"]
    
    if n <= 0:
        raise ValueError("n must be positive.")
        
    if time_limit is not None and (not math.isfinite(time_limit) or time_limit < 0):
        raise ValueError("time_limit must be finite and nonnegative.")

    if seed is None:
        
        seed = random.randint(1, 10**6)
        
    rng = random.Random(seed)
    start_time = time.monotonic()

    max_iter = 20 * n
    eps = 1e-12
    epsilon = 0.02
    # Reset measured in ALNS iterations, retaining the original reset interval.
    G_reset = max(500, int(0.20 * max_iter))
    q_max = 0.3
    q_min = min(q_max, max(2 / n, 0.03))
    p_insert = 0.7
    k_regret = 2
    stagnation_limit = max(100, int(max_iter * 0.02))
    T_start = 20000
    T_end = max(0.005 * T_start, 1.0)
    cooling_rate = 0.999
    
    apriori_scores = compute_apriori_relatedness(data, eps=eps)
    destroys = destroy_operators()
    repairs = repair_operators()
    if "rep_3" not in repairs:
        raise ValueError("rep_3 is required for batch reindexing.")

    destroy_wrappers = {
        "des_1": lambda s, d, q, r: destroys["des_1"](s, d, q, r),
        "des_2": lambda s, d, q, r: destroys["des_2"](s, d, q, r, eps),
        "des_3": lambda s, d, q, r: destroys["des_3"](s, d, q, r, apriori_scores),
        "des_4": lambda s, d, q, r: destroys["des_4"](s, d, q, r),
        "des_5": lambda s, d, q, r: destroys["des_5"](s, d, r),
        "des_6": lambda s, d, q, r: destroys["des_6"](s, d, r),
        "des_7": lambda s, d, q, r: destroys["des_7"](s, d, q, r),
        "des_8": lambda s, d, q, r: destroys["des_8"](s, d, r),
        "des_9": lambda s, d, q, r: destroys["des_9"](s, d, q, r),
    }
    
    repair_wrappers = {
        "rep_1": lambda s, d, p, r: repairs["rep_1"](s, d, p, r),
        "rep_2": lambda s, d, p, r: repairs["rep_2"](s, d, p, r, eps),
        "rep_4": lambda s, d, p, r: repairs["rep_4"](s, d, p, r, eps),
        "rep_5": lambda s, d, p, r: repairs["rep_5"](s, d, p, r, eps),
        "rep_6": lambda s, d, p, r: repairs["rep_6"](s, d, p, r, eps, k_regret),
        "rep_7": lambda s, d, p, r: repairs["rep_7"](s, d, r),
        "rep_8": lambda s, d, p, r: repairs["rep_8"](s, d, r),
        "rep_9": lambda s, d, p, r: repairs["rep_9"](s, d, p, r, eps),
    }
    
    destroy_names = [name for name in destroy_wrappers if name in destroys]
    repair_names = [name for name in repair_wrappers if name in repairs]
    
    if not destroy_names or not repair_names:
        raise ValueError("At least one destroy and one repair operator are required.")

    phi_des = {name: 0 for name in destroy_names}
    phi_rep = {name: 0 for name in repair_names}
    compute_operator_probs(phi_des, epsilon)
    compute_operator_probs(phi_rep, epsilon)

    initial_sol = initial_solution(data, seed=seed)
    initial_sol, _ = repairs["rep_3"](initial_sol, data)
    
    if not is_feasible(data, initial_sol):
        raise ValueError("Initial solution is infeasible.")
        
    initial_obj_result = calculate_objective(initial_sol, data)
    initial_obj = float(initial_obj_result[0])
    
    if not math.isfinite(initial_obj):
        raise ValueError("Initial objective must be finite.")

    current_sol = copy.deepcopy(initial_sol)
    current_obj = initial_obj
    best_sol = copy.deepcopy(initial_sol)
    best_obj = initial_obj
    best_obj_result = initial_obj_result
    
    destroy_select_count = Counter()
    repair_select_count = Counter()
    destroy_accepted_count = Counter()
    repair_accepted_count = Counter()
    history_best = [best_obj]
    history_current = [current_obj]
    history_temp = [T_start]
    history_q = [q_max]
    no_improve_count = 0
    it = 0

    if verbose:
        print(f"Initial objective: {initial_obj:.4f}")
        print(f"T_start: {T_start:.4f}, T_end: {T_end:.4f}")

    while it < max_iter:
        if time_limit is not None and time.monotonic() - start_time >= time_limit:
            if verbose:
                print(f"[Time limit] Stopping at iteration {it}.")
            break

        T = max(T_end, T_start * cooling_rate ** it)
        # Retain the original three-cycle cosine destruction schedule.
        phase = it / max(max_iter - 1, 1) * math.pi * 6
        q_used = q_min + 0.5 * (q_max - q_min) * (1 + math.cos(phase))
        q_used = max(q_min, min(q_max, q_used))
        
        if no_improve_count >= stagnation_limit:
            current_sol = copy.deepcopy(best_sol)
            current_obj = best_obj
            no_improve_count = 0
            # Retain the original one-iteration temperature boost.
            T = max(T, 0.30 * T_start)
            if verbose:
                print(f"[Restart] iter {it + 1}: reset to best, T={T:.3f}.")

        w_des = compute_operator_probs(phi_des, epsilon)
        w_rep = compute_operator_probs(phi_rep, epsilon)
        d_name = weighted_pick(destroy_names, w_des, rng)
        r_name = weighted_pick(repair_names, w_rep, rng)
        destroy_select_count[d_name] += 1
        repair_select_count[r_name] += 1

        destroyed_sol, _ = destroy_wrappers[d_name](current_sol, data, q_used, rng)
        candidate_sol, _ = repair_wrappers[r_name](destroyed_sol, data, p_insert, rng)
        candidate_sol, _ = repairs["rep_3"](candidate_sol, data)
        
        accepted = False
        candidate_obj = None
        candidate_changed = candidate_sol != current_sol
        new_best = False

        if is_feasible(data, candidate_sol):
            candidate_obj_result = calculate_objective(candidate_sol, data)
            candidate_obj = float(candidate_obj_result[0])
            if not math.isfinite(candidate_obj):
                raise ValueError(f"Nonfinite candidate objective at iteration {it + 1}.")

            delta = candidate_obj - current_obj
            
            if candidate_changed:
                accepted = delta <= 0 or rng.random() < math.exp(-delta / T)

            if accepted:
                # Credit both operators for the accepted combined move.
                phi_des[d_name] += 1
                phi_rep[r_name] += 1
                destroy_accepted_count[d_name] += 1
                repair_accepted_count[r_name] += 1
                current_sol = copy.deepcopy(candidate_sol)
                current_obj = candidate_obj

                if candidate_obj < best_obj:
                    best_sol = copy.deepcopy(candidate_sol)
                    best_obj = candidate_obj
                    best_obj_result = candidate_obj_result
                    new_best = True
                    if verbose:
                        print(
                            f"Iter {it + 1:5d} | New best={best_obj:.4f} "
                            f"| d={d_name}, r={r_name}, q={q_used:.3f}, T={T:.3f}"
                        )

        no_improve_count = 0 if new_best else no_improve_count + 1
        it += 1

        if it % G_reset == 0:
            phi_des = {name: 0 for name in destroy_names}
            phi_rep = {name: 0 for name in repair_names}
            if verbose:
                print(f"[AOS reset] iter {it}: all operator scores reset to zero.")

        history_best.append(best_obj)
        history_current.append(current_obj)
        history_temp.append(T)
        history_q.append(q_used)

        if verbose and (it == 1 or it % 50 == 0 or it == max_iter):
            candidate_text = "infeasible" if candidate_obj is None else f"{candidate_obj:.4f}"
            print(
                f"Iter {it:5d} | des={d_name}, rep={r_name} "
                f"| cur={current_obj:.4f}, cand={candidate_text}, best={best_obj:.4f} "
                f"| T={T:.4f}, q={q_used:.3f}, accepted={accepted}"
            )

    runtime = time.monotonic() - start_time
    w_des = compute_operator_probs(phi_des, epsilon)
    w_rep = compute_operator_probs(phi_rep, epsilon)
    
    if verbose:
        print(f"Best objective: {best_obj:.4f}")
        print(f"Runtime: {runtime:.2f}s; iterations: {it}")
        for label, names, selected, accepted_counts in (
            ("Destroy", destroy_names, destroy_select_count, destroy_accepted_count),
            ("Repair", repair_names, repair_select_count, repair_accepted_count),
        ):
            print(f"{label} operator usage:")
            for name in names:
                uses = selected[name]
                accepts = accepted_counts[name]
                rate = 100 * accepts / uses if uses else 0.0
                print(f"  {name}: selected={uses}, accepted={accepts}, rate={rate:.1f}%")

    if plot:
        plt.figure(figsize=(8, 5))
        plt.plot(history_best, label="Best Objective", linewidth=2, color="red")
        plt.plot(history_current, label="Current Objective", color="skyblue")
        plt.xlabel("Iteration")
        plt.ylabel("Objective Value")
        plt.title(f"ALNS Convergence (seed={seed})")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.show()

    (
        best_objective, best_production_cost, best_lateness_cost,
        best_rejection_cost, best_unused_capacity_cost,
        best_job_completion_time, best_batch_completion_time,
        best_batch_processing_time, best_batch_weight, best_batch_volume,
        best_batch_height, best_batch_unused_capacity,
        best_job_tardiness, best_total_rejected_jobs, best_acceptance_rate,
    ) = best_obj_result
    
    
    return {
        "best_solution": best_sol,
        "best_objective": best_objective,
        "initial_solution": initial_sol,
        "initial_objective": initial_obj,
        "current_solution": current_sol,
        "current_objective": current_obj,
        "best_production_cost": best_production_cost,
        "best_lateness_cost": best_lateness_cost,
        "best_rejection_cost": best_rejection_cost,
        "best_unused_capacity_cost": best_unused_capacity_cost,
        "best_total_rejected_jobs": best_total_rejected_jobs,
        "best_acceptance_rate": best_acceptance_rate,
        "best_job_completion_time": best_job_completion_time,
        "best_job_tardiness": best_job_tardiness,
        "best_batch_completion_time": best_batch_completion_time,
        "best_batch_processing_time": best_batch_processing_time,
        "best_batch_weight": best_batch_weight,
        "best_batch_volume": best_batch_volume,
        "best_batch_height": best_batch_height,
        "best_batch_unused_capacity": best_batch_unused_capacity,
        # Retain existing result keys; these now contain selection probabilities.
        "destroy_weights": w_des,
        "repair_weights": w_rep,
        "destroy_scores": phi_des,
        "repair_scores": phi_rep,
        "history_best": history_best,
        "history_current": history_current,
        "history_temp": history_temp,
        "history_q": history_q,
        "destroy_select_count": destroy_select_count,
        "repair_select_count": repair_select_count,
        "destroy_accepted_count": destroy_accepted_count,
        "repair_accepted_count": repair_accepted_count,
        "runtime_seconds": runtime,
        "iterations_run": it,
        "seed": seed,
    }
    
    
    
    
    
        
         
        
  
