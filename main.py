
# imported libraries
import os
import matplotlib.pyplot as plt
import networkx as nx
from random import random
from math import floor, exp, log
from itertools import product 
import pickle
import numpy as np
from time import perf_counter

# global variables
n = 10 # number of nodes
k = 3 # max number of colors accepted
p = 0.5
seed = 42
training = True

# Initial heuristic
def initial_coloring(G, k):
    e_c = [] #list of edges that have the same color on both ends, e_c stands for "edges with conflicts", its elements are of the type (u, v, ind_u_in_v, ind_v_in_u)
    nb_of_conflicts = 0 #number of edges that have the same color on both ends
    ordered_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True) #nodes ordered by degree in descending order
    color_map = [None] * len(G.nodes())
    # color_map = np.full(len(G.nodes()), -1, dtype=np.int32)
    neighbors_per_color = [[0 for i in range(k)] for _ in range(len(G.nodes()))] #for each node, count how many neighbors have each color
    # neighbors_per_color = np.zeros(
    # (len(G.nodes()), k),
    # dtype=np.int32
    # )
    a = [[] for i in range(len(G.nodes()))]
    for node in G.nodes():
        a[node] = list(sorted(G.neighbors(node))) 
    adj_list = [[] for i in range(len(G.nodes()))] #complete adjacency list of type (neighbor, l, j) with neighbor, index of edge between node and neighbor if there is a conflict (None otherwise), and with index of node in neighbor's adjacency list

    # construct adj_list
    for node in range(len(G.nodes())):
        for i in range(len(a[node])):
            neighbor = a[node][i]
            adj_list[neighbor].append([node, None, i])

    # assign colors to nodes in descending order of degree
    for node in ordered_nodes:
        c = min(neighbors_per_color[node])
        color_map[node] = neighbors_per_color[node].index(c) # assigned color that minimizes the number of new conflicts
        # color_map[node] = np.argmin(neighbors_per_color[node])
        for i in range(len(adj_list[node])):
            neighbor, l, j = adj_list[node][i]
            neighbors_per_color[neighbor][color_map[node]] += 1
            if color_map[neighbor] == color_map[node]: # neighbor and node are in conflict
                e_c.append((node, neighbor, j, i)) # add edge to conflicting edges with corresponding info
                adj_list[node][i][1] = len(e_c) - 1 # position of edge indicated in adj_list[node][index of neighbor]
                adj_list[neighbor][j][1] = len(e_c) - 1 # position of edge indicated in adj_list[neighbor][index of node]

    nb_of_conflicts = len(e_c)
    return color_map, nb_of_conflicts, e_c, adj_list, neighbors_per_color

# draw the colored graph
def draw_colored_graph(G, color_map):
    pos = nx.spring_layout(G, seed=seed)  # Seed for reproducible layout
    nx.draw(G, pos=pos, node_color=color_map, with_labels=True)
    plt.show()

### SMALL GRAPHS
#draw the colored graph step by step by coloring one node at a time in descending order of degree
def draw_colored_graph_step_by_step(G, color_map):
    pos = nx.spring_layout(G, seed=seed)  # Seed for reproducible layout
    ordered_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True) #nodes ordered by degree in descending order
    current_color_map = [None] * len(G.nodes())
    for node in ordered_nodes:
        current_color_map[node] = color_map[node]
        nx.draw(G, pos=pos, node_color=current_color_map, with_labels=True)
        plt.pause(2)  # Pause for 2 seconds to visualize the coloring process
    plt.show()

def example(n, k, p):
    G = nx.erdos_renyi_graph(n, p)
    color_map, nb_of_conflicts, e_c, adj_list, neighbors_per_color = initial_coloring(G, k)
    print("number of conflicts:", nb_of_conflicts)
    draw_colored_graph(G, color_map)
    # draw_colored_graph_step_by_step(G, color_map)

# Draw all unlabeled graphs with n nodes (for n <= 7)
atlas = nx.graph_atlas_g()

def find_best_coloring(G, k): #try all combinations of colors for a graph G, return the coloring with the least number of conflicts
    best_color_map = None
    min_conflicts = float('inf')
    #generate all combinations of colors for the nodes in G
    for color_map in product(range(k), repeat=len(G.nodes())): #this will generate all combinations of colors for the nodes in G
        nb_of_conflicts = 0
        e_c = []
        for edge in G.edges():
            if color_map[edge[0]] == color_map[edge[1]]:
                nb_of_conflicts += 1
                e_c.append(edge)
        if nb_of_conflicts < min_conflicts:
            min_conflicts = nb_of_conflicts
            best_color_map = color_map
    return best_color_map, min_conflicts, e_c

