from __future__ import print_function

from datetime import date

import pandas as pd
from django.db import connection
from django.db.models import Q
from django.shortcuts import render, redirect

from inventory.forms import MaterialRequisition
from inventory.forms import MaterialRequisitionForm
from sales.models import ClientItem, SalesInvoice
from utilities import final_gantt
from .forms import ExtruderScheduleForm, PrintingScheduleForm, CuttingScheduleForm, LaminatingScheduleForm
from .forms import JODetailsForm
from .models import JobOrder, ExtruderSchedule, PrintingSchedule, CuttingSchedule, LaminatingSchedule
from .models import Machine
from plotly.offline import plot
from plotly.graph_objs import Scatter

# scheduling import
# Import Python wrapper for or-tools constraint solver.

#from ortools.constraint_solver import pywrapcp


# Create your views here.
def production_details(request):
    context = {
        'title': 'Production Content'
    }

    return render(request, 'production/production_details.html', context)


'''
arrange_schedule() is the function built for the Scheduling system

3 Major Constraints
1. No task for a job can be started until the previous task for that job is completed.
2. A machine can only work on one task at a time.
3. A task, once started, must run to completion.
    - This means that if a task is already running, said task will not adjust for new inputs.

Input = ""
    TODO Machine assignmet, Duration between now() and deadline, filter jobs that are now() - n hours
Output = Updated schedule

2 Levels

Level 1 Solution
Output has minimized production length. Meaning that it takes the minimum amount of time to finish all ongoing jobs.

Level 2 Solution
Input can accept deadlines.

  -Jobs must start after given release dates and be completed before given deadlines

#TODO fix arrange_schedule() to take in 2 parameters (2 2D Lists) based from actual data. Also take note of machine and job count
def arrange_schedule():
  # Create the solver.
  solver = ortools.constraint_solver.pywrapcp.Solver('jobshop')

  machines_count = 3
  jobs_count = 3
  all_machines = range(0, machines_count)
  all_jobs = range(0, jobs_count)


  # Define data. In this case should be input from a function
  machines = [[0, 1, 2],
              [0, 2, 1],
              [1, 2]]

  processing_times = [[3, 2, 2],
                      [2, 1, 4],
                      [4, 3]]

#   This example means
 #  Job n = [(m,p] where m = machine number; p = units of time
  # job 0 = [(0, 3), (1, 2), (2, 2)]
   #job 1 = [(0, 2), (2, 1), (1, 4)]
   #job 2 = [(1, 4), (2, 3)]
   
   #note: each machine and processing time must have a corresponding array
     #    The array machines contains the first entries of the pairs of numbers, while processing_times contains the second entries.
         
    #Issue: machines and processing times are the main input. For each phase in bigapple production, a task can only be done in certain machines.
    #A task production length must also be predefined.
   
  # Computes horizon.
  horizon = 0
  for i in all_jobs:
    horizon += sum(processing_times[i])


  # Creates jobs.
  all_tasks = {}
  for i in all_jobs:
    for j in range(0, len(machines[i])):
      all_tasks[(i, j)] = solver.FixedDurationIntervalVar(0,
                                                          horizon,
                                                          processing_times[i][j],
                                                          False,
                                                          'Job_%i_%i' % (i, j))

  #FixedDurationIntervalVar method creates all_tasks, an array containing the variables for the time interval of each task
  #where i = start time; j = end time
  

  # Creates sequence variables and add disjunctive constraints.
  all_sequences = []
  all_machines_jobs = []
  for i in all_machines:

    machines_jobs = []
    for j in all_jobs:
      for k in range(0, len(machines[j])):
        if machines[j][k] == i:
          machines_jobs.append(all_tasks[(j, k)])
    disj = solver.DisjunctiveConstraint(machines_jobs, 'machine %i' % i)
    all_sequences.append(disj.SequenceVar())
    solver.Add(disj)

   # DisjunctiveConstraints method creates the disjunctive constraints for the problem, and add them to the solver. 
  #  These prevent tasks for the same machine from overlapping in time.
  
  # Add conjunctive contraints.
  for i in all_jobs:
    for j in range(0, len(machines[i]) - 1):
      solver.Add(all_tasks[(i, j + 1)].StartsAfterEnd(all_tasks[(i, j)]))


#    The program then adds the conjunctive constraints, which prevent consecutive tasks for the same job from overlapping in time:
    
 #   For each job, this forces the start time of task j + 1 to occur later than the end time of task j.
  
  # Set the objective.
  obj_var = solver.Max([all_tasks[(i, len(machines[i])-1)].EndExpr()
                        for i in all_jobs])
  objective_monitor = solver.Minimize(obj_var, 1)

#  The expression all_tasks[(i, len(machines[i])-1)].EndExpr() returns the end time for the last task on machine i.
 # By definition, the length of a solution is the maximum of these end times over all all machines. The code above sets the objective for the problem to be this maximum value.
  
  # Create search phases.
  sequence_phase = solver.Phase([all_sequences[i] for i in all_machines],
                                solver.SEQUENCE_DEFAULT)
  vars_phase = solver.Phase([obj_var],
                            solver.CHOOSE_FIRST_UNBOUND,
                            solver.ASSIGN_MIN_VALUE)
  main_phase = solver.Compose([sequence_phase, vars_phase])


  #Creates decision builders. Decision builders create the search tree and determines the order in which the solver searches solutions.
  #The following code creates the decision builder using the solver's Phase method. 
  #(The reason for the term "phase" is that in more complicated problems, the search can involve multiple phases, each of which employs different techniques for finding solutions.)
  
  #phases commonly has two parameters:
 # 1.  Decision variables — the variables the solver uses to decide which node of the tree to visit next.
#  2.  Specifies how the solver chooses the next variable for the search.

  # Create the solution collector.
  collector = solver.LastSolutionCollector()

  # Add the interesting variables to the SolutionCollector.
  collector.Add(all_sequences)
  collector.AddObjective(obj_var)

  # initalize 2D list
  machine_schedule_start_times = []
  machine_schedule_end_times = []
  jobs = []
  tasks = []

  # set 2D list size
  for i in all_machines:
    machine_schedule_start_times.append([])
    machine_schedule_end_times.append([])
    jobs.append([])
    tasks.append([])

  count = 0
  data_count = 0
  # MACHINES
  for i in all_machines:
    sequence = all_sequences[i];
    sequence_count = sequence.Size();
    for j in range(0, sequence_count):
      t = sequence.Interval(j)
      collector.Add(t.StartExpr().Var())
      collector.Add(t.EndExpr().Var())

    
    #Stores the the optimal schedule, including the begin and end times for each task, and the value of the objective function.
    
    #The solution collector stores the values of the start time and end time for each task as t.StartExpr() and t.EndExpr(), respectively
    

  # Solve the problem.
  disp_col_width = 10
  if solver.Solve(main_phase, [objective_monitor, collector]):
    print("\nOptimal Schedule Length to finish all jobs:", collector.ObjectiveValue(0), "hours\n")
    sol_line = ""
    sol_line_tasks = ""
    print("Optimal Schedule", "\n")
    print("Job_i_j represents the jth task for job i", "\n")



    for i in all_machines:
      seq = all_sequences[i]
      sol_line += "Machine " + str(i) + ": "
      sol_line_tasks += "Machine " + str(i) + ": "
      sequence = collector.ForwardSequence(0, seq)
      seq_size = len(sequence)



      #JOBS AND TASKS
      for j in range(0, seq_size):
        t = seq.Interval(sequence[j]);
         # Add spaces to output to align columns.
        sol_line_tasks +=  t.Name() + " " * (disp_col_width - len(t.Name()))

        s = t.Name()

        print("This is task set " + str(count) + " for machine " + str(i))
        print("Job : " + str(s[4]) + " - ")
        print("Task : " + str(s[6]) + " - \n")

        jobs[count].append(str(s[4]))
        tasks[count].append(str(s[6]))

        data_count += 1

        
        #^ this code calls the solver and prints out the optimal schedule length and task order
        
        #The optimal schedule is displayed for each machine, where Job_i_j represents the jth task for job i.
        
      #TIME SCHEDULES
      for j in range(0, seq_size):
        t = seq.Interval(sequence[j]);
        sol_tmp = "[" + str(collector.Value(0, t.StartExpr().Var())) + ","
        sol_tmp += str(collector.Value(0, t.EndExpr().Var())) + "] "

        #converted to string >>> Time Intervals
        print("\n This is time set " + str(count) + " for machine " + str(i))
        #print(str(collector.Value(0, t.StartExpr().Var())) + " - " )
        #print(str(collector.Value(0, t.EndExpr().Var())) + " - \n")
        start_val = collector.Value(0, t.StartExpr().Var())
        end_val = collector.Value(0, t.EndExpr().Var())
        start_time = dt.now()+ td(hours = start_val)
        end_time = dt.now() + td(hours = end_val)
        print ("Start time : " + str(start_time))
        print ("End time : " +  str(end_time))
        print ("Duration of task : " + str(end_val-start_val) + " hours")


        machine_schedule_start_times[count].append(start_time)
        machine_schedule_end_times[count].append(end_time)


        # Add spaces to output to align columns.
        sol_line += sol_tmp + " " * (disp_col_width - len(sol_tmp))



      sol_line += "\n"
      sol_line_tasks += "\n"

      print(sol_line_tasks) #Jobs and tasks
      print("Time Intervals for Tasks\n")
      print("Machine n: [start time,end time]\n")
      print(sol_line) # Time intervals

      count += 1

    gantt_chart_dict = []
    loop_count = 0
    print("TEST>>>>>>>>>>>>>>>>>>>>>>>>")
    print (str(len(all_machines)))
    print ("Count = " + str(count))
    for i in range(count):
      print("\n\nMachine : " + str(i))
      for j in range (len(tasks[i])):
        print("Job : " + str(jobs[i][j]))
        print("Tasks : " + str(tasks[i][j]))
        print("START: " + str(machine_schedule_start_times[i][j]) + "| END : "  + str(machine_schedule_end_times[i][j]))


        task = ""
        if str(tasks[i][j]) == "0":
          task = "Extrusion"
        elif str(tasks[i][j]) == "1":
          task = "Printing"
        else:
          task = "Cutting"


        data_list = {"Task" : str("Machine " + str(i)),
                     "Start" : str(machine_schedule_start_times[i][j]),
                     "Finish" :  str(machine_schedule_end_times[i][j]),
                     "Resource" : str("Job Order : " + str(jobs[i][j]) + "| Task : " +  task)}
        gantt_chart_dict.append(data_list)
        loop_count += 1


    #GENERATE GANTT CHART

    df = gantt_chart_dict
       [   dict(Task="Job A", Start='2009-01-01', Finish='2009-02-28'),
          dict(Task="Job B", Start='2009-03-05', Finish='2009-04-15'),
          dict(Task="Job C", Start='2009-02-20', Finish='2009-05-30') ]


    title = str("Production Schedule as of " + str(dt.now().strftime('%b %d, %Y at %I:%M %p')))
    fig = ff.create_gantt(df, title=title, group_tasks=True, show_colorbar=True, showgrid_x=True, showgrid_y=True, index_col='Resource')
    div_next = opy.plot(fig, auto_open=False, output_type='div')

    return div_next

  if __name__ == '__arrange_schedule__':
    arrange_schedule()


#TODO Add scheduling values lists.
#TODO convert to now() + deltatime (scheduling time values)
#TODO gray area >>> How to adjust durations? hint: not all start times are now()
def production_schedule(request):
  div_next = arrange_schedule()

  x = [-2, 0, 4, 6, 7]
  y = [q ** 2 - q + 3 for q in x]
  trace1 = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104, 'size': 10},
                      mode="lines", name='1st Trace')

  data = go.Data([trace1])
  layout = go.Layout(title="Meine Daten", xaxis={'title': 'x1'}, yaxis={'title': 'x2'})
  figure = go.Figure(data=data, layout=layout)
  div = opy.plot(figure, auto_open=False, output_type='div')
  

  div = ""

  context = {'graph': div, 'graph_next' : div_next}


  return render(request, 'production/production_schedule.html', context)

'''

