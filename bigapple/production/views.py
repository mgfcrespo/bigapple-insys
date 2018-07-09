from __future__ import print_function
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Machine
from .models import WorkerSchedule
from .models import SalesInvoice


#scheduling import
# Import Python wrapper for or-tools constraint solver.
from ortools.constraint_solver import pywrapcp
from datetime import timedelta

'''
import plotly
plotly.offline.init_notebook_mode(connected=True)
import plotly.offline as py
import plotly.plotly as py
import plotly.figure_factory as ff
'''

# Create your views here.
def production_details(request):
    context = {
        'title': 'Production Content'
    }

    return render(request, 'production/production_details.html', context)

def generate_gantt_chart():
  ...

def machines_data():
  ...

def processing_times_data():
  ...

def deadlines_data():
  ...

'''
main() is the function built for the Scheduling system

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
'''

def main():
  # Create the solver.
  solver = pywrapcp.Solver('jobshop')

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

  deadlines = []

  '''
   This example means
   Job n = [(m,p] where m = machine number; p = units of time
   job 0 = [(0, 3), (1, 2), (2, 2)]
   job 1 = [(0, 2), (2, 1), (1, 4)]
   job 2 = [(1, 4), (2, 3)]
   
   note: each machine and processing time must have a corresponding array
         The array machines contains the first entries of the pairs of numbers, while processing_times contains the second entries.
         
    Issue: machines and processing times are the main input. For each phase in bigapple production, a task can only be done in certain machines.
    A task production length must also be predefined.
   '''

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

  '''
  FixedDurationIntervalVar method creates all_tasks, an array containing the variables for the time interval of each task
  where i = start time; j = end time
  '''

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

    '''
    DisjunctiveConstraints method creates the disjunctive constraints for the problem, and add them to the solver. 
    These prevent tasks for the same machine from overlapping in time.
    '''

  # Add conjunctive contraints.
  for i in all_jobs:
    for j in range(0, len(machines[i]) - 1):
      solver.Add(all_tasks[(i, j + 1)].StartsAfterEnd(all_tasks[(i, j)]))

    '''
    The program then adds the conjunctive constraints, which prevent consecutive tasks for the same job from overlapping in time:
    
    For each job, this forces the start time of task j + 1 to occur later than the end time of task j.
    '''

  # Set the objective.
  obj_var = solver.Max([all_tasks[(i, len(machines[i])-1)].EndExpr()
                        for i in all_jobs])
  objective_monitor = solver.Minimize(obj_var, 1)

  '''
  The expression all_tasks[(i, len(machines[i])-1)].EndExpr() returns the end time for the last task on machine i.
  By definition, the length of a solution is the maximum of these end times over all all machines. The code above sets the objective for the problem to be this maximum value.
  '''

  # Create search phases.
  sequence_phase = solver.Phase([all_sequences[i] for i in all_machines],
                                solver.SEQUENCE_DEFAULT)
  vars_phase = solver.Phase([obj_var],
                            solver.CHOOSE_FIRST_UNBOUND,
                            solver.ASSIGN_MIN_VALUE)
  main_phase = solver.Compose([sequence_phase, vars_phase])

  '''
  Creates decision builders. Decision builders create the search tree and determines the order in which the solver searches solutions.
  The following code creates the decision builder using the solver's Phase method. 
  (The reason for the term "phase" is that in more complicated problems, the search can involve multiple phases, each of which employs different techniques for finding solutions.)
  
  phases commonly has two parameters:
  1.  Decision variables — the variables the solver uses to decide which node of the tree to visit next.
  2.  Specifies how the solver chooses the next variable for the search.
  '''

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

    '''
    Stores the the optimal schedule, including the begin and end times for each task, and the value of the objective function.
    
    The solution collector stores the values of the start time and end time for each task as t.StartExpr() and t.EndExpr(), respectively
    '''

  # Solve the problem.
  disp_col_width = 10
  if solver.Solve(main_phase, [objective_monitor, collector]):
    print("\nOptimal Schedule Length to finish all jobs:", collector.ObjectiveValue(0), "hours\n")
    sol_line = ""
    sol_line_tasks = ""
    print("Optimal Schedule", "\n")

    for i in all_machines:
      seq = all_sequences[i]
      sol_line += "Machine " + str(i) + ": "
      sol_line_tasks += "Machine " + str(i) + ": "
      sequence = collector.ForwardSequence(0, seq)
      seq_size = len(sequence)

      for j in range(0, seq_size):
        t = seq.Interval(sequence[j]);
         # Add spaces to output to align columns.
        sol_line_tasks +=  t.Name() + " " * (disp_col_width - len(t.Name()))


        '''
        ^ this code calls the solver and prints out the optimal schedule length and task order
        '''

      for j in range(0, seq_size):
        t = seq.Interval(sequence[j]);
        sol_tmp = "[" + str(collector.Value(0, t.StartExpr().Var())) + ","
        sol_tmp += str(collector.Value(0, t.EndExpr().Var())) + "] "
        # Add spaces to output to align columns.
        sol_line += sol_tmp + " " * (disp_col_width - len(sol_tmp))

      sol_line += "\n"
      sol_line_tasks += "\n"

    print(sol_line_tasks)
    print("Time Intervals for Tasks\n")
    print(sol_line)

    '''
    ^ this code prints the scheduled time intervals for each task
    '''

if __name__ == '__main__':
  main()


def production_schedule(request):
    main()
    context = {'': ''}
    render(request, 'production/production_schedule.html', context)
