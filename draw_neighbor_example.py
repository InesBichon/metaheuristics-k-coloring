"""Two graphs side by side: the neighbor differs by one recolored vertex."""
import matplotlib.pyplot as plt
import networkx as nx

G = nx.Graph()
G.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (3, 4), (3, 5), (4, 5)])
pos = {0: (0, 1), 1: (1, 1.7), 2: (1, 0.3), 3: (2, 1), 4: (3, 1.7), 5: (3, 0.3)}

colors = ["tab:blue", "tab:orange", "tab:green"]

# current: vertex 4 (blue) conflicts with neighbor 3 (blue)
current = [0, 1, 2, 0, 0, 2]
# neighbor: vertex 4 recolored blue -> orange
neighbor = [0, 1, 2, 0, 1, 2]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

nx.draw(G, pos, ax=ax1, with_labels=True, node_color=[colors[c] for c in current], node_size=800)
ax1.set_title("Current solution")

nx.draw(G, pos, ax=ax2, with_labels=True, node_color=[colors[c] for c in neighbor], node_size=800)
ax2.set_title("Neighbor solution")

fig.savefig("plots/neighbor_example.png", dpi=150)
print("Saved plots/neighbor_example.png")
