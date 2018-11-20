# Import Python wrapper for or-tools constraint solver.
import datetime

import numpy as np
import pandas as pd
import plotly.figure_factory as ff
from ortools.constraint_solver import pywrapcp
from plotly.offline import plot

'''
Job Shop example from 
https://developers.google.com/optimization/scheduling/job_shop
with gantt chart
'''


def get_start_time(current, interval):
    dt = current + np.timedelta64(interval, 'h')
    dt = np.datetime64(np.datetime_as_string(dt)[:16])
    dt = str(dt)
    lst = list(dt)
    # Modifies string format
    lst[lst.index('T')] = ' '
    dt = "".join(lst)
    return dt


# Gets the finish time giving start time and duration (in minutes), returns finish time as string
def get_finish_time(current, interval):
    dt = current + np.timedelta64(interval, 'h')
    dt = np.datetime64(np.datetime_as_string(dt)[:16])
    dt = str(dt)
    lst = list(dt)
    # Modifies string format
    lst[lst.index('T')] = ' '
    dt = "".join(lst)
    return dt


def get_machine_type(i):
    machine_dict = {0: 'Extruder', 1: 'Printer', 2: 'Laminator', 3: 'Cutter'}
    return machine_dict.get(i)


# Creates html file of plotly gantt chart
def chart(df, filename):
    fig = ff.create_gantt(df, index_col='Resource', show_colorbar=True, group_tasks=True)
    plot(fig, filename=filename, output_type='div')
    print(fig)


# Solves the job shop problem using OR-tools constraint solver, returns a dictionary with the solution
def schedule(df, filename):
    # Create the solver.
    solver = pywrapcp.Solver('jobshop')

    machines_count = 4  # Extrude, Print, (Laminate), Cut
    jobs_count = len(df.index)
    all_machines = range(0, machines_count)
    all_jobs = range(0, jobs_count)

    # Define data.
    machines = []
    for i in range(0, len(df.index)):
        # Include Printing and Laminating machine
        if df.ix[i]['printed'] == 1 and df.ix[i]['laminate'] == 1:
            machines.append([0, 1, 2, 3])
        # Include only Printing
        elif df.ix[i]['printed'] == 1:
            machines.append([0, 1, 3])
        # Include only Laminating
        elif df.ix[i]['laminate'] == 1:
            machines.append([0, 2, 3])
        else:
            machines.append([0, 3])

    #TODO: Sinsinin ang processing times.
    processing_times = []
    for i in range(0, len(df.index)):
        # Include Printing and Laminating machine
        if df.ix[i]['printed'] == 1 and df.ix[i]['laminate'] == 1:
            processing_times.append([2, 5, 1, 4])
        # Include only Printing
        elif df.ix[i]['printed'] == 1:
            processing_times.append([2, 5, 4])
        # Include only Laminating
        elif df.ix[i]['laminate'] == 1:
            processing_times.append([2, 1, 4])
        else:
            processing_times.append([2, 4])

    # Compute horizon.
    horizon = 0
    for i in all_jobs:
        horizon += sum(processing_times[i])

    # Create jobs.
    all_tasks = {}
    for i in all_jobs:
        for j in range(0, len(machines[i])):
            all_tasks[(i, j)] = solver.FixedDurationIntervalVar(0,
                                                                horizon,
                                                                processing_times[i][j],
                                                                False,
                                                                'Job %i_%i' % (i, j))

    # Create sequence variables and add disjunctive constraints.
    all_sequences = []
    for i in all_machines:
        machines_jobs = []
        for j in all_jobs:
            for k in range(0, len(machines[j])):
                if machines[j][k] == i:
                    machines_jobs.append(all_tasks[(j, k)])
        disj = solver.DisjunctiveConstraint(machines_jobs, 'machine %i' % i)
        all_sequences.append(disj.SequenceVar())
        solver.Add(disj)

    # Add conjunctive constraints.
    for i in all_jobs:
        for j in range(0, len(machines[i]) - 1):
            solver.Add(all_tasks[(i, j + 1)].StartsAfterEnd(all_tasks[(i, j)]))

    # Set the objective.
    obj_var = solver.Max([all_tasks[(i, len(machines[i])-1)].EndExpr()
                          for i in all_jobs])
    objective_monitor = solver.Minimize(obj_var, 1)
    # Create search phases.
    sequence_phase = solver.Phase([all_sequences[i] for i in all_machines],
                                  solver.SEQUENCE_DEFAULT)
    vars_phase = solver.Phase([obj_var],
                              solver.CHOOSE_FIRST_UNBOUND,
                              solver.ASSIGN_MIN_VALUE)
    main_phase = solver.Compose([sequence_phase, vars_phase])
    # Create the solution collector.
    collector = solver.LastSolutionCollector()

    # Add the interesting variables to the SolutionCollector.
    collector.Add(all_sequences)
    collector.AddObjective(obj_var)

    for i in all_machines:
        sequence = all_sequences[i];
        sequence_count = sequence.Size();
        for j in range(0, sequence_count):
            t = sequence.Interval(j)
            collector.Add(t.StartExpr().Var())
            collector.Add(t.EndExpr().Var())

    # Solve the problem.
    # Arrays for plotly gantt chart
    plot_df = []
    machine_list = []
    start_list = []
    finish_list = []
    resource_list = []
    description_list = []
    current_time = np.datetime64(datetime.datetime.now())
    disp_col_width = 10

    if solver.Solve(main_phase, [objective_monitor, collector]):
        for i in all_machines:
            seq = all_sequences[i]
            machine_list.append(get_machine_type(i))  # Add machine name
            sequence = collector.ForwardSequence(0, seq)
            seq_size = len(sequence)

            for j in range(0, seq_size):
                t = seq.Interval(sequence[j]);
                temp_name = t.Name().split('_', 1)[0]
                temp_name = temp_name[4:]  # get the job number
                job_num = int(temp_name)
                resource_list.append(str(df.ix[job_num, 'id']))  # Add resource (aka Job ID)
                description_list.append(df.ix[job_num, 'material_type'])  # Add material used to description list

            for j in range(0, seq_size):
                t = seq.Interval(sequence[j]);
                # Add start time
                start_list.append(get_start_time(current_time, collector.Value(0, t.StartExpr().Var())))
                # Add finish time
                finish_list.append(get_finish_time(current_time, collector.Value(0, t.EndExpr().Var())))

            for j in range(0, seq_size):
                temp_dict = {'Task': machine_list[i],
                             'Start': start_list.pop(0),
                             'Finish': finish_list.pop(0),
                             'Resource': resource_list.pop(0),
                             'Description': description_list.pop(0)
                             }
                plot_df.append(temp_dict)

        chart(plot_df, filename)


# Generates gantt for all machine types
def generate_overview_gantt_chart(df):
    schedule(df, 'overview_gantt_chart.html')


# Generates gantt for specific machine types
def generate_specific_gantt_chart(df, machine_type):
    filename = machine_type + '_gantt_chart.html'
    chart(df, filename)

def main():
    data = {'id': [100, 101, 102],
            'laminate': [0, 1, 0],
            'printed': [1, 1, 0],
            'material_type': ['PP', 'PET', 'PP']}
    df = pd.DataFrame(data, index=[0, 1, 2])
    generate_overview_gantt_chart(df)

if __name__ == '__main__':
    main()
