# pip install matplotlib
import sys
import matplotlib.pyplot as plt
import re # for regex

# CONFIGURABLES -----------------------------
filename = "whole-round-five-log.csv"

from_sim = False 
simulate = True # can also change to True or False to simulate or not
plot_monkeys = False
plot_monkey_volume = True # not very useful btw
resultsMode = True # if true, plots round results (change in parsing)
sim_day = 1
sim_round = 4

monkey_tradefile = "./training/trades_round_" + str(sim_round) + "_day_" + str(sim_day) + "_wn.csv" #wn = with names
monkeys_to_plot = ["Caesar"] # if empty, will plot all monkeys
monkey_volume_filter = 8 # will only plot trades over this volume
if from_sim:
    filename = 'simresults.txt'
    if simulate:  
        import backtester
        backtester.run_simulation(sim_day, sim_round, plot_monkeys)
plotCombo = 2

if plotCombo == 0:
    plot_products = ["PINA_COLADAS", "COCONUTS"]
elif plotCombo == 1:
    plot_products = ["DIVING_GEAR", "DOLPHIN_SIGHTINGS"]
else:
    #plot_products = ["PICNIC_BASKET", "UKULELE", "DIP", "BAGUETTE"]
    plot_products = ["BAGUETTE", "BERRIES"]

plot_bid_and_ask = False
plot_price = True
plot_pnl = True
plot_position = True
plot_volume = True # not very useful btw


plot_zero_vel = False
plot_zero_acc = False
plot_zero_pnl = False
plot_const_customs = [50, 65, 35]
plot_customs = True
mirror_const_customs = False # if true, will plot the negative of each const custom

# Case sensitive, use * to match any characters in between
customs_to_plot = {
    "PEARLS": [],
    "BANANAS": ["shortMa", "ultraLongMa", "longMa"],

    "PINA_COLADAS": ["Ratio", "+t", "-t", "*NPrice"],
    "COCONUTS": ["bbavgPrice", "upperPrice", "lowerPrice",],    

    "BERRIES": ["ultraLongMa"],

    "DOLPHIN_SIGHTINGS": ["trend*", "*Ma", "*Days"],
    "DIVING_GEAR": [ "longMa", "sellPrice", "buyPrice",  "ultraLongMa", "ultra*Trend","ultra*Vel", "longVel"],
    "DIP": [],
    "BAGUETTE": [],
    "UKULELE": [ "bandVel", "rsi", "upperPrice", "lowerPrice", "overallVel", 'bbb'],
    "PICNIC_BASKET": ["bbavgPrice", "rstatus", "rsi", "overallVel"]
}
# END CONFIGURABLES -----------------------------
# set stdout back to normal (console)
sys.stdout = sys.__stdout__


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
monkeyBuyTrades: dict[str, dict[str, dict[float, float]]] = {}
monkeySellTrades: dict[str, dict[str, dict[float, float]]] = {}
monkeyVolume: dict[str, dict[str, dict[float, float]]] = {}
# product: monkey: {timestamp: price}
monkeyColors = ["red", "green", "blue", "orange", "purple", "silver", "black", "pink", "brown",  "olive", "cyan", "magenta",  "coral", "navy", "maroon", "violet",   "khaki", "indigo", "darkgreen", "darkblue", "darkred", "darkorange", "darkgray", "darkcyan", "darkmagenta", "darkolivegreen", "darkkhaki", "darkgoldenrod", "darkviolet", "darkslategray", "darkslateblue", "darkseagreen", "darkorchid"]

common_customs = ["shortMa", "longMa", "ultraLongMa", "shortVel", "longVel", "ultraLongVel", "shortAcc", "longAcc", "ultraLongAcc", "volume"]

