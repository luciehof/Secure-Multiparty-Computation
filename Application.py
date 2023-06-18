import time
from multiprocessing import Process, Queue
from expression import Scalar, Secret
from protocol import ProtocolSpec
from server import run

from smc_party import SMCParty

def smc_client(client_id, prot, value_dict, queue):
    cli = SMCParty(
        client_id,
        "localhost",
        5000,
        protocol_spec=prot,
        value_dict=value_dict
    )
    res = cli.run()
    queue.put(res)
    print(f"{client_id} has finished!")


def smc_server(args):
    run("localhost", 5000, args)


def run_processes(server_args, *client_args):
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

    for _ in clients:
        results.append(queue.get())

    server.terminate()
    server.join()

    # To "ensure" the workers are dead.
    time.sleep(2)

    print("Server stopped.")

    return results

def suite(parties, expr, expected):
    participants = list(parties.keys())

    prot = ProtocolSpec(expr=expr, participant_ids=participants)
    clients = [(name, prot, value_dict) for name, value_dict in parties.items()]

    results =  run_processes(participants, *clients)

    for result in results:
        assert result == expected

    return results[0]

def main():
    h1_nb_patients = Secret()
    h2_nb_patients = Secret()
    h3_nb_patients = Secret()
    h1_avg_time = Secret()
    h2_avg_time = Secret()
    h3_avg_time = Secret()

    parties = {
        "H1": {h1_nb_patients: 1500, h1_avg_time: 3},
        "H2": {h2_nb_patients: 2000, h2_avg_time: 4},
        "H3": {h3_nb_patients: 800, h3_avg_time: 3}
    }

    total_patients = (h1_nb_patients + h2_nb_patients + h3_nb_patients)
    expected1 = 1500 + 2000 + 800
    day_cost = Scalar(1500)
    reimbursement = Scalar(200)
    total_cost = (h1_nb_patients*h1_avg_time + h2_nb_patients*h2_avg_time + h3_nb_patients*h3_avg_time) * day_cost - reimbursement
    expected2 = (1500*3 + 2000*4 + 800*3) * 1500 - 200
    res1 = suite(parties, total_patients, expected1)
    res2 = suite(parties, total_cost, expected2)

    avg_net_cost = res2/res1

    print("Average patient cost: "+str(avg_net_cost))

if __name__ == "__main__":
    main()