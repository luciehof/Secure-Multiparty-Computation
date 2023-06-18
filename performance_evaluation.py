"""
Integration tests that verify different aspects of the protocol.
You can *add* new tests here, but it is best to  add them to a new test file.
ALL EXISTING TESTS IN THIS SUITE SHOULD PASS WITHOUT ANY MODIFICATION TO THEM.
"""

import statistics
import time
from statistics import mean
from multiprocessing import Process, Queue
import pandas as pd
import pytest

from expression import Expression, Scalar, Secret
from protocol import ProtocolSpec
from server import run
import matplotlib.pyplot as plt
import sys 

# from matplotlib import plot

from smc_party import SMCParty

sys.setrecursionlimit(5000)

### Make a plot of the given csv file
def make_plot(title, csv_file):
    df = pd.read_csv(csv_file)
    df_stat = pd.DataFrame(columns=["Computation Time (in seconds)", "Bytes In", "Bytes Out"])
    
    df = df.set_index("Unnamed: 0")
    fig, axs = plt.subplots(4, sharex=True)
    axs[1].plot(df["Computation Time (in seconds)"], 'tab:orange', label="Computation Time (in seconds)")
    axs[2].plot(df["Bytes In"], 'tab:green', label="Bytes In")
    axs[2].legend()
    axs[3].plot(df["Bytes Out"], 'tab:red', label="Bytes Out")
    axs[3].legend()
    axs[1].legend()
    axs[3].set_xlabel(title)

    df_stat = df_stat.append(pd.Series(df.mean(), name="Mean"))
    df_stat = df_stat.append(pd.Series(df.std(), name="Standard deviation"))
    df_stat = df_stat.round(2)

    values = ["Mean", "Standard deviation"]
    cell_text = []
    for row in range(len(df_stat)):
        txt = list(df_stat.iloc[row][:-1])
        txt.insert(0, values[row])
        cell_text.append(txt)

    # statistics table
    t = axs[0].table(cellText=cell_text, colLabels=["", "Computation Time", "Bytes In", "Bytes Out"], loc="center")
    axs[0].axis("off")
    t.auto_set_font_size(False)
    t.set_fontsize(8)
    t.scale(1, 1.2)

    plt.savefig("perf_eval/" + title + ".png")
    
    plt.close()

## Class handling the performance evaluation for one test suite
class PerformanceEvaluator:
  def __init__(self, title=""):
    self.df = pd.DataFrame(columns=["Computation Time (in seconds)", "Bytes In", "Bytes Out"])
    self.computation_times = []
    self.bytes_in = []
    self.bytes_out = []
    self.title = title

  # Adds the given evaluation results to the list of parties' results 
  def performance_eval_callback(self, client_id, computation_time, bytes_in, bytes_out):
    self.computation_times.append(computation_time)
    self.bytes_in.append(bytes_in)
    self.bytes_out.append(bytes_out)

  # Reset the evaluation for one parameter
  def complete_results(self, id):
    self.df = self.df.append(pd.Series({
      "Computation Time (in seconds)": mean(list(self.computation_times)), 
      "Bytes In": mean(list(self.bytes_in)), 
      "Bytes Out": mean(list(self.bytes_out))
    }, name=str(id)))

    self.df.to_csv(f"perf_eval/{self.title}.csv")
    
    self.computation_times = []
    self.bytes_in = []
    self.bytes_out = []

  def plot_results(self):
    make_plot(self.title, f"perf_eval/{self.title}.csv")


def smc_client(client_id, prot, value_dict, queue):
    cli = SMCParty(
        client_id,
        "localhost",
        5000,
        protocol_spec=prot,
        value_dict=value_dict,
        performance_evaluation=True
    )
    res = cli.run()
    queue.put(res)
    print(f"{client_id} has finished!")


def smc_server(args):
    run("localhost", 5000, args)


def run_processes(server_args, performance_evaluator, *client_args):
    queue = Queue()


    server = Process(target=smc_server, args=(server_args,))
    clients = [Process(target=smc_client, args=(*args, queue)) for args in client_args]

    server.start()
    time.sleep(3)
    for client in clients:
        client.start()

    results = list()
    for client in clients:
        client.join()
        
    for client in clients:
        res = queue.get()
        performance_evaluator.performance_eval_callback("", res[1], res[2], res[3])
        results.append(res[0])

    server.terminate()
    server.join()

    # To "ensure" the workers are dead.
    time.sleep(2)

    print("Server stopped.")

    return results


