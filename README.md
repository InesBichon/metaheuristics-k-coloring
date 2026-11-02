The initial coloring is constructed using the following greedy strategy:

- Vertices are processed in descending order of degree.
- For each vertex, the colors assigned to its neighbors are examined.
- The vertex is assigned the first available color that does not create any conflicts. If no such color exists, it is assigned the color that minimizes the number of conflicts.

The k-coloring loop is done with a simulated annealing metaheuristic, combined with a GRASP (Greedy Randomized Adaptive Search Procedure)-type probabilistic selection at each iteration to choose the vertex whose color will be changed.

This approach involves four parameters to optimize: the initial temperature T0, the cooling rate μ, the parameter α, which controls the size of the restricted candidate list, and the maximum number of iterations.

For each graph, the metaheuristic is run with different parameter combinations, recording the minimum number of conflicts found and its corresponding coloring.