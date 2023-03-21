# currencies are slices, roots, balls, and shells

#vertical is from, horizontal is to
import itertools


conversion_rates = [
#  slices, roots, balls, shells
    [1, 0.5, 1.45, 0.75], # slices
    [1.95, 1, 3.1, 1.49], # roots
    [0.67, 0.31, 1, 0.48],# balls
    [1.34, 0.64, 1.98, 1] # shells
]

# Requirements: 
# Start with 2,000,000 shells
#Start with shells, end with shells, 5 trades max
#(Shells -> A -> B -> C -> D -> Shells

num_currency = [0, 0, 0, 2000000]

# Strategy:
# Simulate all possible paths from shells to shells with 5 trades, and pick the one with the highest profit

possible_paths = []
current_path = ['shells']

for i in [p1 for p1 in itertools.product([0, 1, 2, 3], repeat=6)]:
    if i[0] == 3 and i[len(i)-1] == 3:
        possible_paths.append(i)

# print(possible_paths)

print(len(possible_paths))

path_to_profit = {}

for p in possible_paths:
    num_currency = [0, 0, 0, 2000000]
    # Compute the profit for each path
    for i in range(len(p)):
        current_count = num_currency[p[i-1]]
        num_currency[p[i-1]] = 0
        num_currency[p[i]] = current_count * conversion_rates[p[i-1]][p[i]]
        

    path_to_profit[p] = num_currency[3]

# print the path with the highest profit
print(max(path_to_profit, key=path_to_profit.get))
# print the highest profit
print(max(path_to_profit.values()))