# Color all graphs with n nodes and draw only those that have at least one conflict and are better than the coloring found by f_coloriage
def draw_colored_graphs_with_conflicts(n, k):
    for G in atlas:
        if len(G.nodes()) == n:
            color_map, nb_of_conflicts, e_c, adj_list, neighbors_per_color = initial_coloring(G, k)
            if nb_of_conflicts > 0:
                best_color_map, min_conflicts, e_c_best = find_best_coloring(G, k)
                if nb_of_conflicts > min_conflicts: #only draw graphs that have at least one conflict and are better than the coloring found by f_coloriage
                    print(f"Graph with {n} nodes and {nb_of_conflicts} conflicts:")
                    draw_colored_graph(G, color_map)
                    draw_colored_graph(G, best_color_map)

### END OF SMALL GRAPHS

# read file containing lines "e node1 node2" and return a graph with the edges defined in the file
def read_graph_from_file(filename):
    G = nx.Graph()
    k = None

    with open(filename, "r") as f:
        for line in f:
            if line.startswith("k"):
                _, k = line.split()
                k = int(k)
            elif line.startswith("e"):
                _, node1, node2 = line.split()
                G.add_edge(int(node1) - 1, int(node2) - 1)

    if k == None:
        raise ValueError("Error: did you add 'k value_of_k' at the beginning of the graph file?")
    return G, k

def read_files_from_directory(directory):
    return [
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if filename.endswith(".col")
    ]

def probabilistic_heuristic(graph_name, nb_iter_max, alpha, T0, mu, simulated_annealing, save_callback=None):
    global training
    
    if training:
        initial_values = load_initial_coloring(graph_name)
        current_color_map, current_nb_of_conflicts, e_c, adj_list, neighbors_per_color = initial_values
    else:
        store_initial_colorings("graph_exam", output_directory="output_exam")
        initial_values = load_initial_coloring(graph_name, input_directory="output_exam")
        current_color_map, current_nb_of_conflicts, e_c, adj_list, neighbors_per_color = initial_values
        training = True

    T = T0
    # print(f"Initial number of conflicts is {current_nb_of_conflicts}.")

    history_nb_of_conflicts = [current_nb_of_conflicts]

    iteration_stop = 0
    best_nb_of_conflicts_seen = current_nb_of_conflicts
    iter_best_nb_of_conflicts_seen = 0
    best_color_map = current_color_map.copy()

    # Time measurements
    start_time = perf_counter()
    time_to_best_solution = 0.0

    # Number of evaluated solutions
    solutions_evaluated = 0

    for t in range(nb_iter_max):
        if current_nb_of_conflicts == 0:
            print("There are no conflicts, yay!")
            break

        iteration_stop += 1
        # choose a conflicting edge uniformly at random
        r1 = random()
        r2 = random()
        ind_edge = floor(r1*current_nb_of_conflicts)
        if 2*r2 > 1:
            neighbor, node, ind_neighbor_in_node, ind_node_in_neighbor = e_c[ind_edge]
        else:
            node, neighbor, ind_node_in_neighbor, ind_neighbor_in_node = e_c[ind_edge]

        row = neighbors_per_color[node]
        m = min(row)
        M = max(row)
        upper_bound = m + alpha * M

        # candidate_colors = np.flatnonzero(row <= upper_bound)
        # color_candidate = int(
        #     candidate_colors[np.random.randint(len(candidate_colors))]
        # )

        solutions_evaluated += 1
        nb_candidates = 0
        for color in range(len(neighbors_per_color[node])):
            if neighbors_per_color[node][color] <= upper_bound:
                nb_candidates += 1

        r3 = random()
        ind_new_color = floor(r3*nb_candidates)

        color_counter = 0
        color_candidate = 0
        for color in range(len(neighbors_per_color[node])):

            if neighbors_per_color[node][color] <= upper_bound:
                if ind_new_color == color_counter:
                    color_candidate = color
                    break
                color_counter += 1

        if simulated_annealing:
            delta = (
                neighbors_per_color[node][color_candidate]
                - neighbors_per_color[node][current_color_map[node]]
            )

            if delta > 0:
                limit = exp(-delta / T)

                if random() > limit:
                    T *= mu
                    history_nb_of_conflicts.append(current_nb_of_conflicts)
                    continue

        T *= mu
        old_color = current_color_map[node]
        new_color = color_candidate

        if old_color == new_color:
            history_nb_of_conflicts.append(len(e_c))
            continue

        current_color_map[node] = new_color
        for i in range(len(adj_list[node])):
            v, l, j = adj_list[node][i]
            neighbors_per_color[v][new_color] += 1
            neighbors_per_color[v][old_color] -= 1

            # print(f"value of l is {l}.")
            if current_color_map[v] == old_color:
                x, y, ind_x_in_y, ind_y_in_x = e_c[len(e_c)-1]
                
                if l == len(e_c)-1:
                    e_c.pop()
                else:
                    e_c[l], e_c[len(e_c)-1] = e_c[len(e_c)-1], e_c[l]
                    e_c.pop()
                    u, w, ind_u_in_w, ind_w_in_u = e_c[l]
                    adj_list[u][ind_w_in_u][1] = l
                    adj_list[w][ind_u_in_w][1] = l
                adj_list[node][i][1] = None
                adj_list[v][j][1] = None

            if current_color_map[v] == new_color:
                e_c.append((v, node, i, j))
                # print(f"v is {v}, j is {j}, node is {node}")
                adj_list[v][j][1] = len(e_c) - 1
                adj_list[node][i][1] = len(e_c) - 1

        current_nb_of_conflicts = len(e_c)
        if current_nb_of_conflicts < best_nb_of_conflicts_seen:
            best_nb_of_conflicts_seen = current_nb_of_conflicts
            iter_best_nb_of_conflicts_seen = t

            best_color_map = current_color_map.copy()
            time_to_best_solution = perf_counter() - start_time
            # Notify the caller of every new best so it can persist it live
            if save_callback is not None:
                save_callback(best_nb_of_conflicts_seen, best_color_map)
        history_nb_of_conflicts.append(current_nb_of_conflicts)
        # print(f"Current number of conflicts is {current_nb_of_conflicts} after {t} iterations.")

    # Total optimization time
    total_time = perf_counter() - start_time

    # Conflict statistics
    average_conflicts = np.mean(history_nb_of_conflicts)
    min_conflicts = np.min(history_nb_of_conflicts)
    max_conflicts = np.max(history_nb_of_conflicts)

    # Solutions evaluated per second
    solutions_per_second = (
        solutions_evaluated / total_time if total_time > 0 else 0
    )
    # print(f"Final value of T is {T}")
    return (
    current_nb_of_conflicts,
    best_color_map,
    history_nb_of_conflicts,
    iteration_stop,
    best_nb_of_conflicts_seen,
    iter_best_nb_of_conflicts_seen,
    average_conflicts,
    min_conflicts,
    max_conflicts,
    total_time,
    time_to_best_solution,
    solutions_evaluated,
    solutions_per_second
    )

