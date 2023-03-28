# pip install matplotlib
import sys
import matplotlib.pyplot as plt
import re # for regex

# CONFIGURABLES -----------------------------
filename = "output.txt"

from_sim = True
simulate = True # can also change to True or False to simulate or not
sim_day = 3

if from_sim:
    filename = 'simresults.txt'
    if simulate:  
        import backtester
        backtester.run_simulation(sim_day)

# set stdout back to normal (console)
sys.stdout = sys.__stdout__

plotCombo = 2

if plotCombo == 0:
    plot_products = ["PINA_COLADAS", "COCONUTS"]
elif plotCombo == 1:
    plot_products = ["DIVING_GEAR", "DOLPHIN_SIGHTINGS", "COCONUTS"]
else:
    #plot_products = ["PICNIC_BASKET", "UKULELE", "DIP", "BAGUETTE"]
    plot_products = ["UKULELE"]

plot_bid_and_ask = True
plot_price = True
plot_pnl = True
plot_position = True

plot_zero_vel = False
plot_zero_acc = False
plot_zero_pnl = False
plot_const_customs = [0.0003]

mirror_const_customs = True # if true, will plot the negative of each const custom


customs_to_plot = {
    "PEARLS": [],
    "BANANAS": ["shortMa", "ultraLongMa", "longMa"],

    "PINA_COLADAS": ["Ratio", "+t", "-t", "*NPrice"],
    "COCONUTS": ["*Ma", "*Price", "Diff", "*Trend", "ultraLongVel"],    

    "BERRIES": ["ultraLongMa"],

    "DOLPHIN_SIGHTINGS": ["trend*", "*Ma", "*Days"],
    "DIVING_GEAR": [ "longMa", "sellPrice", "buyPrice",  "ultraLongMa", "ultra*Trend","ultra*Vel", "longVel"],
    "DIP": [],
    "BAGUETTE": [],
    "UKULELE": ["*Ma", "*Trend", ],
    "PICNIC_BASKET": []
}
# END CONFIGURABLES -----------------------------

if mirror_const_customs:
    new_const_customs = []
    for i in plot_const_customs:
        new_const_customs.append(-i)
        new_const_customs.append(i)
    plot_const_customs = new_const_customs    


timestamps: dict[str, list[int]] = {}
prices: dict[str, list[float]] = {}
bids: dict[str, list[float]] = {}
asks: dict[str, list[float]] = {}
positions: dict[str, list[float]] = {}
customs: dict[str, list[list[float]]] = {}
pnls: dict[str, list[float]] = {}
products = ['PEARLS', 'BANANAS', 'COCONUTS', 'PINA_COLADAS', 'DIVING_GEAR', 'BERRIES', 'DOLPHIN_SIGHTINGS', 'BAGUETTE', 'DIP', 'UKULELE', 'PICNIC_BASKET']

common_customs = ["shortMa", "longMa", "ultraLongMa", "shortVel", "longVel", "ultraLongVel", "shortAcc", "longAcc", "ultraLongAcc",]

productToCustomSeries = {
    "PEARLS": common_customs + ["CUSTOM1", "CUSTOM2", "CUSTOM3", "CUSTOM4", "CUSTOM5"],
    "BANANAS": common_customs + ["buyPrice", "sellPrice"],
    "PINA_COLADAS": common_customs + ["PC NPrice", "Coconut NPrice", "Ratio", "+t", "-t", "versusAcc"],
    "COCONUTS": common_customs + ["buyPrice", "sellPrice", "Diff", "sd", "ultraLongTrend"],
    "BERRIES": common_customs + ["buyPrice", "sellPrice", "Diff"],
    "DOLPHIN_SIGHTINGS": common_customs + ["trend0", "trend1", "trend2", "dolphinDays", "gearDays", "prediction"],
    "DIVING_GEAR": common_customs + ["ultraLongTrend", "sellPrice", "buyPrice", "longTrend", "sd", "sdsAway"] ,
    "DIP": common_customs,
    "BAGUETTE": common_customs,
    "UKULELE": common_customs + ["sdShort", "sdLong", "sdUL","S-L_trend","L-UL_trend","ultraLongTrend"],
    "PICNIC_BASKET": common_customs
}

custom_colors = ["red", "green", "blue", "orange", "purple", "silver", "black", "pink", "brown",  "olive", "cyan", "magenta",  "coral", "navy", "maroon", "violet",   "khaki", "indigo", "darkgreen", "darkblue", "darkred", "darkorange", "darkgray", "darkcyan", "darkmagenta", "darkolivegreen", "darkkhaki", "darkgoldenrod", "darkviolet", "darkslategray", "darkslateblue", "darkseagreen", "darkorchid"]

