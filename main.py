
# imported libraries
import os
import matplotlib.pyplot as plt
import networkx as nx
from random import random
from math import floor, exp
from itertools import product 
import pickle


# global variables
n = 10 # number of nodes
k = 3 # max number of colors accepted
p = 0.5
seed = 20160
training = True


#computes min, max, and both indices from a list
def min_and_max(l):
    if len(l) == 0:
        print("Error: list is empty")
        return
    m = l[0]
    ind_m = 0
    M = l[0]
    ind_M = 0
    for i in range(len(l)):
        if l[i] < m:
            m = l[i]
            ind_m = i
        if l[i] > M:
            M = l[i]
            ind_M = i
    return m, M, ind_m, ind_M

def initial_coloring(G, k):
    e_c = [] #list of edges that have the same color on both ends, e_c stands for "edges with conflicts", its elements are of the type (u, v, ind_u_in_v, ind_v_in_u)
    nb_of_conflicts = 0 #number of edges that have the same color on both ends
    ordered_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True) #nodes ordered by degree in descending order
    color_map = [None] * len(G.nodes())
    neighbors_per_color = [[0 for i in range(k)] for _ in range(len(G.nodes()))] #for each node, count how many neighbors have each color
    a = [[] for i in range(len(G.nodes()))]
    for node in G.nodes():
        a[node] = list(sorted(G.neighbors(node))) 
    adj_list = [[] for i in range(len(G.nodes()))] #completed adjacency list of type (neighbor, l, j) with neighbor, index of edge between node and neighbor if there is a conflict (None otherwise), and with index of node in neighbor's adjacency list

    # construct adj_list
    count_total_neighbors = 0
    for node in range(len(G.nodes())):
        for i in range(len(a[node])):
            neighbor = a[node][i]
            # if not node in a[a[node][i]]:
            #     print("Initial error with adjacency list a")
            adj_list[neighbor].append([node, None, i])
            # if not (len(adj_list[node]) == 0):
                # if adj_list[node][i][0] != a[node][i]:

            count_total_neighbors += 1
            # if a[node][i] == node:
            #     print(f"Error: node {node} has an edge with itself.")
            #     print(f"this is a[{node}]: {a[node]}")
    
    # print("adj_list is:")
    # for i in range(len(adj_list)):
    #     print(f"adj_list[{i}] is {adj_list[i]}")
    
    # count_edges = 0
    # for node in range(len(G.nodes())):
    #     for i in range(len(adj_list[node])):
    #         neighbor, l, j = adj_list[node][i]
    #         count_edges += 1
    #         if adj_list[neighbor][j][0] != node:
    #             print(f"WRONG ASSIGNMENT for node {node}")

    # assign colors to nodes in descending order of degree
    for node in ordered_nodes:
        c = min(neighbors_per_color[node])
        color_map[node] = neighbors_per_color[node].index(c) # assigned color that minimizes the number of new conflicts
        # if color_map[node] == None:
        #     print(f"Error: node {node} should have a color.")
        for i in range(len(adj_list[node])):
            neighbor, l, j = adj_list[node][i]
            neighbors_per_color[neighbor][color_map[node]] += 1
            if color_map[neighbor] == color_map[node]: # neighbor and node are in conflict
                e_c.append((node, neighbor, j, i)) # add edge to conflicting edges with corresponding info
                # if adj_list[node][i][1] != None:
                #     print("1.Error: l value should be None")
                # if adj_list[neighbor][j][1] != None:
                #     print("2.Error: l value should be None")
                adj_list[node][i][1] = len(e_c) - 1 # position of edge indicated in adj_list[node][index of neighbor]
                adj_list[neighbor][j][1] = len(e_c) - 1 # position of edge indicated in adj_list[neighbor][index of node]

    # count_l_not_None = 0
    # for node in range(len(G.nodes())):
    #     for i in range(len(adj_list[node])):
    #         neighbor, l, j = adj_list[node][i]
            # if adj_list[neighbor][j][0] != node:
            #     print("Initial Error, wrong neighbor assignment")
            # if adj_list[neighbor][j][1] != l:
            #     print("Initial Error, conflicting assignment for l in node and neighbor")
            # if not (l == None):
            #     count_l_not_None += 1

    
    # print(f"number of nodes is {len(adj_list)}")
    # print(f"number of edges is {count_edges/2}")
    # print(f"count_total_neighbors is {count_total_neighbors}")
    # print(f"2 * nb of edges is {2 * len(G.edges)} initially")
    # print(f"count_l_not_None is {count_l_not_None} initially")
    nb_of_conflicts = len(e_c)
    return color_map, nb_of_conflicts, e_c, adj_list, neighbors_per_color

# draw the colored graph
def draw_colored_graph(G, color_map):
    pos = nx.spring_layout(G, seed=seed)  # Seed for reproducible layout
    nx.draw(G, pos=pos, node_color=color_map, with_labels=True)
    plt.show()

### EXPERIMENTS WITH SMALL GRAPHS
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

# Draw all unlabeled graphs with n nodes
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