def suite(parties, expr, expected, performance_evaluator):
    participants = list(parties.keys())

    prot = ProtocolSpec(expr=expr, participant_ids=participants)
    clients = [(name, prot, value_dict) for name, value_dict in parties.items()]

    results = run_processes(participants, performance_evaluator, *clients)

    print(results)


def test_number_additions(perf):
    """
    f(a) = a + b + ... + a + b
    """
    
    num_ops = [10, 100, 500, 1000, 2000, 4000]

    for num_op in num_ops:
      print("----- Performance evaluation for number of additions " + str(num_op))
      secret = Secret()
      secret2 = Secret()
      parties = {}
      expr = secret
      parties["Alice"] = { secret: 5 }
      parties["Bob"] = { secret2: 3 }

      for i in range(num_op):
        expr = expr + (secret if i % 2 == 0 else secret2)

      suite(parties, expr, 0, perf)
      perf.complete_results(num_op)

    perf.plot_results()

def test_number_additions_scalar(perf):
    """
    f(a) = a + b + K0 + ... + K0
    """
    
    num_ops = [10, 100, 500, 1000, 2000, 4000]

    for num_op in num_ops:
      print("----- Performance evaluation for number of scalar additions " + str(num_op))
      secret = Secret()
      secret2 = Secret()
      parties = {}
      expr = secret + secret2
      parties["Alice"] = { secret: 5 }
      parties["Bob"] = { secret2: 4 }

      for i in range(num_op):
        expr = expr + Scalar(5)

      suite(parties, expr, 0, perf)
      perf.complete_results(num_op)

    perf.plot_results()

def test_number_multiplications(perf):
    """
    f(a) = a * b * ... * a * b
    """
    
    num_ops = [10, 100, 500, 1000, 2000, 4000]

    for num_op in num_ops:
      print("----- Performance evaluation for number of multiplications " + str(num_op))
      secret = Secret()
      secret2 = Secret()
      parties = {}
      expr = secret
      parties["Alice"] = { secret: 2 }
      parties["Bob"] = { secret2: 2 }

      for i in range(num_op):
        expr = expr * (secret if i % 2 == 0 else secret2)

      suite(parties, expr, 0, perf)
      perf.complete_results(num_op)

    perf.plot_results()

def test_number_scalar_multiplications(perf):
    """
    f(a) = a * b * K * ... * K
    """
    
    num_ops = [10, 100, 500, 1000, 2000, 4000]

    for num_op in num_ops:
      print("----- Performance evaluation for number of scalar multiplications " + str(num_op))
      secret = Secret()
      secret2 = Secret()
      parties = {}
      expr = secret * secret2
      parties["Alice"] = { secret: 2 }
      parties["Bob"] = { secret2: 2 }

      for i in range(num_op):
        expr = expr * Scalar(2)

      suite(parties, expr, 0, perf)
      perf.complete_results(num_op)

    perf.plot_results()


def test_number_parties(perf):
  """
  f(x1, x2, ..., xn) = x1 + x2 + ... + xn
  """

  num_ops = 1000
  secrets = [Secret() for _ in range(num_ops)]

  num_parties = [1, 10, 25, 50, 75, 100, 125, 150]

  expr = secrets[0]
  for i in range(1, num_ops):
    expr = expr + secrets[i]

  for num_party in num_parties:
    print("----- Performance evaluation for number of parties " + str(num_party))

    parties = {}
    secrets_per_parties = int(num_ops / num_party)

    secret_count = 0
    while secret_count < num_ops:
      idx = str(int(secret_count / secrets_per_parties))
      if idx not in parties.keys():
        parties[idx] = {}
      parties[idx][secrets[secret_count]] = 5
      secret_count += 1

    suite(parties, expr, 0, perf)
    perf.complete_results(num_party)

  perf.plot_results()

    



# test_number_additions(PerformanceEvaluator("Number of additions"))
# test_number_additions_scalar(PerformanceEvaluator("Number of scalar additions"))
# test_number_multiplications(PerformanceEvaluator("Number of multiplications"))
# test_number_scalar_multiplications(PerformanceEvaluator("Number of scalar multiplications"))
# test_number_parties(PerformanceEvaluator("Number of parties"))
make_plot("Number of parties", "perf_eval/Number of parties.csv")
make_plot("Number of additions", "perf_eval/Number of additions.csv")
make_plot("Number of scalar additions", "perf_eval/Number of scalar additions.csv")
make_plot("Number of multiplications", "perf_eval/Number of multiplications.csv")
make_plot("Number of scalar multiplications", "perf_eval/Number of scalar multiplications.csv")