def draw_evolution_of_conflicts(list_y, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen, alpha_value):
    list_x = [i for i in range(len(list_y))]
    plt.plot(list_x, list_y, label=f"alpha = {alpha_value}")
    plt.scatter(iter_best_nb_of_conflicts_seen, best_nb_of_conflicts_seen, color='red')

    plt.annotate(
    str(best_nb_of_conflicts_seen),
    (iter_best_nb_of_conflicts_seen, best_nb_of_conflicts_seen),
    xytext=(10, 5),
    textcoords="offset points",
    color="red",
    fontsize=12,
    fontweight="bold"
    )

    return

def find_best_alpha(graph_name, iterations, T0, mu, simulated_annealing):
    # alpha_values = [0, 0.05, 0.1, 0.15, 0.2]
    alpha_values = [0, 0.01, 0.05, 0.1]
    lists_of_conflicts_alphas = []
    for alpha in alpha_values:
        (
            nb_of_conflicts,
            color_map,
            history_nb_of_conflicts,
            iteration_stop,
            best_nb_of_conflicts_seen,
            iter_best_nb_of_conflicts_seen,
            average_conflicts,
            min_conflicts,
            max_conflicts,
            total_time,
            time_to_best_solution,
            solutions_evaluated,
            solutions_per_second
        ) = probabilistic_heuristic(
            graph_name, iterations, alpha, T0, mu, simulated_annealing
        )
        lists_of_conflicts_alphas.append([history_nb_of_conflicts, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen])
        draw_evolution_of_conflicts(history_nb_of_conflicts, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen, alpha)

    plt.legend()
    plt.show()
    return


#### FIND BEST PARAMETERS

def draw_evolution_of_conflicts_large(
    ax,
    list_y,
    best_nb_of_conflicts_seen,
    iter_best_nb_of_conflicts_seen,
    alpha_value
):
    list_x = range(len(list_y))

    ax.plot(list_x, list_y, label=f"alpha = {alpha_value}")

    ax.scatter(
        iter_best_nb_of_conflicts_seen,
        best_nb_of_conflicts_seen,
        color="red",
        zorder=5
    )

    ax.annotate(
        str(best_nb_of_conflicts_seen),
        (iter_best_nb_of_conflicts_seen, best_nb_of_conflicts_seen),
        xytext=(10, 5),
        textcoords="offset points",
        color="red",
        fontsize=9,
        fontweight="bold"
    )

# def find_best_T0_and_mu(graph_name, iterations, simulated_annealing=True):

#     T0_values = [100, 1000, 10000]       # À adapter
#     mu_values = [0.999, 0.9995, 0.9999]  # À adapter
#     alpha_values = [0, 0.1, 0.15]

#     fig, axes = plt.subplots(
#         len(T0_values),
#         len(mu_values),
#         figsize=(15, 12),
#         sharex=True,
#         sharey=True
#     )

#     for i, T0 in enumerate(T0_values):
#         for j, mu in enumerate(mu_values):

#             ax = axes[i, j]

