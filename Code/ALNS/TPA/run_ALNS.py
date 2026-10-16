#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 11 13:21:26 2026

@author: parisa
"""

from ALNS import run_alns, is_feasible
from read_data import generate_data
from export_ALNS_results import export_ALNS_results


if __name__ == "__main__":

    FILE_NAME = "TPA37.xlsx"
    
    data = generate_data(FILE_NAME)
    
  
    seeds = [10]
    
    
    time_limits = [10]
    
    
    
    if len(seeds) != len(time_limits):
        raise ValueError("Each seed must have one corresponding time limit.")

    for seed, time_limit in zip(seeds, time_limits):
        print(f'\n{"=" * 60}')
        print(f"Seed: {seed} | Time limit: {time_limit} seconds")

        r = run_alns(
            data,
            seed=seed,
            verbose=True,
            plot=True,
            time_limit=time_limit,
        )

        best_solution = r["best_solution"]

        if is_feasible(data, best_solution):
            print("Best solution is feasible.")
        else:
            raise ValueError(f"Best solution is infeasible for seed {seed}.")

        print(
            f'\nSeed {seed} | Initial: {r["initial_objective"]:.4f} '
            f'| Best: {r["best_objective"]:.4f} '
            f'| Cost reduction: '
            f'{r["initial_objective"] - r["best_objective"]:.4f}'
        )
        
        
        export_ALNS_results(
            seed=r["seed"],
            running_time=r["runtime_seconds"],
            initial_solution=r["initial_solution"],
            initial_objective=r["initial_objective"],
            best_solution=r["best_solution"],
            best_objective=r["best_objective"],
            best_production_cost=r["best_production_cost"],
            best_lateness_cost=r["best_lateness_cost"],
            best_rejection_cost=r["best_rejection_cost"],
            best_unused_capacity_cost=r["best_unused_capacity_cost"],
            best_job_completion_time=r["best_job_completion_time"],
            best_batch_completion_time=r["best_batch_completion_time"],
            best_batch_processing_time=r["best_batch_processing_time"],
            best_batch_weight=r["best_batch_weight"],
            best_batch_volume=r["best_batch_volume"],
            best_batch_height=r["best_batch_height"],
            best_batch_unused_capacity=r["best_batch_unused_capacity"],
            best_job_tardiness=r["best_job_tardiness"],
            history_best=r["history_best"],
            history_current=r["history_current"],
            history_temp=r["history_temp"],
            history_q=r["history_q"],
            destroy_select_count=r["destroy_select_count"],
            repair_select_count=r["repair_select_count"],
            destroy_accepted_count=r["destroy_accepted_count"],
            repair_accepted_count=r["repair_accepted_count"],
            destroy_weights=r["destroy_weights"],
            repair_weights=r["repair_weights"],
            filename=f"ALNS_TPA{seed}.xlsx",
        )
        
        
        

    



         
         