def job_order_list(request):
    data = JobOrder.objects.exclude(status='Waiting').exclude(status='Ready for Delivery').exclude(status='Delivered')
    items = ClientItem.objects.filter(client_po=data)

    if request.session['session_position'] == "General Manager":
        template = 'general_manager_page_ui.html'
    elif request.session['session_position'] == "Production Manager":
        template = 'production_manager_page_ui.html'
    else:
        template = 'line_leader_page_ui.html'
    context = {
        'items': items,
        'title': 'Job Order List',
        'data' : data,
        'template' : template
    }
    return render (request, 'production/job_order_list.html', context)

def job_order_details(request, id):
		
    data = JobOrder.objects.get(id=id)
    items = ClientItem.objects.filter(client_po=data)
    form = JODetailsForm(request.POST or None)
    extrusion = ExtruderSchedule.objects.filter(job_order=data.id).order_by('datetime_in')
    printing = PrintingSchedule.objects.filter(job_order=data.id).order_by('datetime_in')
    cutting = CuttingSchedule.objects.filter(job_order=data.id).order_by('datetime_in')
    laminating = LaminatingSchedule.objects.filter(job_order=data.id).order_by('datetime_in')

    if request.method == 'POST':
      data.remarks = request.POST.get("remarks")
      data.save()

      return redirect('joborder:job_order_details', id = data.id)
        
    form.fields["remarks"].initial = data.remarks

    context = {
      'form': form,
      'title' : data.job_order,
      'data': data,
      'extrusion': extrusion,
      'printing': printing,
      'cutting': cutting,
      'laminating' : laminating,
      'items' : items
    }
    return render(request, 'production/job_order_details.html', context)