"""
draw_colored_graphs_with_conflicts was created to see what happens in small graphs
"""
# Color all graphs with n nodes and draw only those that have at least one conflict and are better than the coloring found by f_coloriage
def draw_colored_graphs_with_conflicts(n, k):
    for G in atlas:
        if len(G.nodes()) == n:
            color_map, nb_of_conflicts, e_c, dict_conflicts_per_node = initial_coloring(G, k)
            if nb_of_conflicts > 0:
                best_color_map, min_conflicts, e_c_best = find_best_coloring(G, k)
                if nb_of_conflicts > min_conflicts: #only draw graphs that have at least one conflict and are better than the coloring found by f_coloriage
                    print(f"Graph with {n} nodes and {nb_of_conflicts} conflicts:")
                    draw_colored_graph(G, color_map)
                    draw_colored_graph(G, best_color_map)

### END OF EXPERIMENTS WITH SMALL GRAPHS


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

    return G, k

def read_files_from_directory(directory):
    return [
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if filename.endswith(".col")
    ]

# def coloring_from_file(filename_source, filename_group, filename_dest, nb_iter_max, alpha, T0, mu, simulated_annealing):
#     G, k = read_graph_from_file(filename_source)
#     current_nb_of_conflicts, best_color_map, history_nb_of_conflicts, iteration_stop, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen = probabilistic_heuristic(graph_name, nb_iter_max, alpha, T0, mu, simulated_annealing)
#     with open(filename_dest, "w") as f:
#         f.write(f"nb_iter_max = {nb_iter_max}\n")
#         f.write(f"alpha = {alpha}\n")
#         f.write(f"T0 = {T0}\n")
#         f.write(f"mu = {mu}\n")
#         f.write(f"simulated_annealing = {simulated_annealing}\n")
#         f.write(f"best_nb_of_conflicts_seen = {best_nb_of_conflicts_seen}\n")
#         f.write(f"best_color_map = {best_color_map}")
#     with open(filename_group, "w") as fg:
#         fg.write(f"{filename_source} {best_nb_of_conflicts_seen}")
#     return

# def coloring_from_directory(directory, folder, nb_iter_max, alpha, T0, mu, simulated_annealing):
#     files = read_files_from_directory(directory)
#     file_group = os.path.join(folder, f"{directory}.txt")
#     for filename_source in files:
#         filename_dest = os.path.join(folder, f"{os.path.basename(filename_source)}.txt")
#         coloring_from_file(filename_source, file_group, filename_dest, nb_iter_max, alpha, T0, mu, simulated_annealing)
#     return

# #TODO csv
# def run_on_directory(directory, nb_iter_max_list, alpha_list, T0_list, mu_list, simulated_annealing_list):

#     for nb_iter_max, alpha, T0, mu, simulated_annealing in product(nb_iter_max_list, alpha_list, T0_list, mu_list, simulated_annealing_list):
#         folder = f"output/{nb_iter_max}_{alpha}_{T0}_{mu}_{simulated_annealing}"
#         os.makedirs(folder, exist_ok=True)

#         coloring_from_directory(directory, folder, nb_iter_max, alpha, T0, mu, simulated_annealing)

#     print("All results saved.")
#     return


def probabilistic_heuristic(graph_name, nb_iter_max, alpha, T0, mu, simulated_annealing):
    if training:
        initial_values = load_initial_coloring(graph_name)

        current_color_map, current_nb_of_conflicts, e_c, adj_list, neighbors_per_color = initial_values
    else:
        G, k = read_graph_from_file(graph_name)
        current_color_map, current_nb_of_conflicts, e_c, adj_list, neighbors_per_color = initial_coloring(G, k)
    T = T0
    # print(f"Initial number of conflicts is {current_nb_of_conflicts}.")
    history_nb_of_conflicts =[current_nb_of_conflicts]
    iteration_stop = 0
    best_nb_of_conflicts_seen = current_nb_of_conflicts
    iter_best_nb_of_conflicts_seen = 0
    best_color_map = current_color_map
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

        m, M, ind_m, ind_M = min_and_max(neighbors_per_color[node])
        upper_bound = m + alpha * M
        candidates_color = []
        for color in range(len(neighbors_per_color[node])):
            if neighbors_per_color[node][color] <= upper_bound:
                candidates_color.append(color)
        r3 = random()
        ind_new_color = floor(r3*len(candidates_color))
        if simulated_annealing:
            delta = candidates_color[ind_new_color] - neighbors_per_color[node][current_color_map[node]]
            if delta > 0:
                r4 = random()
                limit = exp(-delta/T)
                if r4 > limit:
                    history_nb_of_conflicts.append(current_nb_of_conflicts)
                    continue
        T = T * mu
        old_color = current_color_map[node]
        new_color = candidates_color[ind_new_color]

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
            best_color_map = current_color_map
        history_nb_of_conflicts.append(current_nb_of_conflicts)
        # print(f"Current number of conflicts is {current_nb_of_conflicts} after {t} iterations.")

    print(f"Final value of T is {T}")
    return current_nb_of_conflicts, best_color_map, history_nb_of_conflicts, iteration_stop, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen

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
    alpha_values = [0, 0.05, 0.1]
    lists_of_conflicts_alphas = []
    for alpha in alpha_values:
        nb_of_conflicts, color_map, history_nb_of_conflicts, iteration_stop, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen = probabilistic_heuristic(graph_name, iterations, alpha, T0, mu, simulated_annealing)
        lists_of_conflicts_alphas.append([history_nb_of_conflicts, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen])
        draw_evolution_of_conflicts(history_nb_of_conflicts, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen, alpha)

    plt.legend()
    plt.show()
    return