#TIMESTAMP, PRODUCT, POSITION, BID, PRICE, ASK, shortMa, longMa, ultraLongMa, shortVel, longVel, ultraLongVel, shortAcc, longAcc, ultraLongAcc, custom1, custom2, custom3, custom4, custom5
#day;timestamp;product;bid_price_1;bid_volume_1;bid_price_2;bid_volume_2;bid_price_3;bid_volume_3;ask_price_1;ask_volume_1;ask_price_2;ask_volume_2;ask_price_3;ask_volume_3;mid_price;profit_and_loss

for i in [timestamps, prices, bids, asks, positions, pnls]:
    for product in products:
        i[product] = []

for product in products:
    customs[product] = [
        [] for i in range(len(productToCustomSeries[product]) if product in productToCustomSeries else 0)
    ]

jsonMode = False

print("Opening file: " + filename)
with open(filename, "r") as f:        
    lines = f.readlines()
    if jsonMode:
        lines = lines[8].split('": "')[1].split("\\n")
    for line in lines:
        if len(line) < 2 or (line[1] != ";" and line[2] != ';' and (not "CSVDATA" in line or "TIMESTAMP" in line)): # skip header and all lines without CSVDATA, but don't skip lines with ; in them
            continue
        line = line.strip()

        if line[1] == ";":
            line = line.split(";")
            product = line[2]
            if product not in plot_products:
                continue

            timestamp = int(line[1] if line[1] != "" else timestamps[product][-1] + 100 if len(timestamps[product]) > 0 else 0)

            if jsonMode:
                timestamps[product].append(timestamp)
                prices[product].append(float(line[-2]))
            if timestamp in timestamps[product]:
                pnls[product].append(float(line[-1]))
            else:
                print("Unknown timestamp: " + str(timestamp) + " for product " + product + " in line " + str.join(";", line))
                pnls[product].append(0)
            continue

        line = line.split(",")
        product = line[1].removeprefix('"').removesuffix('"') if len(line) > 1 else "UNKNOWN"
        if product not in plot_products:
            continue
        timestamps[product].append(int(line[0].split(" ")[0]))
        positions[product].append(float(line[2]))
        prices[product].append(float(line[4]))
        bids[product].append(float(line[3]))
        asks[product].append(float(line[5]))
        for i in range(6, len(line) - 1): # skip timestamp, product, position, bid, price, ask and CSVDATA
            if i-6 >= len(customs[product]):
                #print("ERROR: too many custom series for product " + product)
                break
            if line[i] == "True":
                customs[product][i-6].append(1)
            elif line[i] == "False":
                customs[product][i-6].append(0)
            else:
                customs[product][i-6].append(float(line[i]))

for product in products:
    if len(timestamps[product]) != len(pnls[product]):
        print("Different lengths for timestamps and pnls for product " + product + ": " + str(len(timestamps[product])) + " vs " + str(len(pnls[product])) + ". Fixing...")
        modified = 0
        while len(timestamps[product]) > len(pnls[product]):
            pnls[product].append(0)
            modified += 1
        while len(timestamps[product]) < len(pnls[product]):
            pnls[product].pop(0)
            modified += 1
        print("Modified " + str(modified) + " PnLs for product " + product)

# UTILITY FUNCTIONS
def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

def isCustomExcluded(product, seriesLabel):
    for regex in customs_to_plot[product]:
        if regex in seriesLabel or seriesLabel in regex or ("*" in regex and re.match(regex.replace("*", ".*"), seriesLabel)):
            return False
    
    return True
# END UTILITY FUNCTIONS
# number of plots is number of products where timestamps are not empty
num_plots = len([i for i in timestamps if len(timestamps[i]) > 0])

if num_plots == 0:
    print("No data to plot regarding products " + str(plot_products))
    exit()

fig, axsRes = plt.subplots(num_plots, 1, figsize=(10, 10), squeeze=False, sharex=True)

axs = [axsRes[i][0] for i in range(len(axsRes))]