def finished_job_order_list_view(request):
    object_list = JobOrder.objects.filter(status='Ready for delivery' or 'Delivered')
    invoice = SalesInvoice.objects.all()

    for x in object_list:
        if request.method == "POST":
            x.status = "Delivered"
            x.save()

    context = {
        'object_list': object_list,
        'invoice' : invoice
    }

    return render(request, 'production/finished_job_order_list.html', context)

# EXTRUDER 
def add_extruder_schedule(request, id):
		
    data = JobOrder.objects.get(id=id)
    e = ExtruderSchedule.objects.filter(job_order = id)
    e.job_order = id
    items = ClientItem.objects.filter(client_po = data)
    printed = False
    for y in items:
        if y.printed == 1:
            printed == True
            break

    if e.count == 0:
        data.status = 'Under Extrusion'
        data.save()

    form = ExtruderScheduleForm(request.POST)

    if request.method == 'POST':
        data.status = 'Under Extrusion'
        data.save()
        print(form)
        if form.is_valid():
            x = request.POST.get("weight_rolls")
            y = float(x)*float(4.74)
            form.balance = float(y)
            print(form.balance)
            new_schedule = form.save()
            if new_schedule.final:
                if printed:
                    data.status = 'Under Printing'
                    data.save()
                else:
                    data.status = 'Under Cutting'
                    data.save()
        return redirect('production:job_order_details', id = id)

    form.fields["machine"].queryset = Machine.objects.filter(machine_type='Extruder')

    context = {
      'data': data,
      'form': form,
      'id' : id
    }
    
    return render (request, 'production/add_extruder_schedule.html', context)

