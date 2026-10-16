#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 11:32:21 2026

@author: parisa
"""

def compute_apriori_relatedness(data, eps=1e-12):
    """
    Compute static/a priori relatedness scores between pairs of jobs.

    This relatedness does not depend on the current solution.
    It uses only problem data:
        - same material
        - similar due date
        - similar ready/release time

    Returns
    -------
    apriori_scores : dict
        apriori_scores[(j1, j2)] = relatedness score
    """

    J = data['J']
    job_material = data['job_material']
    d_j = data['d_j']
    r_j = data['r_j']
    
    # Normalization for due dates
    due_vals = [float(d_j[j]) for j in J]
    due_range = max(due_vals) - min(due_vals)
    if due_range <= eps:
        due_range = 1.0

    # Normalization for ready/release times
    ready_vals = [float(r_j[j]) for j in J]
    ready_range = max(ready_vals) - min(ready_vals)
    if ready_range <= eps:
        ready_range = 1.0


    # Weights
    w_material = 4.0
    w_due = 2.0
    w_ready = 2.0
   
    
    apriori_scores = {}

    for j1 in J:
        for j2 in J:
            if j1 == j2:
                continue

            same_material = (
                1.0 if job_material[j1] == job_material[j2]
                else 0.0
            )

            due_similarity = max(
                0.0,
                1.0 - abs(float(d_j[j1]) - float(d_j[j2])) / due_range
            )

            ready_similarity = max(
                0.0,
                1.0 - abs(float(r_j[j1]) - float(r_j[j2])) / ready_range
            )


            score = (
                w_material * same_material
                + w_due * due_similarity
                + w_ready * ready_similarity
            )

            apriori_scores[(j1, j2)] = score

    return apriori_scores
    
    
    