productToCustomSeries = {
    "PEARLS": common_customs + ["CUSTOM1", "CUSTOM2", "CUSTOM3", "CUSTOM4", "CUSTOM5"],
    "BANANAS": common_customs + ["buyPrice", "sellPrice"],
    "PINA_COLADAS": common_customs + ["PC NPrice", "Coconut NPrice", "Ratio", "+t", "-t", "versusAcc"],
    "COCONUTS": common_customs + ["rsi", "rstatus"],
    "BERRIES": common_customs + ["buyPrice", "sellPrice", "Diff"],
    "DOLPHIN_SIGHTINGS": common_customs + ["trend0", "trend1", "trend2", "dolphinDays", "gearDays", "prediction"],
    "DIVING_GEAR": common_customs + ["ultraLongTrend", "sellPrice", "buyPrice", "longTrend", "sd", "sdsAway"] ,
    "DIP": common_customs + ["rsi", "rstatus"],
    "BAGUETTE": common_customs + ["rsi", "rstatus"],
    "UKULELE": common_customs + ["rsi", "overallVel", "bandVel", "upperPrice", "lowerPrice", "bbb"],
    "PICNIC_BASKET": common_customs + ["rsi", "rstatus"],
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
    monkeyBuyTrades[product] = {}
    monkeySellTrades[product] = {}
    monkeyVolume[product] = {}

jsonMode = False

print("Opening file: " + filename)
with open(filename, "r") as f:        
    lines = f.readlines()
    if jsonMode:
        lines = lines[8].split('": "')[1].split("\\n")
    for line in lines:
        if len(line) < 3 or (line[1] != ";" and line[2] != ';' and (not "CSVDATA" in line or "TIMESTAMP" in line)): # skip header and all lines without CSVDATA, but don't skip lines with ; in them
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

            if timestamp not in timestamps[product] and resultsMode:
                timestamps[product].append(timestamp)
            
            if timestamp in timestamps[product]:
                pnls[product].append(float(line[-1]))
                if resultsMode:
                    prices[product].append(float(line[-2]))

            # else:
            #     print("Unknown timestamp: " + str(timestamp) + " for product " + product + " in line " + str.join(";", line))
            #     pnls[product].append(0)
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


if plot_monkeys:
    with open(monkey_tradefile, "r") as f: # timestamp;buyer;seller;symbol;currency;price;quantity
        lines = f.readlines()
        for line in lines:
            values = line.split(";")
            if values[0] == "timestamp":
                continue
            timestamp = int(values[0])
            buyer = values[1]
            seller = values[2]
            product = values[3]
            price = float(values[5])
            
            if product not in plot_products:
                continue
            
            if buyer not in monkeyBuyTrades[product]:
                monkeyBuyTrades[product][buyer] = {}
            if seller not in monkeySellTrades[product]:
                monkeySellTrades[product][seller] = {}
            if buyer not in monkeyVolume[product]:
                monkeyVolume[product][buyer] = {}
            if seller not in monkeyVolume[product]:
                monkeyVolume[product][seller] = {}

            if float(values[6]) < monkey_volume_filter:
                continue

            monkeyBuyTrades[product][buyer][timestamp] = price
            monkeySellTrades[product][seller][timestamp] = price

            monkeyVolume[product][buyer][timestamp] = float(values[6])
            monkeyVolume[product][seller][timestamp] = float(values[6])


for product in products:
    if len(timestamps[product]) != len(pnls[product]):
        print("Different lengths for timestamps and pnls for product " + product + ": " + str(len(timestamps[product])) + " vs " + str(len(pnls[product])) + ". Fixing...")
        modified = 0
        while len(timestamps[product]) > len(pnls[product]):
            pnls[product].append(pnls[product][-1])
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
    vol_ax = axs[i].twinx()
    vel_j_val = 0
    acc_j_val = 0
    vol_j_val = 0

    hasVel = False
    hasAcc = False
    hasVol = False
    hasCustom = False

    seriesLabels = productToCustomSeries[product]
    for j in range(min(len(seriesLabels), len(customs[product]))):
        seriesLabel = seriesLabels[j]
        try:
            if isCustomExcluded(product, seriesLabel) or len(customs[product][j]) == 0 or not plot_customs:
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
            elif "volume" in seriesLabel.lower():
                # plot in volume axis as a solid line
                if not plot_volume:
                    continue
                lines = lines + vol_ax.plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j])
                vol_j_val = j
                hasVol = True
            else:
                lines = lines + secondary_ax.plot(timestamps[product], customs[product][j], label=seriesLabel, color=custom_colors[j]) 
                if not hasCustom:
                    hasCustom = True
                    for const_val in plot_const_customs:
                        secondary_ax.plot(timestamps[product], [const_val] * len(timestamps[product]), color=custom_colors[j], alpha=0.5)
        except Exception as e:
            print("Error plotting custom series " + seriesLabel + " for product " + product + ": " + str(e))


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
        

    if plot_monkeys:
        # plot monkey lines
        num_monkeys = 0
        for monkey in [*set(monkeyBuyTrades[product].keys()) | set(monkeySellTrades[product].keys())]:
            if monkey not in monkeys_to_plot and len(monkeys_to_plot) > 0:
                continue

            if monkey not in monkeyBuyTrades[product]:
                monkeyBuyTrades[product][monkey] = {}
            if monkey not in monkeySellTrades[product]:
                monkeySellTrades[product][monkey] = {}
            lines = lines + axs[i].plot(monkeyBuyTrades[product][monkey].keys(), monkeyBuyTrades[product][monkey].values(), '^', color=monkeyColors[num_monkeys], alpha=0.85, label=monkey)
            lines = lines + axs[i].plot(monkeySellTrades[product][monkey].keys(), monkeySellTrades[product][monkey].values(), 'v', color=monkeyColors[num_monkeys], alpha=0.85, label=monkey)

            if plot_monkey_volume and monkey in monkeyVolume[product]:
                line = vol_ax.plot(monkeyVolume[product][monkey].keys(), monkeyVolume[product][monkey].values(), 'o', color=monkeyColors[num_monkeys], alpha=0.5, label=monkey)
                lines = lines + line
                hasVol = True

            num_monkeys += 1

    if hasVol:
        # if plot_zero_vol:
        #     # plot zero line
        #     vol_ax.plot(timestamps[product], [0] * len(timestamps[product]), color=custom_colors[vol_j_val], linestyle="-")
        vol_ax.spines['right'].set_position(('outward', num_axes * mult))
        # make the spine style solid
        vol_ax.spines['right'].set_linestyle("-")
        # change the color of the spine to the color of the line
        vol_ax.spines['right'].set_color(custom_colors[vol_j_val])
        vol_ax.spines['right'].set_linewidth(2)
        num_axes += 1

    axs[i].set_title(product)



    # make sure x axis is labeled every 10% of the data
    axs[i].set_xticks(timestamps[product][::len(timestamps[product])//10])
    



    labels = [l.get_label() for l in lines]
    axs[i].legend(lines, labels, loc='center left', bbox_to_anchor=(-0.15, 0.5))

    print("product: " + product + ", num_axes: " + str(num_axes))
    i += 1

plt.rcParams["font.size"] =7
fig.set_zorder(1)
plt.tight_layout(pad=0)
# remove whitespace around everything
plt.subplots_adjust(left=0.1, bottom=0.05, right=0.8, top=0.95)

plt.show()