# PRINTING
def add_printing_schedule(request, id):
		
    data = JobOrder.objects.get(id=id)
    form = PrintingScheduleForm(request.POST)
    p = PrintingSchedule.objects.filter(job_order = data.id)
    p.job_order = id
    items = ClientItem.objects.filter(client_po = id)
    laminate = False
    for x in items:
        if x.laminate == 1:
            laminate = True
            break

    if p.count == 0:
        data.status = 'Under Printing'
        data.save()
		
    print(form.errors)
    if request.method == 'POST':
      data.status = 'Under Printing'
      data.save()
      if form.is_valid():
          new_schedule = form.save()
          if new_schedule.final:
              if laminate:
                data.status = 'Under Laminating'
                data.save()
              else:
                data.status = 'Under Cutting'
                data.save()
      return redirect('production:job_order_details', id = data.id)

    form.fields["machine"].queryset = Machine.objects.filter(machine_type='Printing')
    
    context = {
      'data': data,
      'form': form,
        'id': id
    }
    
    return render (request, 'production/add_printing_schedule.html', context)

# CUTTING
def add_cutting_schedule(request, id):
    data = JobOrder.objects.get(id=id)
    form = CuttingScheduleForm(request.POST)
    invoice = SalesInvoice.objects.get(client_po = data)
    client = data.client

    c = CuttingSchedule.objects.filter(job_order = data.id)
    c.job_order = id

    if c.count == 0:
        data.status = 'Under Cutting'
        data.save()
		
    print(form.errors)
    if request.method == 'POST':
      data.status = 'Under Cutting'
      data.save()
      if form.is_valid():
        new_schedule = form.save()
        if new_schedule.final:
            data.status = 'Ready for delivery'
            data.save()
            invoice.date_issued = date.today()
            invoice.date_due = invoice.calculate_date_due()
            invoice.save()

            client.outstanding_balance += invoice.total_amount_computed
            client.save()
        return redirect('production:job_order_details', id = data.id)

    form.fields["machine"].queryset = Machine.objects.filter(machine_type='Cutting')
    
    context = {
      'data': data,
      'form': form,
        'id' : id
    }
    
    return render (request, 'production/add_cutting_schedule.html', context)