#             for alpha in alpha_values:
#                 (
#                     nb_of_conflicts,
#                     color_map,
#                     history_nb_of_conflicts,
#                     iteration_stop,
#                     best_nb_of_conflicts_seen,
#                     iter_best_nb_of_conflicts_seen,
#                     average_conflicts,
#                     min_conflicts,
#                     max_conflicts,
#                     total_time,
#                     time_to_best_solution,
#                     solutions_evaluated,
#                     solutions_per_second
#                 ) = probabilistic_heuristic(
#                     graph_name, iterations, alpha, T0, mu, simulated_annealing
#                 )

#                 draw_evolution_of_conflicts(
#                     ax,
#                     history_nb_of_conflicts,
#                     best_nb_of_conflicts_seen,
#                     iter_best_nb_of_conflicts_seen,
#                     alpha
#                 )

#             ax.set_title(f"T0 = {T0}, mu = {mu}")
#             ax.grid(True, alpha=0.3)

#     fig.supxlabel("Itération")
#     fig.supylabel("Nombre de conflits")
#     fig.suptitle("Influence de T0 et mu pour différentes valeurs de alpha")

#     # Une légende commune aux 9 graphiques
#     handles, labels = axes[0, 0].get_legend_handles_labels()
#     fig.legend(handles, labels, loc="upper center",
#                ncol=len(alpha_values), bbox_to_anchor=(0.5, 0.96))

#     plt.tight_layout(rect=[0, 0, 1, 0.92])
#     plt.show()

def coloring_from_file(
    filename_source,
    filename_dest,
    nb_iter_max,
    alpha,
    T0,
    mu,
    simulated_annealing,
):
    # G, k = read_graph_from_file(filename_source)
    graph_name = os.path.splitext(os.path.basename(filename_source))[0]
    (
    current_nb_of_conflicts,
    best_color_map,
    history_nb_of_conflicts,
    iteration_stop,
    best_nb_of_conflicts_seen,
    iter_best_nb_of_conflicts_seen,
    average_conflicts,
    min_conflicts,
    max_conflicts,
    total_time,
    time_to_best_solution,
    solutions_evaluated,
    solutions_per_second
    ) = probabilistic_heuristic(
        graph_name, nb_iter_max, alpha, T0, mu, simulated_annealing
    )

    # Save results for this parameter combination
    with open(filename_dest, "w") as f:
        f.write(f"graph = {os.path.basename(filename_source)}\n")
        f.write(f"nb_iter_max = {nb_iter_max}\n")
        f.write(f"alpha = {alpha}\n")
        f.write(f"T0 = {T0}\n")
        f.write(f"mu = {mu}\n")
        f.write(f"simulated_annealing = {simulated_annealing}\n")
        f.write(
            f"best_nb_of_conflicts_seen = {best_nb_of_conflicts_seen}\n"
        )
        f.write(f"best_color_map = {best_color_map}\n")

        f.write("\n--- Performance Statistics ---\n")

        f.write(f"Average conflicts = {average_conflicts:.4f}\n")
        f.write(f"Minimum conflicts = {min_conflicts}\n")
        f.write(f"Maximum conflicts = {max_conflicts}\n")

        f.write(f"Total coloring time (seconds) = {total_time:.6f}\n")
        f.write(f"Time to best solution (seconds) = {time_to_best_solution:.6f}\n")

        f.write(f"Solutions evaluated = {solutions_evaluated}\n")
        f.write(f"Solutions evaluated per second = {solutions_per_second:.4f}\n")

    # Return results so the caller can compare parameter combinations
    return (
        best_nb_of_conflicts_seen,
        best_color_map,
        average_conflicts,
        min_conflicts,
        max_conflicts,
        total_time,
        time_to_best_solution,
        solutions_per_second
    )

