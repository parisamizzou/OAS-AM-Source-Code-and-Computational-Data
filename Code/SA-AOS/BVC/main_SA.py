#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 20:05:58 2024

@author: parisa
"""


import copy
import math
import random
import time

import numpy as np

from initial_solution import initial_solution
from generate_data import generate_data
from calculate_objective import calculate_objective
from generate_neighbor import generate_neighbor
from export_SA_results import export_SA_results


def compute_operator_probs(phi, total_operators, epsilon):
    if total_operators < 1:
        raise ValueError("total_operators must be positive.")

    if not 0 < epsilon < 1.0 / total_operators:
        raise ValueError("epsilon must satisfy 0 < epsilon < 1/total_operators.")
           

    operator_ids = list(range(1, total_operators + 1))

    if any(
        not math.isfinite(phi[operator_id])
        or phi[operator_id] < 0
        for operator_id in operator_ids):
        raise ValueError( "Operator scores must be finite and nonnegative.")
          

    phi_sum = sum(phi[operator_id] for operator_id in operator_ids)
    

    if phi_sum == 0:
        return {
            operator_id: 1.0 / total_operators
            for operator_id in operator_ids}

    weights = {
        operator_id:
            epsilon + (1 - total_operators * epsilon) * phi[operator_id]/ phi_sum
        for operator_id in operator_ids}

    weight_sum = sum(weights.values())
    
    return {
        operator_id:
            weights[operator_id] / weight_sum
        for operator_id in operator_ids}





def run_sa(data, seed, output_filename):
    # SA parameters
    Tmin = 1
    Tmax = 1000
    cooling_rate = 0.995
    max_iterations = 400
    epsilon = 0.02
    G_reset = 20
    total_operators = 13


    
    max_no_improvement = max(
    50 * int(data['n']),
    10 * max_iterations,
)

    if not 0 < Tmin < Tmax:
        raise ValueError("Temperatures must satisfy 0 < Tmin < Tmax.")
        

    if not 0 < cooling_rate < 1:
        raise ValueError("cooling_rate must be between 0 and 1.")
       

    if (
        max_iterations < 1
        or max_no_improvement < 1
        or G_reset < 1
    ):
        raise ValueError("Iteration, stopping, and reset limits must be positive.")
        

    if not 0 < epsilon < 1.0 / total_operators:
        raise ValueError("epsilon must satisfy 0 < epsilon < 1/total_operators.")
       

    # Seed both generators once per SA run.
    random.seed(seed)
    np.random.seed(seed)

    phi = {
        operator_id: 0
        for operator_id in range(
            1,
            total_operators + 1,
        )
    }

    initial_sol = initial_solution(data, seed)
    initial_values = calculate_objective(initial_sol, data)

   

    if len(initial_values) != 15:
        raise ValueError( "calculate_objective must return 15 values.")
         
    initial_objective = initial_values[0]

    current_solution = copy.deepcopy(initial_sol)
    current_values = copy.deepcopy(initial_values)
    current_objective = initial_objective

    best_solution = copy.deepcopy(initial_sol)
    best_values = copy.deepcopy(initial_values)
    best_objective = initial_objective

    current_temperature = Tmax
    no_improvement_count = 0
    total_iterations = 0
    temp_reduction_count = 0
    
    # Include the initial state at index zero.
    graph_obj = [current_objective]
    graph_temp = [current_temperature]
    
    no_neighbor_count = 0
    accepted_move_count = 0
    accepted_worse_count = 0
    best_improvement_count = 0
    
    print("Initial Solution (job: [batch, machine]):")
    print(initial_sol)
    print("Initial objective:", initial_objective)

    start_time = time.perf_counter()

    while (
        current_temperature > Tmin
        and no_improvement_count < max_no_improvement):
        iteration = 0

        while iteration < max_iterations:
          
            iteration += 1
            total_iterations += 1

            operator_probs = compute_operator_probs(
                phi,
                total_operators,
                epsilon,
            )

            neighbor_data = generate_neighbor(
                current_solution,
                current_objective,
                total_iterations,
                data,
                operator_probs,
            )

            best_was_improved = False
            
            if neighbor_data is None:
                no_neighbor_count += 1
            else:
                if len(neighbor_data) != 17:
                    raise ValueError(
                        "generate_neighbor must return 17 values or None."
                    )

                neighboring_solution = neighbor_data[0]
                neighboring_objective = neighbor_data[1]
                neighboring_operator = int(neighbor_data[14])
                
                if not 1 <= neighboring_operator <= total_operators:
                    raise ValueError(
                        "generate_neighbor returned an invalid operator ID."
                    )

                neighboring_values = (
                    tuple(neighbor_data[1:14])
                    + tuple(neighbor_data[15:17])
                )
              
    

                cost_increase = (
                    neighboring_objective - current_objective
                )

                if cost_increase <= 0:
                    accepted = True
                else:
                    acceptance_probability = math.exp(
                        -cost_increase
                        / max(current_temperature, 1e-12)
                    )
                    accepted = (
                        random.random() < acceptance_probability
                    )
                
                if accepted:
                    current_solution = copy.deepcopy(
                        neighboring_solution
                    )
                    current_values = copy.deepcopy(
                        neighboring_values
                    )
                    current_objective = neighboring_objective

                    phi[neighboring_operator] += 1
                    accepted_move_count += 1

                    if cost_increase > 0:
                        accepted_worse_count += 1

                    if current_objective < best_objective:
                        best_solution = copy.deepcopy(
                            current_solution
                        )
                        best_values = copy.deepcopy(current_values)
                        best_objective = current_objective
                        best_was_improved = True
                        best_improvement_count += 1

            if best_was_improved:
                no_improvement_count = 0
            else:
                no_improvement_count += 1

            graph_obj.append(current_objective)
            graph_temp.append(current_temperature)

        current_temperature *= cooling_rate
        temp_reduction_count += 1
        
        if temp_reduction_count % G_reset == 0:
            phi = {
                operator_id: 0
                for operator_id in range(1, total_operators + 1)
            }

        print(
            f"Trials: {total_iterations}, "
            f"Current objective: {current_objective:.6f}, "
            f"Best objective: {best_objective:.6f}, "
            "Trials without best improvement: "
            f"{no_improvement_count}"
        )

    running_time = time.perf_counter() - start_time

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

    print("Seed:", seed)
    print("Best Solution (job: [batch, machine]):")
    print(best_solution)
    print("Total cost:", best_objective)
    print("Production cost:", best_production_cost)
    print("Lateness cost:", best_lateness_cost)
    print("Rejection cost:", best_rejection_cost)
    print("Unused-capacity cost:", best_unused_capacity_cost)
    print("Rejected jobs:", best_total_rejected_jobs)
    print(f"Acceptance rate: {best_acceptance_rate:.2f}%")
    print("Accepted moves:", accepted_move_count)
    print("Accepted worse moves:", accepted_worse_count)
    print("Best-solution improvements:", best_improvement_count)
    print(
        "Trials with no changed feasible neighbor:",
        no_neighbor_count,
    )
    print(f"Search running time: {running_time:.2f} seconds")

    export_SA_results(
        seed=seed,
        running_time=running_time,
        initial_solution=initial_sol,
        initial_objective=initial_objective,
        graph_obj=graph_obj,
        graph_temp=graph_temp,
        best_solution=best_solution,
        best_objective=best_objective,
        best_production_cost=best_production_cost,
        best_lateness_cost=best_lateness_cost,
        best_rejection_cost=best_rejection_cost,
        best_unused_capacity_cost=best_unused_capacity_cost,
        best_job_completion_time=best_job_completion_time,
        best_batch_completion_time=best_batch_completion_time,
        best_batch_processing_time=best_batch_processing_time,
        best_batch_weight=best_batch_weight,
        best_batch_volume=best_batch_volume,
        best_batch_height=best_batch_height,
        best_batch_unused_capacity=best_batch_unused_capacity,
        best_job_tardiness=best_job_tardiness,
        filename=output_filename,
    )

    return {
        'seed': seed,
        'total_iterations': total_iterations,
        'temperature_reductions': temp_reduction_count,
        'initial_solution': initial_sol,
        'initial_objective': initial_objective,
        'best_solution': best_solution,
        'best_values': best_values,
        'best_total_rejected_jobs': best_total_rejected_jobs,
        'best_acceptance_rate': best_acceptance_rate,
    }


def main():
    file_name = 'results118.xlsx'
    data = generate_data(file_name)

    # Use fixed seeds for reproducible experiments. Add more seeds as needed.
    seeds = [131]
    #seeds = random.sample(range(1, 1000), 2)

    results = []

    for seed in seeds:
        result = run_sa(
            data=data,
            seed=seed,
            output_filename=f'SA_results{seed}.xlsx',
        )
        results.append(result)

    return results


if __name__ == '__main__':
    main()
                
                
                


        
        