def add_laminating_schedule(request, id):
    data = JobOrder.objects.get(id=id)
    form = LaminatingScheduleForm(request.POST)

    l = LaminatingSchedule.objects.filter(job_order=data.id)
    l.job_order = id

    if l.count == 0:
        data.status = 'Under Laminating'
        data.save()

    print(form.errors)
    if request.method == 'POST':
        data.status = 'Under Laminating'
        data.save()
        if form.is_valid():
            new_schedule = form.save()
            if new_schedule.final:
                data.status = 'Under Cutting'
                data.save()
        return redirect('production:job_order_details', id=data.id)

    form.fields["machine"].queryset = Machine.objects.filter(machine_type='Laminating')

    context = {
        'data': data,
        'form': form,
        'id' : id
    }

    return render(request, 'production/add_laminating_schedule.html', context)
# JO approval 
def jo_approval(request, id):

    jo_id = JobOrder.objects.get(id=id)
    client_po = JobOrder.objects.get(id = jo_id.client_po.id)
    client_po.status = 'Approved'
    client_po.save()
    jo_id.status = "On Queue"
    jo_id.save()

    client_items = ClientItem.objects.filter(client_po = jo_id.client_po.id)
    
    #forms
    form = MaterialRequisitionForm

    print("JO:" ,jo_id)
    print("Client PO:" ,jo_id.client_po.id)

    #variables
    HDPE = 0
    PP = 0
    PET = 0
    LDPE = 0
    LLDPE = 0
    
    for data in client_items:
        print(data.material_type, data.quantity)

        if data.products.material_type == "HDPE":
            #rm for HDPE ratio 3:2:1
            q = data.quantity
            x = (q/100)/6
            HDPE+= x*3
            PP+= x*2  
            PET+= x*1

        elif data.products.material_type == "PP":
            q = data.quantity
            x= (q/100)/6
            PP+= x*3
            PET+= x*2  
            HDPE+= x*1

        elif data.products.material_type == "LDPE":
            q = data.quantity
            x= (q/100)/6
            LDPE+= x*3
            LLDPE+= x*2  
            HDPE+= x*1

    print(LDPE, HDPE, PP, PET, LLDPE)

    MaterialRequisition.objects.create(jo = jo_id)
    mr_id = MaterialRequisition.objects.last() 


    if LDPE != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "LDPE", quantity = LDPE)
    if HDPE != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "HDPE", quantity = HDPE)
    if PP != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "PP", quantity = PP)
    if PET != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "PET", quantity = PET)
    if LLDPE != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "LLDPE", quantity = LLDPE)

    return redirect('production:job_order_details', id = jo_id.id)

#SCHEDULING
def production_schedule(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status="+"'Waiting'"+" and NOT j.status="+"'Ready for delivery'"+" and NOT j.status ="+"'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    final_gantt.generate_overview_gantt_chart(df)

    context = {
        'final_gantt': final_gantt.generate_overview_gantt_chart(df)
    }

    return render(request, 'production/production_schedule.html', context)

def extruder_machine_schedule(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status="+"'Waiting'"+" and NOT j.status="+"'Ready for delivery'"+" and NOT j.status ="+"'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    machines = Machine.objects.filter(machine_type='Extruder').values('machine_id')

    extruder_gantt = final_gantt.generate_specific_gantt_chart(df, machines, machine_type='Extruder')

    context = {
        'extruder_gantt': extruder_gantt
    }

    return render(request, 'production/extruder_machine_schedule.html', context)

def printing_machine_schedule(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status="+"'Waiting'"+" and NOT j.status="+"'Ready for delivery'"+" and NOT j.status ="+"'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    machines = Machine.objects.filter(machine_type='Printing').values('machine_id')

    printing_gantt = final_gantt.generate_specific_gantt_chart(df, machines, machine_type='Printing')

    context = {
        'printing_gantt': printing_gantt
    }

    return render(request, 'production/printing_machine_schedule.html', context)

def laminating_machine_schedule(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status="+"'Waiting'"+" and NOT j.status="+"'Ready for delivery'"+" and NOT j.status ="+"'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    machines = Machine.objects.filter(machine_type='Laminating').values('machine_id')

    laminating_gantt = final_gantt.generate_specific_gantt_chart(df, machines, machine_type='Laminating')

    context = {
        'laminating_gantt': laminating_gantt
    }

    return render(request, 'production/laminating_machine_schedule.html', context)

def cutting_machine_schedule(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status="+"'Waiting'"+" and NOT j.status="+"'Ready for delivery'"+" and NOT j.status ="+"'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    machines = Machine.objects.filter(machine_type='Cutting').values('machine_id')

    cutting_gantt = final_gantt.generate_specific_gantt_chart(df, machines, machine_type='Cutting')

    context = {
        'cutting_gantt': cutting_gantt
    }

    return render(request, 'production/cutting_machine_schedule.html', context)