def run_on_directory(
    directory,
    output_directory,
    nb_iter_max_list,
    alpha_list,
    T0_list,
    mu_list,
    simulated_annealing_list,
):
    files = read_files_from_directory(directory)
    all_best_results = []
    for filename_source in files:
        # One folder per graph
        graph_name = os.path.splitext(
            os.path.basename(filename_source)
        )[0]

        graph_folder = os.path.join(output_directory, graph_name)
        os.makedirs(graph_folder, exist_ok=True)

        # Track the best result for this graph across all parameters
        best_overall_conflicts = None
        best_overall_color_map = None
        best_overall_parameters = None

        for (
            nb_iter_max,
            alpha,
            T0,
            mu,
            simulated_annealing,
        ) in product(
            nb_iter_max_list,
            alpha_list,
            T0_list,
            mu_list,
            simulated_annealing_list,
        ):
            # A separate file for each parameter combination
            params_name = (
                f"nb_iter_{nb_iter_max}"
                f"_alpha_{alpha}"
                f"_T0_{T0}"
                f"_mu_{mu}"
                f"_sa_{simulated_annealing}"
            )

            filename_dest = os.path.join(
                graph_folder, f"{params_name}.txt"
            )

            (
                conflicts,
                color_map,
                average_conflicts,
                min_conflicts,
                max_conflicts,
                total_time,
                time_to_best_solution,
                solutions_per_second
            ) = coloring_from_file(
                filename_source,
                filename_dest,
                nb_iter_max,
                alpha,
                T0,
                mu,
                simulated_annealing
            )

            # Update the best result only if it improves the previous best
            if (
                best_overall_conflicts is None
                or conflicts < best_overall_conflicts
            ):
                best_overall_conflicts = conflicts
                best_overall_color_map = color_map

                best_overall_parameters = {
                    "nb_iter_max": nb_iter_max,
                    "alpha": alpha,
                    "T0": T0,
                    "mu": mu,
                    "simulated_annealing": simulated_annealing,
                    "average_conflicts": average_conflicts,
                    "min_conflicts": min_conflicts,
                    "max_conflicts": max_conflicts,
                    "total_time": total_time,
                    "time_to_best_solution": time_to_best_solution,
                    "solutions_per_second": solutions_per_second
                }

        # Write the final summary after testing every parameter combination
        summary_file = os.path.join(
            graph_folder, "best_overall.txt"
        )

        with open(summary_file, "w") as f:
            f.write(f"Graph = {os.path.basename(filename_source)}\n")
            f.write(
                f"Best number of conflicts = {best_overall_conflicts}\n"
            )
            f.write(f"Best color map = {best_overall_color_map}\n")
            f.write("Parameters yielding the best result:\n")

            for name, value in best_overall_parameters.items():
                f.write(f"{name} = {value}\n")

        all_best_results.append((
            graph_name,
            best_overall_conflicts,
            best_overall_parameters
        ))
    summary_file = os.path.join(output_directory, "best_results.txt")

    with open(summary_file, "w") as f:
        f.write(
            "graph best_conflicts nb_iter_max alpha T0 mu "
            "average_conflicts min_conflicts max_conflicts "
            "total_time time_to_best solutions_per_second\n"
        )
        for graph_name, best_conflicts, best_params in all_best_results:
            f.write(
                f"{graph_name} {best_conflicts} "
                f"{best_params['nb_iter_max']} "
                f"{best_params['alpha']} "
                f"{best_params['T0']} "
                f"{best_params['mu']} "
                f"{best_params['average_conflicts']:.4f} "
                f"{best_params['min_conflicts']} "
                f"{best_params['max_conflicts']} "
                f"{best_params['total_time']:.6f} "
                f"{best_params['time_to_best_solution']:.6f} "
                f"{best_params['solutions_per_second']:.4f}\n"
            )
    print("All results saved.")

#### END OF SECTION FIND BEST PARAMETERS

def store_initial_colorings(directory, output_directory="output/initial_colorings"):
    """
    Compute the initial coloring once per graph and store all values
    needed to initialize probabilistic_heuristic.
    """
    os.makedirs(output_directory, exist_ok=True)

    files = read_files_from_directory(directory)

    for filename in files:
        graph_name = os.path.splitext(os.path.basename(filename))[0]
        initial_file = os.path.join(output_directory, f"{graph_name}.pkl")

        # Skip initialization if the file already exists
        if os.path.exists(initial_file):
            continue

        G, k = read_graph_from_file(filename)

        # Replace this call with your actual initialization heuristic
        initial_values = initial_coloring(G, k)

        # Store every value returned by the initialization heuristic
        with open(initial_file, "wb") as f:
            pickle.dump(initial_values, f)

    print("Initial colorings stored.")

def load_initial_coloring(graph_name, input_directory="output/initial_colorings"):
    initial_file = os.path.join(input_directory, f"{graph_name}.pkl")

    with open(initial_file, "rb") as f:
        initial_values = pickle.load(f)

    return initial_values

def sample_parameters(
    alpha_range=(0.0, 0.15),
    T0_range=(1.0, 10000.0),
    mu_range=(0.999, 0.999999),
    simulated_annealing=True,
):
    """
    Draw a random (alpha, T0, mu, simulated_annealing) parameter set.

    - alpha is drawn uniformly in alpha_range.
    - T0 is drawn log-uniformly in T0_range (it spans several orders of
      magnitude, so uniform sampling would almost always pick large values).
    - mu is drawn so that the cooling gap (1 - mu) is log-uniform between
      (1 - mu_range[1]) and (1 - mu_range[0]); this samples mu evenly across
      its orders of magnitude of "closeness to 1".
    """
    lo_a, hi_a = alpha_range
    alpha = lo_a + random() * (hi_a - lo_a)

    lo_T, hi_T = T0_range
    T0 = exp(log(lo_T) + random() * (log(hi_T) - log(lo_T)))

    gap_lo = 1.0 - mu_range[1]  # smallest gap  -> mu closest to 1
    gap_hi = 1.0 - mu_range[0]  # largest gap
    mu = 1.0 - exp(log(gap_lo) + random() * (log(gap_hi) - log(gap_lo)))

    return alpha, T0, mu, simulated_annealing

