# Import Python wrapper for or-tools constraint solver.
from ortools.constraint_solver import pywrapcp
from plotly.offline import plot
# import plotly.offline
import plotly.figure_factory as ff
import numpy as np
import pandas as pd
import datetime
from django.db.models import Count
from production.models import Machine, JobOrder
from sales.models import ClientItem
from accounts.models import Employee
from django.db.models import Q
import random

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

def get_worker(i):
    worker_dict = {0: 'Extruder', 1: 'Printing', 2: 'Cutting'}
    return worker_dict.get(i)

def get_machine_type(i):
    machine_dict = {0: 'Extruder', 1: 'Printing', 2: 'Laminating', 3: 'Cutting'}
    return machine_dict.get(i)


def get_processing_time(machine_type):
    processing_time_dict = {'Extruder': 2, 'Printing': 5, 'Laminating': 1, 'Cutting': 4}

    return processing_time_dict.get(machine_type)

    '''
    processing_times = []
    for i in range(0, len(df.index)):
        # Include Printing and Laminating machine
        # Standard lead time: Plain - 1-2 weeks; Printed - 2-4 weeks
        # IN HOURS:
        # Extruder = 4 days * 20 hours every 70000 pieces = 80hr/70000pcs
        # Cutting = 3 days * 20 hours every 70000 pieces = 60hr/70000pcs
        # Laminating = 3 days * 20 hours every 70000 pieces = 60hr/70000pcs
        # Printing = 5 days * 20 hours  every 70000 pieces = 100hr/70000pcs
        item = ClientItem.objects.get(client_po_id=df.ix[i]['id'])
        quantity = item.quantity
        extrusion_time = int((quantity * 80) / 70000)
        cutting_time = int((quantity * 60) / 70000)
        laminating_time = int((quantity * 60) / 70000)
        printing_time = int((quantity * 100) / 70000)

        if df.ix[i]['printed'] == 1 and df.ix[i]['laminate'] == 1:
            processing_times.append(
                [extrusion_time, printing_time, laminating_time, cutting_time])  # Extrude, Print, Laminate, Cut
        # Include only Printing
        elif df.ix[i]['printed'] == 1:
            processing_times.append([extrusion_time, printing_time, cutting_time])
        # Include only Laminating
        elif df.ix[i]['laminate'] == 1:
            processing_times.append([extrusion_time, laminating_time, cutting_time])
        else:
            processing_times.append([extrusion_time, cutting_time])

    return processing_times
    '''

# Creates html file of plotly gantt chart
def chart(task_list, filename):
    all_the_colors = list((x, y, z) for x in range(256) for y in range(256) for z in range(256))
    colors = [f"rgb({random.choice(all_the_colors)})" for x in task_list.Resource.unique()]

    print('generated colors')
    task_list.Resource = task_list.Resource.apply(str)
    print('applied to str')
    fig = ff.create_gantt(task_list, colors=colors, index_col='Resource', show_colorbar=True, group_tasks=True)
    print('created gantt')
    # plot(fig, filename=filename)
    return plot(fig, filename=filename, include_plotlyjs=False, output_type='div')
    #print(fig)


