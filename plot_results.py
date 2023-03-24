# pip install matplotlib
import matplotlib.pyplot as plt


filename = "to_plot_2.log"

timestamps: dict[str, list[int]] = {}
prices: dict[str, list[float]] = {}
bids: dict[str, list[float]] = {}
asks: dict[str, list[float]] = {}

products = ["PEARLS", "BANANAS", "PINA_COLADAS", "COCONUTS"]

#TIMESTAMP, PRODUCT, POSITION, BID, PRICE, ASK, CUSTOM1, CUSTOM2, CUSTOM3, CUSTOM4, CUSTOM5, CSVDATA

for i in [timestamps, prices, bids, asks]:
    for product in products:
        i[product] = []

with open(filename, "r") as f:
    lines = f.readlines()
    for line in lines:
        if not "CSVDATA" in line or "TIMESTAMP" in line: # skip header and all lines without CSVDATA
            continue
        line = line.strip()
        line = line.split(",")
        product = line[1].removeprefix('"').removesuffix('"')
        print(product)
        timestamps[product].append(int(line[0].split(" ")[0]))
        prices[product].append(float(line[4]))
        bids[product].append(float(line[3]))
        asks[product].append(float(line[5]))


# number of plots is number of products where timestamps are not empty
num_plots = len([i for i in timestamps if len(timestamps[i]) > 0])

fig, axs = plt.subplots(num_plots, 1, figsize=(10, 10))

i = 0
for kv in enumerate(products):
    product = kv[1]
    if (product not in timestamps) or len(timestamps[product]) == 0:
        continue
    axs[i].plot(timestamps[product], prices[product], label="Price")
    axs[i].plot(timestamps[product], bids[product], label="Bid")
    axs[i].plot(timestamps[product], asks[product], label="Ask")
    axs[i].set_title(product)
    axs[i].legend()
    # make sure x axis is labeled every 10% of the data
    axs[i].set_xticks(timestamps[product][::len(timestamps[product])//10])
    i += 1

plt.show()