def read_best_conflicts_from_file(output_file):
    """
    Read just the `best_nb_of_conflicts` value from a previously written best
    file, or return None if the file is missing / unparseable. Stops reading
    before the large best_color_map line so this stays cheap.
    """
    if not os.path.exists(output_file):
        return None
    try:
        with open(output_file) as f:
            for line in f:
                if line.startswith("best_nb_of_conflicts"):
                    return int(line.split("=", 1)[1].strip())
    except (ValueError, OSError):
        return None
    return None

def run_timed_search(
    graph_file,
    time_budget=600.0,
    output_file=None,
    nb_iter_max=100000,
    alpha_range=(0.0, 0.15),
    T0_range=(1.0, 10000.0),
    mu_range=(0.999, 0.999999),
    simulated_annealing=True,
    param_grid=None,
):
    """
    Spend up to `time_budget` seconds (default 600 = 10 minutes) searching for
    the best coloring of a single graph.

    Parameters for each restart come from one of two sources:
    - if `param_grid` is given (a list of (alpha, T0, mu, sa) tuples), the
      restarts cycle through those combinations round-robin (grid search);
    - otherwise a fresh random (alpha, T0, mu) is drawn each restart.

    The best coloring and conflict count seen across ALL restarts are kept and
    written to `output_file` every time they improve, using an atomic rename so
    the file can safely be inspected at any moment -- even before the budget
    runs out (e.g. `cat best_<graph>.txt` in another terminal).

    `graph_file` is the path to a .col file. If its initial coloring has not
    been cached yet it is computed and stored automatically.
    """
    graph_name = os.path.splitext(os.path.basename(graph_file))[0]

    # Ensure the cached initial coloring exists (compute it once if missing).
    initial_dir = "output/initial_colorings"
    os.makedirs(initial_dir, exist_ok=True)
    initial_file = os.path.join(initial_dir, f"{graph_name}.pkl")
    if not os.path.exists(initial_file):
        print(f"Computing initial coloring for {graph_name} ...")
        G, k = read_graph_from_file(graph_file)
        with open(initial_file, "wb") as f:
            pickle.dump(initial_coloring(G, k), f)

    if output_file is None:
        output_file = f"best_{graph_name}.txt"

    # Never regress an existing result: read the incumbent conflict count (if
    # any) and only overwrite the file once we strictly beat it this session.
    incumbent = read_best_conflicts_from_file(output_file)
    if incumbent is not None:
        print(f"Existing result for {graph_name}: {incumbent} conflicts -- will only overwrite if improved.")

    # All-time best across every restart. "stats" holds the per-run statistics
    # of the restart that produced the current all-time best (None until the
    # producing run finishes). "conflicts" is seeded with the incumbent so the
    # session only reports / persists genuine improvements over the saved file.
    # "improved" records whether this session beat the incumbent.
    best = {
        "conflicts": incumbent,
        "color_map": None,
        "params": None,
        "stats": None,
        "improved": False,
    }
    start_time = perf_counter()

    def persist():
        # Only write once we have a real coloring from this session that beat
        # the incumbent; otherwise leave the existing (better/equal) file alone.
        if best["color_map"] is None:
            return
        elapsed = perf_counter() - start_time
        tmp = output_file + ".tmp"
        with open(tmp, "w") as f:
            f.write(f"graph = {graph_name}\n")
            f.write(f"best_nb_of_conflicts = {best['conflicts']}\n")
            f.write(f"elapsed_seconds = {elapsed:.1f}\n")
            f.write(f"params (alpha, T0, mu, sa) = {best['params']}\n")

            s = best["stats"]
            f.write("\n--- statistics of the run that found this best ---\n")
            if s is None:
                f.write("(run still in progress -- stats available once it ends)\n")
            else:
                f.write(f"average_conflicts = {s['average_conflicts']:.4f}\n")
                f.write(f"max_conflicts = {s['max_conflicts']}\n")
                f.write(f"run_total_time_seconds = {s['total_time']:.6f}\n")
                f.write(f"time_to_best_within_run_seconds = {s['time_to_best_solution']:.6f}\n")
                f.write(f"solutions_evaluated = {s['solutions_evaluated']}\n")
                f.write(f"solutions_per_second = {s['solutions_per_second']:.4f}\n")

            # Convert to a plain Python list so the full map is written: a
            # NumPy array longer than 1000 elements would otherwise be
            # abbreviated with "..." by its string formatting.
            cm = best["color_map"]
            if hasattr(cm, "tolist"):
                cm = cm.tolist()
            f.write(f"\nbest_color_map = {cm}\n")
        # atomic replace: a concurrent reader never sees a half-written file
        os.replace(tmp, output_file)

    restart = 0
    while perf_counter() - start_time < time_budget:
        if param_grid:
            # Grid search: cycle through the fixed combinations round-robin
            alpha, T0, mu, sa = param_grid[restart % len(param_grid)]
        else:
            # Draw a fresh random parameter set for this restart
            alpha, T0, mu, sa = sample_parameters(
                alpha_range, T0_range, mu_range, simulated_annealing
            )

        improved = [False]  # did this restart set a new all-time best?

        def save_callback(conflicts, color_map, _p=(alpha, T0, mu, sa)):
            if best["conflicts"] is None or conflicts < best["conflicts"]:
                best["conflicts"] = conflicts
                best["color_map"] = color_map  # already a fresh copy from the heuristic
                best["params"] = _p
                best["stats"] = None  # this run's final stats aren't known yet
                best["improved"] = True
                improved[0] = True
                persist()
                elapsed = perf_counter() - start_time
                print(f"[{elapsed:6.1f}s] new all-time best: {conflicts} conflicts  (alpha={_p[0]:.4f}, T0={_p[1]:.1f}, mu={_p[2]:.7f})", flush=True)

        result = probabilistic_heuristic(
            graph_name, nb_iter_max, alpha, T0, mu, sa, save_callback=save_callback
        )

        # If this restart produced the all-time best, record its run statistics
        # and rewrite the file now that total_time / solutions_per_second exist.
        if improved[0]:
            (
                _current_nb, _best_cm, _history, _iter_stop, _best_seen, _iter_best,
                average_conflicts, _min_conflicts, max_conflicts,
                total_time, time_to_best_solution,
                solutions_evaluated, solutions_per_second,
            ) = result
            best["stats"] = {
                "average_conflicts": average_conflicts,
                "max_conflicts": max_conflicts,
                "total_time": total_time,
                "time_to_best_solution": time_to_best_solution,
                "solutions_evaluated": solutions_evaluated,
                "solutions_per_second": solutions_per_second,
            }
            persist()

        restart += 1
        if best["conflicts"] == 0:
            print("Found a conflict-free coloring! Stopping early.")
            break

    persist()  # final write (also covers the case where nothing ever improved)
    total = perf_counter() - start_time
    print(
        f"Done after {total:.1f}s and {restart} restart(s). "
        f"Best = {best['conflicts']} conflicts. Saved to {output_file}"
    )
    return best

