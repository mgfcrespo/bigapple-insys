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
from datetime import timedelta, datetime, time
import operator

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
            e = ExtruderSchedule.objects.filter(Q(job_order_id=df.ix[i]['id']) & Q(ideal=False))
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
                for alt_id in range(0, num_alternatives, 3):
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
    # for worker_id, intervals in intervals_per_workers.items():
    #    intervals = intervals_per_workers[worker_id]

    #    if len(intervals) > 1:
    #        model.AddNoOverlap(intervals)


    # Makespan objective
    makespan = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(makespan, job_ends)
    model.Minimize(makespan)

    # Solve model.
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    status = solver.Solve(model)

    # Print/save final solution.
    plot_list = []
    for job_id in all_jobs:
        print('Job %i:' % job_id)
        for task_id in range(len(jobs[job_id])):
            start_value = solver.Value(starts[(job_id, task_id)])
            # start_value = start_value - dateTimeDifferenceInHours
            machine = -1
            duration = -1
            selected = -1
            worker = -1
            duration = jobs[job_id][task_id][0][0]
            if duration == 0:
                continue
            for alt_id in range(0, len(jobs[job_id][task_id]), 3):

                if solver.Value(presences[(job_id, task_id, alt_id)]):
                    machine = jobs[job_id][task_id][alt_id][1]
                    selected = alt_id
                    worker = jobs[job_id][task_id][alt_id][2]
            print(
                '  task_%i_%i starts at %i (alt %i, machine %i, duration %i, worker %i)'
                % (job_id, task_id, start_value, selected, machine, duration,
                   worker))

    print('Solve status: %s' % solver.StatusName(status))
    print('Optimal objective value: %i' % solver.ObjectiveValue())
    print('Statistics')
    print('  - conflicts : %i' % solver.NumConflicts())
    print('  - branches  : %i' % solver.NumBranches())
    print('  - wall time : %f s' % solver.WallTime())

    return plot_list


def shift_schedule(plot_list):
    work = Employee.objects.filter(Q(position='Extruder') |Q(position='Cutting') | Q(position='Printing') | Q(position='Laminating'))

    print(work)
    print('------')
    num_workers = len(work)
    all_workers = range(num_workers)
    num_shifts = 3
    plot_list.sort(key=lambda x: x["Finish"])
    i = len(plot_list) - 1
    earliest = plot_list[0]['Start']
    latest = plot_list[i]['Finish']
    num_days = (latest - earliest).days
    all_shifts = range(num_shifts)
    all_days = range(num_days)
    #TODO Add shift specializations per worker. SEE: [worker[day[shift, 1 = specialization]]]
    specializations = []
    week = []
    worker = []
    foo = False
    check = False
    count = 0

    for x in work:
        week = []
        count = 0
        for every in all_days:
            compare = earliest + timedelta(days=every)
            for a in range(len(plot_list)):
                if plot_list[a]['Start'].date() == compare.date() or plot_list[a]['Finish'].date() == compare.date():
                    foo = True
                if len(week) == every:
                    check = True
                else:
                    check = False
                if x.position == 'Extruder' and plot_list[a]['Task'] == 'Extrusion' and foo and check and count == every:
                    if 6 == plot_list[a]['Start'].hour or 7 == plot_list[a]['Start'].hour or 8 == plot_list[a]['Start'].hour or \
                        12 == plot_list[a]['Finish'].hour or 13 == plot_list[a][
                            'Finish'].hour or 14 == plot_list[a]['Finish'].hour:
                        week.insert(every, [1, 0, 0])
                        count += 1
                        break
                    elif 14 == plot_list[a]['Start'].hour or 15 == plot_list[a]['Start'].hour or 16 == plot_list[a]['Start'].hour or \
                        20 == plot_list[a]['Finish'].hour or 21 == plot_list[a][
                            'Finish'].hour or 22 == plot_list[a]['Finish'].hour:
                        #week.append([0, 1, 0])
                        week.insert(every, [0, 1, 0])
                        count += 1
                        break
                    elif 4 == plot_list[a]['Finish'].hour or 5 == plot_list[a]['Finish'].hour or 6 == plot_list[a]['Finish'].hour or \
                        20 == plot_list[a]['Start'].hour or 21 == plot_list[a][
                            'Start'].hour or 22 == plot_list[a]['Start'].hour:
                        #week.append([0, 0, 1])
                        week.insert(every, [0, 0, 1])
                        count += 1
                        break
                elif x.position == plot_list[a]['Task'] and foo and check and count == every:
                    if 6 == plot_list[a]['Start'].hour or 7 == plot_list[a]['Start'].hour or 8 == plot_list[a]['Start'].hour or \
                            12 == plot_list[a]['Finish'].hour or 13 == plot_list[a][
                            'Finish'].hour or 14 == plot_list[a]['Finish'].hour:
                        #week.append([1, 0, 0])
                        week.insert(every, [1, 0, 0])
                        count += 1
                        print('SHIFT 1 ADDED FOR ' + str(x))
                        break
                    elif 14 == plot_list[a]['Start'].hour or 15 == plot_list[a][
                        'Start'].hour or 16 == plot_list[a]['Start'].hour or \
                            20 == plot_list[a]['Finish'].hour or 21 == plot_list[a][
                            'Finish'].hour or 22 == plot_list[a]['Finish'].hour:
                        #week.append([0, 1, 0])
                        week.insert(every, [0, 1, 0])
                        count += 1
                        print('SHIFT 2 ADDED FOR ' + str(x))
                        break
                    elif 4 == plot_list[a]['Finish'].hour or 5 == plot_list[a][
                        'Finish'].hour or 6 == plot_list[a]['Finish'].hour or \
                            20 == plot_list[a]['Start'].hour or 21 == plot_list[a][
                            'Start'].hour or 22 == plot_list[a]['Start'].hour:
                        #week.append([0, 0, 1])
                        week.insert(every, [0, 0, 1])
                        count += 1
                        print('SHIFT 3 ADDED FOR ' + str(x))
                        break
                else:
                    pass
        if len(week) < (num_days - 1):
            for a in range(0, (num_days-len(week))):
                week.append([0, 0, 0])
                print('NONE ADDED FOR ' + str(x))
            print('End of ' + str(every))
        specializations.append(week)

    print(specializations)
    print('------')

    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: worker 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_workers:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d,
                        s)] = model.NewBoolVar('shift_n%id%is%i' % (n, d, s))
    print(shifts)
    print('------')
    for d in all_days:
        for s in all_shifts:
            model.Add(sum(shifts[(n, d, s)] for n in all_workers) >= 1)

    # Each worker works at most one shift per day.
    for n in all_workers:
        for d in all_days:
            model.Add(sum(shifts[(n, d, s)] for s in all_shifts) <= 1)

    # min_shifts_assigned is the largest integer such that every worker can be
    # assigned at least that number of shifts.
    min_shifts_per_worker = (num_shifts * num_days) // num_workers
    max_shifts_per_worker = min_shifts_per_worker + 1
    for n in all_workers:
        num_shifts_worked = sum(
            shifts[(n, d, s)] for d in all_days for s in all_shifts)
        model.Add(min_shifts_per_worker <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_worker)

    model.Maximize(
        sum(specializations[n][d][s] * shifts[(n, d, s)] for n in all_workers for d in all_days for s in all_shifts))

    print('------ 2nd to last')
    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.Solve(model)
    workers_schedule = []
    for d in all_days:
        print('Day', d)
        for n in all_workers:
            for s in all_shifts:
                if solver.Value(shifts[(n, d, s)]) == 1:
                    if specializations[n][d][s] == 1:
                        print('worker', n, 'works shift', s, '(specialization).')
                    else:
                        print('worker', n, 'works shift', s, '(non-specialization).')
                    temp_dict = {'Worker' : work[n],
                                 'Shift' : s+1,
                                 'Day' : (earliest+timedelta(days=d)).date()}

                    workers_schedule.append(temp_dict)

    print(workers_schedule)

    # Statistics.
    print()
    print('Statistics')
    print('  - Number of shift prioritizations met = %i' % solver.ObjectiveValue(),
          '(out of', num_workers * min_shifts_per_worker, ')')
    print('  - wall time       : %f s' % solver.WallTime())

    return workers_schedule



class NursesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_nurses, num_days, num_shifts, num_machines, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_nurses = num_nurses
        self._num_days = num_days
        self._num_shifts = num_shifts
        self._num_machines = num_machines
        self._solutions = set(sols)
        self._solution_count = 0

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            for d in range(self._num_days):
                print('Day %i' % d)
                for n in range(self._num_nurses):
                    is_working = False
                    for s in range(self._num_shifts):
                        if self.Value(self._shifts[(n, d, s)]):
                            is_working = True
                            print('  Nurse %i works shift %i' % (n, s))
                    if not is_working:
                        print('  Nurse {} does not work'.format(n))
            print()
        self._solution_count += 1

    def solution_count(self):
        return self._solution_count

def shifts(plot_list):
    extruders = Employee.objects.filter(position='Extruder')
    e_work = []
    for x in extruders:
        id = x.id
        e_work.append(id)

    num_nurses = 5
    all_nurses = range(num_nurses)
    num_shifts = 3
    plot_list.sort(key=lambda x: x["Finish"])
    i = len(plot_list) - 1
    earliest = plot_list[0]['Start']
    latest = plot_list[i]['Finish']
    num_days = (latest - earliest).days
    all_shifts = range(num_shifts)
    all_days = range(num_days)
    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: nurse 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar('shift_n%id%is%i' % (n, d,
                                                                          s))

    # Each shift is assigned to exactly one nurse in the schedule period.
    for d in all_days:
        for s in all_shifts:
            model.Add(sum(shifts[(n, d, s)] for n in all_nurses) >= 1)

    # Each nurse works at most one shift per day.
    for n in all_nurses:
        for d in all_days:
            model.Add(sum(shifts[(n, d, s)] for s in all_shifts) <= 1)

    # min_shifts_per_nurse is the largest integer such that every nurse
    # can be assigned at least that many shifts. If the number of nurses doesn't
    # divide the total number of shifts over the schedule period,
    # some nurses have to work one more shift, for a total of
    # min_shifts_per_nurse + 1.
    min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
    max_shifts_per_nurse = min_shifts_per_nurse + 1
    for n in all_nurses:
        num_shifts_worked = sum(
            shifts[(n, d, s)] for d in all_days for s in all_shifts)
        model.Add(min_shifts_per_nurse <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_nurse)

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    # Display the first five solutions.
    a_few_solutions = range(1)
    solution_printer = NursesPartialSolutionPrinter(
        shifts, num_nurses, num_days, num_shifts, a_few_solutions)
    solver.SearchForAllSolutions(model, solution_printer)

    # Statistics.
    print()
    print('Statistics')
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - wall time       : %f s' % solver.WallTime())
    print('  - solutions found : %i' % solution_printer.solution_count())
