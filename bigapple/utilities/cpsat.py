from __future__ import print_function
import collections
from ortools.sat.python import cp_model
from django.db.models import Count, Sum
from production.models import Machine, JobOrder, ExtruderSchedule, CuttingSchedule, PrintingSchedule, LaminatingSchedule
from sales.models import ClientItem
from accounts.models import Employee
from django.db.models import Q
from collections import defaultdict
import datetime
from datetime import timedelta, datetime

def flexible_jobshop(df, actual_out, job_match, extrusion_not_final, cutting_not_final, printing_not_final, laminating_not_final, in_production):
    # Data part.
    jobs = []
    joids = []

    extruder_machines = Machine.objects.filter(Q(machine_type='Extruder') & Q(state='OK'))
    e_mach = []
    for x in extruder_machines:
        id = x.machine_id
        e_mach.append(id)
    cutting_machines = Machine.objects.filter(Q(machine_type='Cutting') & Q(state='OK'))
    c_mach = []
    for x in cutting_machines:
        id = x.machine_id
        c_mach.append(id)
    printing_machines = Machine.objects.filter(Q(machine_type='Printing') & Q(state='OK'))
    p_mach = []
    for x in printing_machines:
        id = x.machine_id
        p_mach.append(id)
    laminating_machines = Machine.objects.filter(Q(machine_type='Laminating') & Q(state='OK'))
    l_mach = []
    for x in laminating_machines:
        id = x.machine_id
        l_mach.append(id)

    extruders = Employee.objects.filter(position='Extruder')
    e_work = []
    for x in extruders:
        id = x.id
        e_work.append(id)
    cutters = Employee.objects.filter(position='Cutting')
    c_work = []
    for x in cutters:
        id = x.id
        c_work.append(id)
    printers = Employee.objects.filter(position='Printing')
    p_work = []
    for x in printers:
        id = x.id
        p_work.append(id)
    laminators = Employee.objects.filter(position='Laminating')
    l_work = []
    for x in laminators:
        id = x.id
        l_work.append(id)

    for i in range(0, len(df.index)):
        item = ClientItem.objects.get(client_po_id=df.ix[i]['id'])
        joids.append(df.ix[i]['id'])
        quantity = item.quantity
        number_rolls = number_rolls = float(quantity / 10000)
        if extrusion_not_final and df.ix[i]['id'] == job_match:
            e = ExtruderSchedule.objects.filter(Q(job_order_id = df.ix[i]['id']) & Q(ideal=False))
            if e:
                sum_number_rolls = float(e.aggregate(Sum('number_rolls'))['number_rolls__sum'])
                balance_number_rolls = number_rolls - sum_number_rolls
                quantity = balance_number_rolls * 10000
                extrusion_time = int((quantity * 80) / 70000)
        else:
            extrusion_time = int((quantity * 80) / 70000)
        if cutting_not_final and df.ix[i]['id'] == job_match:
            c = CuttingSchedule.objects.filter(Q(job_order_id=df.ix[i]['id']) & Q(ideal=False))
            if c:
                sum_number_rolls = float(c.aggregate(Sum('number_rolls'))['number_rolls__sum'])
                balance_number_rolls = number_rolls - sum_number_rolls
                quantity = balance_number_rolls * 10000
                cutting_time = int((quantity * 60) / 70000)
        else:
            cutting_time = int((quantity * 60) / 70000)
        if laminating_not_final and df.ix[i]['id'] == job_match:
            l = LaminatingSchedule.objects.filter(Q(job_order_id=df.ix[i]['id']) & Q(ideal=False))
            if l:
                sum_number_rolls = float(l.aggregate(Sum('number_rolls'))['number_rolls__sum'])
                balance_number_rolls = number_rolls - sum_number_rolls
                quantity = balance_number_rolls * 10000
                laminating_time = int((quantity * 60) / 70000)
        else:
            laminating_time = int((quantity * 60) / 70000)
        if printing_not_final and df.ix[i]['id'] == job_match:
            p = PrintingSchedule.objects.filter(Q(job_order_id=df.ix[i]['id']) & Q(ideal=False))
            if p:
                sum_number_rolls = float(p.aggregate(Sum('number_rolls'))['number_rolls__sum'])
                balance_number_rolls = number_rolls - sum_number_rolls
                quantity = balance_number_rolls * 10000
                printing_time = int((quantity * 100) / 70000)
        else:
            printing_time = int((quantity * 100) / 70000)

        if in_production:
            print('IN_PRODUCTION')
            print(in_production)
            for each in in_production:
                if each.id == df.ix[i]['id']:
                    if each.status == 'Under Extrusion':
                        e = ExtruderSchedule.objects.filter(Q(job_order_id=df.ix[i]['id']) & Q(ideal=False))
                        if e:
                            sum_number_rolls = float(e.aggregate(Sum('number_rolls'))['number_rolls__sum'])
                            balance_number_rolls = number_rolls - sum_number_rolls
                            quantity = balance_number_rolls * 10000
                            extrusion_time = int((quantity * 80) / 70000)
                    elif each.status == 'Under Cutting':
                        extrusion_time = 0
                        printing_time = 0
                        laminating_time = 0
                        c = CuttingSchedule.objects.filter(Q(job_order_id=df.ix[i]['id']) & Q(ideal=False))
                        if c:
                            sum_number_rolls = float(c.aggregate(Sum('number_rolls'))['number_rolls__sum'])
                            balance_number_rolls = number_rolls - sum_number_rolls
                            quantity = balance_number_rolls * 10000
                            cutting_time = int((quantity * 60) / 70000)
                    elif each.status == 'Under Laminating':
                        extrusion_time = 0
                        printing_time = 0
                        l = LaminatingSchedule.objects.filter(Q(job_order_id=df.ix[i]['id']) & Q(ideal=False))
                        if l:
                            sum_number_rolls = float(l.aggregate(Sum('number_rolls'))['number_rolls__sum'])
                            balance_number_rolls = number_rolls - sum_number_rolls
                            quantity = balance_number_rolls * 10000
                            laminating_time = int((quantity * 60) / 70000)
                    elif each.status == 'Under Printing':
                        extrusion_time = 0
                        p = PrintingSchedule.objects.filter(Q(job_order_id=df.ix[i]['id']) & Q(ideal=False))
                        if p:
                            sum_number_rolls = float(p.aggregate(Sum('number_rolls'))['number_rolls__sum'])
                            balance_number_rolls = number_rolls - sum_number_rolls
                            quantity = balance_number_rolls * 10000
                            printing_time = int((quantity * 100) / 70000)
        extrusion = []
        cutting = []
        printing = []
        laminating = []
        job = []

        for e in e_mach:
            for a in e_work:
                extrusion.append((extrusion_time, e, a))
        if extrusion_not_final:
            job.append(extrusion)
        for p in p_mach:
            if df.ix[i]['printed'] == 1:
                for b in p_work:
                    printing.append((printing_time, p, b))
                if printing_not_final:
                    job.append(printing)
            else:
                pass
        for l in l_mach:
            if df.ix[i]['laminate'] == 1:
                for c in l_work:
                    laminating.append((laminating_time, l, c))
                if laminating_not_final:
                    job.append(laminating)
            else:
                pass
        for c in c_mach:
            for d in c_work:
                cutting.append((cutting_time, c, d))
        if cutting_not_final:
            job.append(cutting)

        jobs.append(job)

    print('jobs')
    print(jobs)

    num_jobs = len(jobs)
    all_jobs = range(num_jobs)

    num_machines = Machine.objects.filter(state='OK').count()
    all_machines = range(num_machines)

    all_workers = range(len(e_work) + len(c_work) + len(p_work))

    # Model the flexible jobshop problem.
    model = cp_model.CpModel()

    horizon = 0
    for job in jobs:
        for task in job:
            max_task_duration = 0
            for alternative in task:
                max_task_duration = max(max_task_duration, alternative[0])
            horizon += max_task_duration

    print('Horizon = %i' % horizon)

    # Global storage of variables.
    intervals_per_resources = defaultdict(list)
    intervals_per_workers = defaultdict(list)
    starts = {}  # indexed by (job_id, task_id).
    presences = {}  # indexed by (job_id, task_id, alt_id).
    job_ends = []

    # Scan the jobs and create the relevant variables and intervals.
    for job_id in all_jobs:
        job = jobs[job_id]
        num_tasks = len(job)
        previous_end = None

        for task_id in range(num_tasks):
            task = job[task_id]

            min_duration = task[0][0]
            max_duration = task[0][0]

            num_alternatives = len(task)
            all_alternatives = range(num_alternatives)
            for alt_id in range(1, num_alternatives):
                alt_duration = task[alt_id][0]
                min_duration = min(min_duration, alt_duration)
                max_duration = max(max_duration, alt_duration)

            if min_duration != max_duration:
                print(min_duration, max_duration)

            # Create main interval for the task.
            suffix_name = '_j%i_t%i' % (job_id, task_id)
            start = model.NewIntVar(0, horizon, 'start' + suffix_name)
            duration = model.NewIntVar(min_duration, max_duration,
                                       'duration' + suffix_name)
            end = model.NewIntVar(0, horizon, 'end' + suffix_name)

            # Store the start for the solution.
            starts[(job_id, task_id)] = start

            # Add precedence with previous task in the same job.
            if previous_end:
                model.Add(start >= previous_end)
            previous_end = end

            # Create alternative intervals.
            if num_alternatives > 1:
                l_presences = []
                for alt_id in all_alternatives:
                    alt_suffix = '_j%i_t%i_a%i' % (job_id, task_id, alt_id)
                    l_presence = model.NewBoolVar('presence' + alt_suffix)
                    l_interval = model.NewOptionalIntervalVar(
                        start, duration, end, l_presence,
                        'interval' + alt_suffix)
                    l_presences.append(l_presence)

                    # Add the local interval to the right machine.
                    intervals_per_resources[task[alt_id][1]].append(l_interval)

                    # Add the local interval to the right worker.

                    intervals_per_workers[task[alt_id][2]].append(l_interval)

                    # Store the presences for the solution.
                    presences[(job_id, task_id, alt_id)] = l_presence

                # Select exactly one presence variable.
                model.Add(sum(l_presences) == 1)
            else:
                interval = model.NewIntervalVar(start, duration, end,
                                                'interval' + suffix_name)
                intervals_per_resources[task[0][1]].append(interval)
                intervals_per_workers[task[0][2]].append(interval)
                presences[(job_id, task_id, 0)] = model.NewIntVar(1, 1, '')

        job_ends.append(previous_end)

    # Create machines constraints.
    for machine_id, intervals in intervals_per_resources.items():
        intervals = intervals_per_resources[machine_id]

        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

    # Create workers constraints.
    for worker_id, intervals in intervals_per_workers.items():
        intervals = intervals_per_workers[worker_id]

        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

    # Makespan objective
    makespan = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(makespan, job_ends)
    model.Minimize(makespan)

    if actual_out:
        actual_out = str(actual_out)
        actual_out = datetime.strptime(actual_out, "%Y-%m-%d %H:%M:%S")
        dateTimeDifference = actual_out - datetime.now()
        dateTimeDifferenceInHours = dateTimeDifference.total_seconds() / 3600
        dateTimeDifferenceInHours = abs(dateTimeDifferenceInHours)
    else:
        dateTimeDifferenceInHours = 0

    print('8-------')
    # Solve model.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    #solution_printer = SolutionPrinter()
    #status = solver.SolveWithSolutionCallback(model, solution_printer)
    print('9-------')
    # Print/save final solution.
    plot_list = []
    for job_id in all_jobs:
        print('Job %i:' % job_id)
        for task_id in range(len(jobs[job_id])):
            start_value = solver.Value(starts[(job_id, task_id)])
            start_value = start_value - dateTimeDifferenceInHours
            machine = -1
            duration = -1
            selected = -1
            worker = -1
            for alt_id in range(len(jobs[job_id][task_id])):
                if solver.Value(presences[(job_id, task_id, alt_id)]):
                    duration = jobs[job_id][task_id][alt_id][0]
                    machine = jobs[job_id][task_id][alt_id][1]
                    selected = alt_id
                    worker = jobs[job_id][task_id][alt_id][2]
            print(
                '  task_%i_%i starts at %i (alt %i, machine %i, duration %i, worker %i)' %
                (job_id, task_id, start_value, selected, machine, duration, worker))

            if datetime.now() + timedelta(hours=start_value) != datetime.now() + timedelta(hours=start_value + duration):
                item = ClientItem.objects.get(client_po_id=joids[job_id])
                product = item.products
                material = product.material_type

                phase = None

                if task_id == 0:
                    phase = 'Extrusion'
                elif task_id == 1:
                    if item.printed == 1:
                        phase = 'Printing'
                    elif item.laminate == 1:
                        phase = 'Laminating'
                    else:
                        phase = 'Cutting'
                elif task_id == 2:
                    if item.laminate == 1:
                        phase = 'Laminating'
                    else:
                        phase = 'Cutting'
                elif task_id == 3:
                    phase = 'Cutting'

                temp_dict = {'ID': joids[job_id],
                             'Machine': Machine.objects.get(machine_id=machine),
                             'Task': phase,
                             'Start': datetime.now() + timedelta(hours=start_value),
                             'Finish': datetime.now() + timedelta(hours=start_value + duration),
                             'Resource': material,
                             'Worker': Employee.objects.get(id=worker)
                             }

                plot_list.append(temp_dict)


    print('Solve status: %s' % solver.StatusName(status))
    print('Optimal objective value: %i' % solver.ObjectiveValue())
    print('Statistics')
    print('  - conflicts : %i' % solver.NumConflicts())
    print('  - branches  : %i' % solver.NumBranches())
    print('  - wall time : %f s' % solver.WallTime())


    return plot_list