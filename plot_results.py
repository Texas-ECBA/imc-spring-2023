# pip install matplotlib
import matplotlib.pyplot as plt

# CONFIGURABLES
filename = "l1.log"
plot_bid_and_ask = False
plot_price = True
plot_products = ["PINA_COLADAS", "COCONUTS"]
def isCustomExcluded(seriesLabel):
    if "CUSTOM" in seriesLabel:
        return True

    if "acc" in seriesLabel.lower():
        return True

    if "short" in seriesLabel:
        return True

    if "long" in seriesLabel:
        return True
    
    if "ultraLong" in seriesLabel:
        return False
    
    return False
    
# END CONFIGURABLES


timestamps: dict[str, list[int]] = {}
prices: dict[str, list[float]] = {}
bids: dict[str, list[float]] = {}
asks: dict[str, list[float]] = {}
positions: dict[str, list[float]] = {}
customs: dict[str, list[list[float]]] = {}

products = ["PEARLS", "BANANAS", "PINA_COLADAS", "COCONUTS"]

common_customs = ["shortMa", "longMa", "ultraLongMa", "shortVel", "longVel", "ultraLongVel", "shortAcc", "longAcc", "ultraLongAcc",]

productToCustomSeries = {
    "PEARLS": common_customs + ["CUSTOM1", "CUSTOM2", "CUSTOM3", "CUSTOM4", "CUSTOM5"],
    "BANANAS": common_customs + ["CUSTOM1", "CUSTOM2", "CUSTOM3", "CUSTOM4", "CUSTOM5"],
    "PINA_COLADAS": common_customs + ["PC PriceNorm", "Coconut PriceNorm", "Ratio", "+t", "-t"],
    "COCONUTS": common_customs + ["CUSTOM1", "CUSTOM2", "CUSTOM3", "CUSTOM4", "CUSTOM5"],
}

custom_colors = ["red", "green", "blue", "orange", "purple", "silver", "black", "pink", "brown", "gray", "olive", "cyan", "magenta",  "teal", "coral", "navy", "maroon", "turquoise", "violet", "silver",  "khaki", "indigo", "darkgreen", "darkblue", "darkred", "darkorange", "darkgray", "darkcyan", "darkmagenta", "darkolivegreen", "darkkhaki", "darkgoldenrod", "darkviolet", "darkslategray", "darkslateblue", "darkseagreen", "darkorchid"]

#TIMESTAMP, PRODUCT, POSITION, BID, PRICE, ASK, shortMa, longMa, ultraLongMa, shortVel, longVel, ultraLongVel, shortAcc, longAcc, ultraLongAcc, custom1, custom2, custom3, custom4, custom5

for i in [timestamps, prices, bids, asks, positions]:
    for product in products:
        i[product] = []

for product in products:
    customs[product] = [
        [] for i in range(len(productToCustomSeries[product]))
    ]

with open(filename, "r") as f:
    lines = f.readlines()
    for line in lines:
        if not "CSVDATA" in line or "TIMESTAMP" in line: # skip header and all lines without CSVDATA
            continue
        line = line.strip()
        line = line.split(",")
        product = line[1].removeprefix('"').removesuffix('"')
        if product not in plot_products:
            continue
        timestamps[product].append(int(line[0].split(" ")[0]))
        positions[product].append(float(line[2]))
        prices[product].append(float(line[4]))
        bids[product].append(float(line[3]))
        asks[product].append(float(line[5]))
        for i in range(6, len(line) - 1): # skip timestamp, product, position, bid, price, ask and CSVDATA
            if i-6 >= len(customs[product]):
                print("ERROR: too many custom series for product " + product)
                break
            if line[i] == "True":
                customs[product][i-6].append(1)
            elif line[i] == "False":
                customs[product][i-6].append(0)
            else:
                customs[product][i-6].append(float(line[i]))


# number of plots is number of products where timestamps are not empty
num_plots = len([i for i in timestamps if len(timestamps[i]) > 0])

fig, axs = plt.subplots(num_plots, 1, figsize=(10, 10))

i = 0
for kv in enumerate(products):
    product = kv[1]
    if (product not in timestamps) or len(timestamps[product]) == 0:
        continue
    
    if plot_price:
        axs[i].plot(timestamps[product], prices[product], label="Price")
    

    if plot_bid_and_ask:
        axs[i].plot(timestamps[product], bids[product], label="Bid")
        axs[i].plot(timestamps[product], asks[product], label="Ask")
    


    # plot custom series on secondary y axis, and also make sure they are labeled
    secondary_ax = axs[i].twinx()
    fourth_ax = axs[i].twinx()
    seriesLabels = productToCustomSeries[product]
    for j in range(min(len(seriesLabels), len(customs[product]))):
        seriesLabel = seriesLabels[j]
        if isCustomExcluded(seriesLabel) or len(customs[product][j]) == 0:
            continue

        if "ma" in seriesLabel.lower():
            # plot in the main axis as a dashed line
            axs[i].plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j], linestyle="--")
            # pass
        elif "vel" in seriesLabel.lower():
            # plot in fourth axis as a dotted line
            fourth_ax.plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j], linestyle=":")
        else:
            secondary_ax.plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j]) 

    tertiary_ax = axs[i].twinx()
    tertiary_ax.plot(timestamps[product], positions[product], label="Position", color="black")
    tertiary_ax.spines['right'].set_position(('outward', 50))
    
    fourth_ax.spines['right'].set_position(('outward', 100))
    

    axs[i].set_title(product)
    axs[i].legend()
    secondary_ax.legend()
    # show fourth axis legend, but offset it so it doesn't overlap with the secondary axis legend
    fourth_ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1))
    # make sure x axis is labeled every 10% of the data
    axs[i].set_xticks(timestamps[product][::len(timestamps[product])//10])
    # make sure all y axis labels are labeled every 20% of the data
    i += 1

plt.legend()
plt.show()