# Solves the job shop problem using OR-tools constraint solver, returns a dictionary with the solution
def schedule(df, filename):
    solver = pywrapcp.Solver('jobshop')

    machines_count = Machine.objects.filter(state='OK').count() # Extrude, Print, (Laminate), Cut
    machine_type = Machine.objects.filter(state='OK')
    workers_count = Employee.objects.filter(Q(position='Cutting') | Q(position='Extruder') | Q(position='Printing') | Q(position='Laminating')).count()
    jobs_count = len(df.index)
    all_machines = range(0, machines_count)
    all_jobs = range(0, jobs_count)
    all_workers = range(0, workers_count)
    workers = Employee.objects.filter(Q(position='Cutting') | Q(position='Extruder') | Q(position='Printing') | Q(position='Laminating'))

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

    processing_times = []
    for i in range(0, len(df.index)):
        # Include Printing and Laminating machine
        # Standard lead time: Plain - 1-2 weeks; Printed - 2-4 weeks
        # IN HOURS:
        # Extruder = 4 days * 20 hours every 70000 pieces = 80hr/70000pcs
        # Cutting = 3 days * 20 hours every 70000 pieces = 60hr/70000pcs
        # Laminating = 3 days * 20 hours every 70000 pieces = 60hr/70000pcs
        # Printing = 5 days * 20 hours  every 70000 pieces = 100hr/70000pcs
        item = ClientItem.objects.get(client_po_id=df.ix[i]['id'])
        quantity = item.quantity
        extrusion_time = int((quantity * 80) / 70000)
        cutting_time = int((quantity * 60) / 70000)
        laminating_time = int((quantity * 60) / 70000)
        printing_time = int((quantity * 100) / 70000)

        if df.ix[i]['printed'] == 1 and df.ix[i]['laminate'] == 1:
            processing_times.append(
                [extrusion_time, printing_time, laminating_time, cutting_time])  # Extrude, Print, Laminate, Cut
        # Include only Printing
        elif df.ix[i]['printed'] == 1:
            processing_times.append([extrusion_time, printing_time, cutting_time])
        # Include only Laminating
        elif df.ix[i]['laminate'] == 1:
            processing_times.append([extrusion_time, laminating_time, cutting_time])
        else:
            processing_times.append([extrusion_time, cutting_time])

    # Compute horizon.
    horizon = 0
    for i in all_jobs:
        horizon += sum(processing_times[i])
        horizon = int(horizon)

    # Create jobs.
    all_tasks = {}
    for i in all_jobs:
        for j in range(0, len(machines[i])):
            all_tasks[(i, j)] = solver.FixedDurationIntervalVar(0,
                                                                horizon,
                                                                processing_times[i][j],
                                                                False,
                                                                'Job_%i_%i' % (i, j))

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

    # TODO Consider date_required of job
    '''
    for job in all_jobs:
        for task_id in range(0, len(jobs_count) - 1):
            solver.Add(all_tasks[job, task_id +
                                1].start >= all_tasks[job, task_id].end)
    '''

    # Set the objective.
    obj_var = solver.Max([all_tasks[(i, len(machines[i]) - 1)].EndExpr()
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
    plot_list = []
    machine_list = []
    start_list = []
    finish_list = []
    resource_list = []
    description_list = []
    worker_list = []
    current_time = np.datetime64(datetime.datetime.now())

    if solver.Solve(main_phase, [objective_monitor, collector]):
        for i in all_machines:
            seq = all_sequences[i]
            machine_list.append(get_machine_type(i))  # Add machine name
            sequence = collector.ForwardSequence(0, seq)
            seq_size = len(sequence)

            for j in range(0, seq_size):
                t = seq.Interval(sequence[j]);
                temp_name = t.Name().split('_')  # , 1)[1]
                temp_name_test = temp_name
                temp_name = temp_name[1]  # get the job number
                job_num = int(temp_name)
                resource_list.append(str(df.ix[job_num, 'id']))  # Add resource (aka Job ID)
                description_list.append(df.ix[job_num, 'material_type'])  # Add material used to description list

            for j in range(0, seq_size):
                t = seq.Interval(sequence[j]);
                # Add start time
                start_list.append(get_start_time(current_time, collector.Value(0, t.StartExpr().Var())))
                # Add finish time
                finish_list.append(get_finish_time(current_time, collector.Value(0, t.EndExpr().Var())))

            # TODO Include worker in schedule
            '''
                        for j in range(0, seq_size):
                            #t = seq.Interval(sequence[j]);
                            worker_list.append(get_worker(j))
            '''

            for j in range(0, seq_size):
                temp_dict = {'Task': machine_list[i],
                             'Start': start_list.pop(0),
                             'Finish': finish_list.pop(0),
                             'Resource': resource_list.pop(0),
                             'Description': description_list.pop(0),
                             # 'Worker' : worker_list.pop(0)
                             }
                plot_list.append(temp_dict)

        print('sched() plot_list:')
        print(plot_list)

        if filename == 'specific':
            return plot_list

        elif filename == 'save':
            return plot_list

        else:
            # print(plot_list)
            return chart(plot_list, filename)


# Generates gantt for all machine types
def generate_overview_gantt_chart(df):
    return schedule(df, '/production_schedule.html')


# Generates gantt for specific machine types
def generate_specific_gantt_chart(task_list, machines, machine_type, workers, charting):
    filename = machine_type + '_gantt_chart.html'
   #task_list = schedule(df, 'specific')  # use OR-tools to solve over all schedule
    plot_list = []
    last_task_finish_time = []  # keep track of batch finish times
    count = 0
    worker_list = []

    # Loop through array find elements where Task == machine_type
    for i in range(0, len(task_list)):
        # one by one, allocate a task per machine
        # reset count when all machines have been allocated
        j = 0  # batch counter

        if count == len(machines):
            count = 0
            j += 1

        # make a new dict
        if (task_list[i])['Task'] == machine_type:
            # assumes 1 worker: 1 machine ratio, allocates one worker to all of the machine's tasks
            worker_name = workers[count]
            curr_task = (task_list[i])
            start_list = []
            finish_list = []

            worker_list.append(worker_name)
            #if count == 0:
                # assumes that tasks have the same length per machine type
                # copies the placement of the task from the first machine's schedule
             #   if j == 0:
                    # BATCH 1
              #      first_task_start_time = curr_task['Start']
               #     first_task_finish_time = curr_task['Finish']
                    #last_task_finish_time.append(first_task_finish_time)

               # else:
                    # BATCH 2 onwards
                #    first_task_start_time = last_task_finish_time[j-1]
                 #   first_task_finish_time = get_finish_time(np.datetime64(first_task_start_time),
                  #                                           get_processing_time(machine_type))
                   # last_task_finish_time.append(first_task_finish_time)

                # temp_dict = {'Task': machine_type + str(machines[count]),
                #              'Start': first_task_start_time,
                #              'Finish': first_task_finish_time,
                #              'Resource': curr_task['Resource'],
                #              'Description': curr_task['Description']
                #              }

            # ADD TO DICTIONARY for plotly
            temp_dict = {'Task': machine_type + str(count),
                         'Start': curr_task['Start'],
                         'Finish': curr_task['Finish'],
                         'Resource': curr_task['Resource'],
                         'Description': curr_task['Description']+' - '+ str(worker_name.first_name) + ' ' + str(worker_name.last_name)
                         #'Worker': str(worker_name.first_name) + ' ' + str(worker_name.last_name)
                         }

            plot_list.append(temp_dict)

        count += 1
    print('plot_list')
    print(plot_list)
    if charting:
        return chart(plot_list, filename)
    else:
        return worker_list


def get_sched_data(df):
    data = schedule(df, 'save')
    return data

def main():
    data = {'id': [100, 101, 102],
            'laminate': [0, 1, 0],
            'printed': [1, 1, 0],
            'material_type': ['PP', 'PET', 'PP']}
    df = pd.DataFrame(data, index=[0, 1, 2])

    # generate_overview_gantt_chart(df)
    generate_specific_gantt_chart(df, ['000', '001'], machine_type='Extruder')


if __name__ == '__main__':
    main()