# def find_best_T0_and_mu(G, k, iterations):
    pass
    

#### EXPERIMENT TO FIND BEST PARAMETERS

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

def find_best_T0_and_mu(graph_name, iterations):

    T0_values = [100, 1000, 10000]       # À adapter
    mu_values = [0.999, 0.9995, 0.9999]  # À adapter
    alpha_values = [0, 0.1, 0.15]

    fig, axes = plt.subplots(
        len(T0_values),
        len(mu_values),
        figsize=(15, 12),
        sharex=True,
        sharey=True
    )

    for i, T0 in enumerate(T0_values):
        for j, mu in enumerate(mu_values):

            ax = axes[i, j]

            for alpha in alpha_values:

                (
                    nb_of_conflicts,
                    color_map,
                    history_nb_of_conflicts,
                    iteration_stop,
                    best_nb_of_conflicts_seen,
                    iter_best_nb_of_conflicts_seen
                ) = probabilistic_heuristic(
                    graph_name, iterations, alpha, T0, mu
                )

                draw_evolution_of_conflicts(
                    ax,
                    history_nb_of_conflicts,
                    best_nb_of_conflicts_seen,
                    iter_best_nb_of_conflicts_seen,
                    alpha
                )

            ax.set_title(f"T0 = {T0}, mu = {mu}")
            ax.grid(True, alpha=0.3)

    fig.supxlabel("Itération")
    fig.supylabel("Nombre de conflits")
    fig.suptitle("Influence de T0 et mu pour différentes valeurs de alpha")

    # Une légende commune aux 9 graphiques
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center",
               ncol=len(alpha_values), bbox_to_anchor=(0.5, 0.96))

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.show()

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

    # Return results so the caller can compare parameter combinations
    return best_nb_of_conflicts_seen, best_color_map


def run_on_directory(
    directory,
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

        graph_folder = os.path.join("output", graph_name)
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

            conflicts, color_map = coloring_from_file(
                filename_source,
                filename_dest,
                nb_iter_max,
                alpha,
                T0,
                mu,
                simulated_annealing,
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
    summary_file = "output/best_results.txt"
    os.makedirs("output", exist_ok=True)

    with open(summary_file, "w") as f:
        f.write("name_of_graph best_nb_of_conflicts nb_iter_max alpha T0 mu\n")

        for graph_name, best_conflicts, best_params in all_best_results:
            f.write(
                f"{graph_name} {best_conflicts} "
                f"{best_params['nb_iter_max']} "
                f"{best_params['alpha']} "
                f"{best_params['T0']} "
                f"{best_params['mu']}\n"
            )
    print("All results saved.")

#### END OF EXPERIMENT TO FIND BEST PARAMETERS

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

def main():
    # G = nx.erdos_renyi_graph(n, p, seed=42)
    # G, k = read_graph_from_file("data/dsjc250.9_k72.col")
    # G, k = read_graph_from_file("data/flat300_26_k13.col")
    # G, k = read_graph_from_file("data/flat300_26_k26.col")
    # G, k = read_graph_from_file("data/le450_15c_k15.col")
    graph_name = "C4000.5_k130.col"
    # iterations = 10000
    # alpha = 0.1
    # T0 = 100
    # mu = 0.99999
    # simulated_annealing = True
    # nb_of_conflicts, color_map, history_nb_of_conflicts, iteration_stop, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen = probabilistic_heuristic(graph_name, iterations, alpha, T0, mu, simulated_annealing)
    # draw_evolution_of_conflicts(history_nb_of_conflicts, best_nb_of_conflicts_seen, iter_best_nb_of_conflicts_seen, alpha)
    # plt.legend()
    # plt.show()
    # print(f"Final number of conflicts is {nb_of_conflicts}.")
    # print(f"Best number of conflicts seen is {best_nb_of_conflicts_seen}")
    # run_on_directory("data")

    # find_best_alpha(graph_name, iterations, T0, mu)
    # find_best_T0_and_mu(graph_name, iterations)

    nb_iter_max_list = [10000, 100000]
    alpha_list = [0, 0.05, 0.1, 0.15]
    T0_list = [100, 500, 1000, 1500]
    mu_list = [0.99, 0.999, 0.9999]
    simulated_annealing = [True]
    # store_initial_colorings("data")
    # run_on_directory("data", nb_iter_max_list, alpha_list, T0_list, mu_list, simulated_annealing)

    return

main()

