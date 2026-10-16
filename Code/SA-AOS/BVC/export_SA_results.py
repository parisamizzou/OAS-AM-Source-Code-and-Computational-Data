#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  6 14:09:07 2024

@author: parisa
"""



from io import BytesIO

import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.drawing.image import Image


def export_SA_results(
    seed,
    running_time,
    initial_solution,
    initial_objective,
    graph_obj,
    graph_temp,
    best_solution,
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
    filename="SA_results.xlsx"):
    
    # Identify accepted jobs and active batches
    total_rejected_jobs = 0
    active_batches = set()

    for job, assignment in best_solution.items():
        batch, machine = assignment

        if batch is None and machine is None:
            total_rejected_jobs += 1
        elif batch is None or machine is None:
            raise ValueError(
                f"Job {job} has an incomplete assignment.")
        else:
            active_batches.add((machine, batch))

    active_batches = sorted(active_batches)

    total_jobs = len(best_solution)
    total_accepted_jobs = total_jobs - total_rejected_jobs
    
    acceptance_rate = (
        100 * total_accepted_jobs / total_jobs
        if total_jobs > 0
        else 0.0)

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:

        # Seed and runtime
        pd.DataFrame([{"Seed": seed}]).to_excel(writer, sheet_name="Seed", index=False)

        # Initial solution and objective
        initial_solution_df = pd.DataFrame.from_dict(initial_solution, orient="index", columns=["Batch", "Machine"])
        initial_solution_df.index.name = "Job"
        initial_solution_df.to_excel(writer, sheet_name="Initial_Solution", index=True)
        
        # Export initial objective
        pd.DataFrame([{"Initial Objective": initial_objective}]).to_excel(writer, sheet_name="Initial_Objective", index=False)

        # Best solution and objective
        best_solution_df = pd.DataFrame.from_dict(
            best_solution,
            orient="index",
            columns=["Batch", "Machine"])
        
        best_solution_df.index.name = "Job"
        best_solution_df.to_excel(writer, sheet_name="Best_Solution", index=True)

        # Export best objective
        pd.DataFrame([{"Best Objective": best_objective}]).to_excel(writer, sheet_name="Best_Objective", index=False)
    
        # Objective components
        pd.DataFrame([{"Best Production Cost": best_production_cost}]).to_excel(writer, sheet_name="Best_Production_Cost", index=False)

        pd.DataFrame(
            [{"Best Lateness Cost": best_lateness_cost}]
        ).to_excel(
            writer, sheet_name="Best_Lateness_Cost", index=False)

        pd.DataFrame(
            [{"Best Rejection Cost": best_rejection_cost}]
        ).to_excel(
            writer, sheet_name="Best_Rejection_Cost", index=False)

        pd.DataFrame(
            [{"Best Unused Capacity Cost": best_unused_capacity_cost}]
        ).to_excel(
            writer,
            sheet_name="Best_Unused_Capacity_Cost",
            index=False)
            
        # Rejection count and acceptance rate
        pd.DataFrame(
            [{"Total Rejected Jobs": total_rejected_jobs}]
        ).to_excel(
            writer, sheet_name="Total_Rejected_Jobs", index=False)

        # Stored as 0–100, consistent with calculate_objective
        pd.DataFrame(
            [{"Acceptance Rate (%)": acceptance_rate}]
        ).to_excel(
            writer, sheet_name="Acceptance_Rate", index=False)

        # Job completion times
        job_completion_df = pd.DataFrame.from_dict(
            best_job_completion_time,
            orient="index",
            columns=["Completion Time"])
        
        job_completion_df.index.name = "Job"
        job_completion_df.to_excel(writer, sheet_name="Best_Job_Completion_Time", index=True)
        
        # Job tardiness
        job_tardiness_df = pd.DataFrame.from_dict(
            best_job_tardiness,
            orient="index",
            columns=["Tardiness"]
        )
        job_tardiness_df.index.name = "Job"
        job_tardiness_df.to_excel(
            writer, sheet_name="Best_Job_Tardiness", index=True
        )

        # Batch completion times
        batch_completion_data = []
        for machine, batch in active_batches:
            batch_completion_data.append({
                "Machine": machine,
                "Batch": batch,
                "Completion Time":
                    best_batch_completion_time[machine][batch - 1]
            })

        pd.DataFrame(
            batch_completion_data,
            columns=["Machine", "Batch", "Completion Time"]
        ).to_excel(
            writer, sheet_name="Best_Batch_Completion_Time", index=False
        )

        # Batch processing times
        batch_processing_data = []
        for machine, batch in active_batches:
            batch_processing_data.append({
                "Machine": machine,
                "Batch": batch,
                "Processing Time":
                    best_batch_processing_time[machine][batch - 1]
            })

        pd.DataFrame(
            batch_processing_data,
            columns=["Machine", "Batch", "Processing Time"]
        ).to_excel(
            writer, sheet_name="Best_Batch_Processing_Time", index=False
        )

        # Batch raw-material requirements
        batch_weight_data = []
        for machine, batch in active_batches:
            batch_weight_data.append({
                "Machine": machine,
                "Batch": batch,
                "Weight": best_batch_weight[machine][batch - 1]
            })

        pd.DataFrame(
            batch_weight_data,
            columns=["Machine", "Batch", "Weight"]
        ).to_excel(
            writer, sheet_name="Best_Batch_Weight", index=False
        )

        # Batch actual part volumes
        batch_volume_data = []
        for machine, batch in active_batches:
            batch_volume_data.append({
                "Machine": machine,
                "Batch": batch,
                "volume": best_batch_volume[machine][batch - 1]
            })

        pd.DataFrame(
            batch_volume_data,
            columns=["Machine", "Batch", "volume"]
        ).to_excel(
            writer, sheet_name="Best_Batch_Volume", index=False
        )

        # Batch heights
        batch_height_data = []
        for machine, batch in active_batches:
            batch_height_data.append({
                "Machine": machine,
                "Batch": batch,
                "height": best_batch_height[machine][batch - 1]
            })

        pd.DataFrame(
            batch_height_data,
            columns=["Machine", "Batch", "height"]
        ).to_excel(
            writer, sheet_name="Best_Batch_Height", index=False
        )

        # Unused-capacity fractions, including zero for full batches
        batch_unused_capacity_data = []
        for machine, batch in active_batches:
            batch_unused_capacity_data.append({
                "Machine": machine,
                "Batch": batch,
                "Unused Capacity Fraction":
                    best_batch_unused_capacity[machine][batch - 1]
            })

        pd.DataFrame(
            batch_unused_capacity_data,
            columns=["Machine", "Batch", "Unused Capacity Fraction"]
        ).to_excel(
            writer, sheet_name="Best_Batch_Unused_Capacity", index=False
        )

        # Batch utilization percentages for active batches only
        batch_utilization_data = []
        for machine, batch in active_batches:
            unused_fraction = (
                best_batch_unused_capacity[machine][batch - 1]
            )

            batch_utilization_data.append({
                "Machine": machine,
                "Batch": batch,
                "Batch Utilization (%)": 100 * (1 - unused_fraction)
            })

        pd.DataFrame(
            batch_utilization_data,
            columns=["Machine", "Batch", "Batch Utilization (%)"]
        ).to_excel(
            writer, sheet_name="Best_Batch_Utilization", index=False
        )

        # Convergence data
        pd.DataFrame(
            graph_obj, columns=["Objective Value"]
        ).to_excel(
            writer,
            sheet_name="Graph_Objective",
            index=True,
            index_label="Iteration"
        )

        pd.DataFrame(
            graph_temp, columns=["Temperature"]
        ).to_excel(
            writer,
            sheet_name="Graph_Temperature",
            index=True,
            index_label="Iteration"
        )

    # Insert plots using in-memory images
    book = load_workbook(filename)
    
    with BytesIO() as objective_image, BytesIO() as temperature_image:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(graph_obj, label="Objective Value")
        ax.set_xlabel("Iterations")
        ax.set_ylabel("Objective Value")
        ax.set_title("Objective Value over Iterations")
        ax.legend()
        fig.tight_layout()
        fig.savefig(objective_image, format="png", dpi=100)
        plt.close(fig)
        objective_image.seek(0)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(graph_temp, label="Temperature", color="orange")
        ax.set_xlabel("Iterations")
        ax.set_ylabel("Temperature")
        ax.set_title("Temperature over Iterations")
        ax.legend()
        fig.tight_layout()
        fig.savefig(temperature_image, format="png", dpi=100)
        plt.close(fig)
        temperature_image.seek(0)

        sheet_obj = book.create_sheet("Graph_Images")
        sheet_obj.add_image(Image(objective_image), "A1")
        sheet_obj.add_image(Image(temperature_image), "A24")

        book.save(filename)

    book.close()

    print(f"Simulated Annealing results successfully exported to {filename}")

    
    
    
    