def run_timed_search_on_directory(
    directory,
    output_directory,
    time_budget=1200.0,
    nb_iter_max=100000,
    alpha_range=(0.0, 0.15),
    T0_range=(1.0, 10000.0),
    mu_range=(0.999, 0.999999),
    simulated_annealing=True,
    skip_done=False,
    param_grid=None,
    total_time_budget=None,
):
    """
    Run run_timed_search on every .col file in `directory`, spending
    `time_budget` seconds (default 1200 = 20 minutes) per graph.

    If `total_time_budget` is given, the per-graph budget is instead set to
    total_time_budget / (number of graphs), so the whole sweep finishes in
    roughly that total time. `param_grid` (a list of (alpha, T0, mu, sa)
    tuples) is passed to run_timed_search to do grid search instead of random
    sampling.

    Each graph's best coloring (plus statistics) is written to
    <output_directory>/best_<graph>.txt, updated live during the search so it
    can be inspected at any time. A one-line-per-graph overview is written to
    <output_directory>/summary.txt and rewritten after every graph, so the
    overview stays valid even if the whole sweep is interrupted.

    When a graph uses up its full budget it is marked done with an empty
    <output_directory>/<graph>.done file. If `skip_done` is True, graphs that
    already have that marker are skipped entirely (their saved result is kept
    and still listed in the summary). A graph interrupted mid-budget has no
    marker, so it is re-run from scratch and gets a clean full budget.
    """
    os.makedirs(output_directory, exist_ok=True)
    files = sorted(read_files_from_directory(directory))

    # Derive a per-graph budget from the total budget if one was given.
    if total_time_budget is not None and files:
        time_budget = total_time_budget / len(files)
        print(
            f"Total budget {total_time_budget:.0f}s over {len(files)} graph(s) "
            f"-> {time_budget:.0f}s ({time_budget/60:.1f} min) per graph."
        )

    summary = []
    overall_start = perf_counter()

    def write_summary():
        summary_file = os.path.join(output_directory, "summary.txt")
        with open(summary_file, "w") as f:
            f.write(
                "graph best_conflicts alpha T0 mu "
                "run_total_time time_to_best solutions_per_second\n"
            )
            for name, b in summary:
                p = b["params"]
                s = b["stats"]
                if p is None:
                    # No new coloring this session: a kept/skipped incumbent
                    # (conflicts known, from the untouched best file) or a graph
                    # that never improved at all (conflicts None).
                    marker = " (unchanged)" if b["conflicts"] is not None else ""
                    f.write(f"{name} {b['conflicts']}{marker}\n")
                elif s is None:
                    f.write(
                        f"{name} {b['conflicts']} "
                        f"{p[0]:.4f} {p[1]:.1f} {p[2]:.7f}\n"
                    )
                else:
                    f.write(
                        f"{name} {b['conflicts']} "
                        f"{p[0]:.4f} {p[1]:.1f} {p[2]:.7f} "
                        f"{s['total_time']:.4f} {s['time_to_best_solution']:.4f} "
                        f"{s['solutions_per_second']:.1f}\n"
                    )

    for idx, filename_source in enumerate(files, start=1):
        graph_name = os.path.splitext(os.path.basename(filename_source))[0]
        output_file = os.path.join(output_directory, f"best_{graph_name}.txt")
        done_marker = os.path.join(output_directory, f"{graph_name}.done")

        if skip_done and os.path.exists(done_marker):
            conflicts = read_best_conflicts_from_file(output_file)
            print(
                f"\n===== [{idx}/{len(files)}] {graph_name} -- already done "
                f"({conflicts} conflicts), skipping ====="
            )
            summary.append((graph_name, {
                "conflicts": conflicts, "color_map": None,
                "params": None, "stats": None, "improved": False,
            }))
            write_summary()
            continue

        elapsed_total = perf_counter() - overall_start
        print(
            f"\n===== [{idx}/{len(files)}] {graph_name} "
            f"(budget {time_budget:.0f}s, {elapsed_total:.0f}s elapsed so far) ====="
        )

        best = run_timed_search(
            filename_source,
            time_budget=time_budget,
            output_file=output_file,
            nb_iter_max=nb_iter_max,
            alpha_range=alpha_range,
            T0_range=T0_range,
            mu_range=mu_range,
            simulated_annealing=simulated_annealing,
            param_grid=param_grid,
        )
        summary.append((graph_name, best))

        # The graph used its full budget: mark it done so a later run with
        # skip_done=True can skip it. (Only reached if the search returned
        # normally -- an interrupted sweep never writes the marker.)
        with open(done_marker, "w") as f:
            f.write(f"{graph_name} completed: {best['conflicts']} conflicts\n")

        write_summary()  # keep the overview current after every graph

    total = perf_counter() - overall_start
    print(
        f"\nAll {len(files)} graph(s) done in {total:.0f}s "
        f"({total/60:.1f} min). Results in {output_directory}/"
    )
    return summary

