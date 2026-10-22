#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 23 21:55:48 2025

@author: parisa
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import os


# ----------------------------
# Parameters (factors)
parameters = [
    "Due Date",
    "Rejection Cost",
    "Batch Underutilization Cost",
    "Tardiness Cost",
    "Flow-time Cost",
    "Material Inventory",
]



kpi_names = [
    "Total Cost",
    "Number of Batches",
    "Acceptance Rate (%)",
    "Average Batch Utilization (%)",
    "Average Tardiness",
    "Average Completion Time",
]



# Decrease table (rows = KPIs, cols = parameters) — numeric percent values
small_decrease = pd.DataFrame(
    data=[
        [4, -17, 21, 0, -22, 36],       # Changes in total cost
        [-3, -62, 3, 0, 0, -14],        # avg number of batches
        [-3, -54, 1, 0,	0, -40],   # Acceptance Rate (%)
        [-2,	34,	-6,	0,	1,	-47],        # avg batch utilization
        [1144,	-97,	0,	0,	0,	-100], # avg tardiness
        [-4,	-11,	-1,	0,	1,	-34],     # avg completion time
    ],
    index=kpi_names,
    columns=parameters,
)

# Increase table (rows = KPIs, cols = parameters)
small_increase = pd.DataFrame(
    data=[
        [0,	6,	19,	0,	21,	-6],
        [0,	3,	-10,	0,	-3,	3],
        [0,	1,	-5,	0,	-4,	8],
        [0,	-3,	7,	0,	-5,	5],
        [-100,	0,	5,	0,	-74,	64],
        [0,	-1,	1,	0,	-7,	5],
    ],
    index=kpi_names,
    columns=parameters,
)


large_decrease = pd.DataFrame(
    data=[
        [17,	-11,	-10,	-2,	-35,	48],       # Changes in total cost
        [13,	-23,	25,	0,	-9,	-23],        # avg number of batches
        [0,	-18,	0,	0,	0,	-35],   # Acceptance Rate (%)
        [-13,	0,	-21,	-1,	10,	-33],        # avg batch utilization
        [466,	-89,	-15,	6,	18,	-90], # avg tardiness
        [-5,	-15,	-7,	0,	4,	-26],     # avg completion time
    ],
    index=kpi_names,
    columns=parameters,
)




# Increase table (rows = KPIs, cols = parameters)
large_increase = pd.DataFrame(
    data=[
        [-4,	6,	7,	2,	33, -4],
        [-5,	4,	-11,	6,	6,	6],
        [0,	0,	-1,	0,	-3,	5],
        [4,	-4,	11,	-6,	-11,	1],
        [-93,	0,	15,	-11,	-29,	26,],
        [1,	-2,	3,	-2,	-7,	3,],
    ],
    index=kpi_names,
    columns=parameters,
)



# ----------------------------
sensitivity_small = {param: {} for param in parameters}
sensitivity_large = {param: {} for param in parameters}

for param in parameters:
    for kpi in kpi_names:
        dec_val = small_decrease.loc[kpi, param]
        inc_val = small_increase.loc[kpi, param]
        sensitivity_small[param][kpi] = {"Decrease Impact (%)": dec_val, "Increase Impact (%)": inc_val}

        dec_val_L = large_decrease.loc[kpi, param]
        inc_val_L = large_increase.loc[kpi, param]
        sensitivity_large[param][kpi] = {"Decrease Impact (%)": dec_val_L, "Increase Impact (%)": inc_val_L}



# ----------------------------
def sens_dict_to_df(sens_dict):
    rows = []
    idx = []
    for param, kpi_map in sens_dict.items():
        for kpi, vals in kpi_map.items():
            idx.append((param, kpi))
            rows.append(vals)
    df = pd.DataFrame(rows, index=pd.MultiIndex.from_tuples(idx, names=["Parameter", "KPI"]))
    return df

sensitivity_small_df = sens_dict_to_df(sensitivity_small)
sensitivity_large_df = sens_dict_to_df(sensitivity_large)



def plot_tornado_chart(kpi, sensitivity_data, figsize=(8, 6), savepath=None):
    params = list(sensitivity_data.keys())
    decrease_impacts = [sensitivity_data[p][kpi]["Decrease Impact (%)"] for p in params]
    increase_impacts = [sensitivity_data[p][kpi]["Increase Impact (%)"] for p in params]
    y_pos = np.arange(len(params))

    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    bar_height = 0.4
    
    # Symmetric x-limits
    all_vals = np.array(decrease_impacts + increase_impacts, dtype=float)
    max_abs = max(np.nanmax(np.abs(all_vals)), 1.0)
    lim = max_abs * (1.08 if max_abs <= 500 else 1.02)
    ax.set_xlim(-lim, lim)
    
    
    
    for yi, (d, inc) in enumerate(zip(decrease_impacts, increase_impacts)):
        # Choose drawing order for same-sign bars
        same_sign = (np.sign(d) == np.sign(inc)) and (d != 0) and (inc != 0)
        
        
        if same_sign:
            # Determine which is longer in magnitude
            first_val, first_color = (d, "orange") if abs(d) >= abs(inc) else (inc, "green")
            second_val, second_color = (inc, "green") if abs(d) >= abs(inc) else (d, "orange")

            # Draw longer under, shorter on top (both full opacity)
            ax.barh(yi, first_val, height=bar_height, color=first_color,
                    edgecolor="black", linewidth=0.3, zorder=1)
            ax.barh(yi, second_val, height=bar_height, color=second_color,
                    edgecolor="black", linewidth=0.3, zorder=2)
        else:
            # Different sides of zero — no overlap issue
            ax.barh(yi, d,   height=bar_height, color="orange",
                    edgecolor="black", linewidth=0.3, zorder=2)
            ax.barh(yi, inc, height=bar_height, color="green",
                    edgecolor="black", linewidth=0.3, zorder=2)
            
            
 
    ax.set_yticks(y_pos)
    ax.set_yticklabels(params, fontsize=11)
    ax.set_xlabel("Impact (%)", fontsize=12)
   
    ax.invert_yaxis()

    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor="orange", edgecolor="black", label="-50% Change"),
        Patch(facecolor="green",  edgecolor="black", label="+50% Change"),
    ]
    ax.legend(handles=legend_handles, fontsize=11)
    
    
    
    plt.tight_layout()
    if savepath:
        os.makedirs(os.path.dirname(savepath) or ".", exist_ok=True)
        fig.savefig(savepath, dpi=600, bbox_inches='tight')
        base, _ = os.path.splitext(savepath)
        fig.savefig(base + ".pdf", bbox_inches='tight')

    plt.show()
    plt.close(fig)
    
  
    
# ----------------------------
# Generate tornado charts for small and large 
# ----------------------------
for kpi in kpi_names:
    # small
    plot_tornado_chart(kpi, {param: sensitivity_small[param] for param in parameters}, figsize=(8, 6))
    # large
    plot_tornado_chart(kpi, {param: sensitivity_large[param] for param in parameters}, figsize=(8, 6))