i = 0
for kv in enumerate(plot_products):
    product = kv[1]
    if (product not in timestamps) or len(timestamps[product]) == 0:
        continue
    
    lines = []

    if plot_price and len(prices[product]) > 0:
        lines = lines + axs[i].plot(timestamps[product], prices[product], label="Price")
    

    if plot_bid_and_ask and len(bids[product]) > 0 and len(asks[product]) > 0:
        lines = lines + axs[i].plot(timestamps[product], bids[product], label="Bid")
        lines = lines + axs[i].plot(timestamps[product], asks[product], label="Ask")
    
    # plot custom series on secondary y axis, and also make sure they are labeled
    secondary_ax = axs[i].twinx()
    vel_ax = axs[i].twinx()
    acc_ax = axs[i].twinx()
    vel_j_val = 0
    acc_j_val = 0

    hasVel = False
    hasAcc = False
    hasCustom = False

    seriesLabels = productToCustomSeries[product]
    for j in range(min(len(seriesLabels), len(customs[product]))):
        seriesLabel = seriesLabels[j]
        if isCustomExcluded(product, seriesLabel) or len(customs[product][j]) == 0:
            continue

        if "ma" in seriesLabel.lower():
            # plot in the main axis as a dashed line
            lines = lines + axs[i].plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j], linestyle="-.")
            # pass
        elif "vel" in seriesLabel.lower():
            # plot in fourth axis as a dotted line
            lines = lines + vel_ax.plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j], linestyle="--")
            hasVel = True
            vel_j_val = j
        elif "acc" in seriesLabel.lower():
            # plot in sixth axis as a dotted line
            lines = lines + acc_ax.plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j], linestyle=":")
            hasAcc = True
            acc_j_val = j
        elif "price" in seriesLabel.lower():
            # plot in the main axis as a solid line
            lines = lines + axs[i].plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j])        
        else:
            lines = lines + secondary_ax.plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j]) 
            if not hasCustom:
                hasCustom = True
                for const_val in plot_const_customs:
                    secondary_ax.plot(timestamps[product], [const_val] * len(timestamps[product]), color=custom_colors[j], alpha=0.5)

    num_axes = 1
    mult = 50
    if plot_position and len(positions[product]) > 0:
        tertiary_ax = axs[i].twinx()
        lines = lines + tertiary_ax.plot(timestamps[product], positions[product], label="Position", color="black")
        tertiary_ax.spines['right'].set_position(('outward', num_axes * mult))
        num_axes += 1
        
    if plot_pnl:
        fifth_ax = axs[i].twinx()
        lines = lines + fifth_ax.plot(timestamps[product], pnls[product], label="PNL", color="green", linestyle="--", alpha=0.5)
        fifth_ax.spines['right'].set_position(('outward', num_axes * mult))
        num_axes += 1
        if plot_zero_pnl:
            # plot zero line
            fifth_ax.plot(timestamps[product], [0] * len(timestamps[product]), color="green", linestyle="--", alpha=0.5)
        
    if hasVel:
        if plot_zero_vel:
            # plot zero line
            vel_ax.plot(timestamps[product], [0] * len(timestamps[product]), color=custom_colors[vel_j_val], linestyle="--")
        
        vel_ax.spines['right'].set_position(('outward', num_axes * mult))
        # make the spine style dashed
        vel_ax.spines['right'].set_linestyle("--")
        # change the color of the spine to the color of the line
        vel_ax.spines['right'].set_color(custom_colors[vel_j_val])
        vel_ax.spines['right'].set_linewidth(2)
        num_axes += 1
    
    if hasAcc:
        if plot_zero_acc:
            # plot zero line
            acc_ax.plot(timestamps[product], [0] * len(timestamps[product]), color=custom_colors[acc_j_val], linestyle=":")
        acc_ax.spines['right'].set_position(('outward', num_axes * mult))
        # make the spine style dotted
        acc_ax.spines['right'].set_linestyle(":")
        # change the color of the spine to the color of the line
        acc_ax.spines['right'].set_color(custom_colors[acc_j_val])
        acc_ax.spines['right'].set_linewidth(2)
        num_axes += 1
        
    axs[i].set_title(product)

    labels = [l.get_label() for l in lines]
    axs[i].legend(lines, labels, loc='center left', bbox_to_anchor=(-0.15, 0.5))

    # make sure x axis is labeled every 10% of the data
    axs[i].set_xticks(timestamps[product][::len(timestamps[product])//10])
    


    print("product: " + product + ", num_axes: " + str(num_axes))
    i += 1

plt.rcParams["font.size"] =7
fig.set_zorder(1)
plt.tight_layout(pad=0)
# remove whitespace around everything
plt.subplots_adjust(left=0.1, bottom=0.05, right=0.8, top=0.95)

plt.show()