def run_grid_search_on_directory(
    directory,
    output_directory,
    total_time_budget=14400.0,   # 4 hours over the whole directory
    alpha_list=(0.0, 0.01, 0.05, 0.1, 0.15),
    T0_list=(100.0, 1000.0, 10000.0),
    mu_list=(0.999, 0.9999, 0.999999),
    simulated_annealing=True,
    nb_iter_max=100000,
    skip_done=False,
):
    """
    Grid search over the whole directory, bounded to `total_time_budget`
    seconds in total (default 14400 = 4 hours). Every (alpha, T0, mu)
    combination from the given lists is tried, cycled round-robin within each
    graph's time slice. Existing results are kept and only overwritten when
    strictly improved (see run_timed_search), so this can safely run on a
    directory that already holds results from a previous run.
    """
    grid = [
        (alpha, T0, mu, simulated_annealing)
        for alpha, T0, mu in product(alpha_list, T0_list, mu_list)
    ]
    print(
        f"Grid search: {len(grid)} parameter combination(s) per graph "
        f"(alpha x T0 x mu = {len(alpha_list)} x {len(T0_list)} x {len(mu_list)})."
    )
    return run_timed_search_on_directory(
        directory,
        output_directory,
        total_time_budget=total_time_budget,
        nb_iter_max=nb_iter_max,
        param_grid=grid,
        simulated_annealing=simulated_annealing,
        skip_done=skip_done,
    )

def main():

    # run_grid_search_on_directory(
    #     "data",
    #     "output_exam",
    #     total_time_budget=14400,   # 4 hours total
    #     alpha_list=(0.0, 0.01, 0.05, 0.1, 0.15),
    #     T0_list=(100.0, 1000.0, 10000.0),
    #     mu_list=(0.999, 0.9999, 0.999999),
    #     skip_done=False,
    # )
    # Classic descent: T0 ~ 0 and mu = 1.0 make the SA acceptance reject every
    # worsening move (exp(-delta/T) ~ 0), so it behaves as a pure descent.
    # run_grid_search_on_directory(
    #     "data",
    #     "output_descent",
    #     total_time_budget=14400,   # 4 hours total
    #     alpha_list=(0.0, 0.01, 0.05, 0.1, 0.15),
    #     T0_list=(1e-10,),          # single-element tuples need the trailing comma
    #     mu_list=(1.0,),
    #     skip_done=False,
    # )

    # ===== EXAM: 10-minute best-coloring search on a single graph =====
    # Point it at the graph file; it caches the initial coloring if needed,
    # runs for `time_budget` seconds, and writes the all-time best to
    # best_<graph>.txt, updating that file on every improvement so you can
    # `cat` it at any time to check progress.

    # CHECKLIST
    # 1. Make sure the graph file exists (e.g. data/dsjc250.9_k72.col)
    # 2. Make sure k is added at the beggining of the file 
    # 3. Run and check that the directory starts receiving the best coloring yet
    # run_timed_search("data/dsjc250.9_k72.col", "output_exam_live", time_budget=600)
    # return
    # ==================================================================

    return




if __name__ == "__main__":
    main()

