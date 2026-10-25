"""The SIMULATED next day used by the demo.

jlcparts stock numbers don't change day to day (see SPIKE_NOTES.md), so a real stock-out
would almost never show up. For the demo we copy today's snapshot and edit it by hand:
the first monitored part sells out and the second jumps 35% in price. Everything that
happens after that (diff, substitute checks, alert) is the real code path.
"""
import copy


def simulate_next_day(today):
    tomorrow = copy.deepcopy(today)
    tomorrow["date"] = "simulated-next-day"
    lcscs = list(tomorrow["parts"])
    if lcscs:
        tomorrow["parts"][lcscs[0]]["stock"] = 0
    if len(lcscs) > 1 and tomorrow["parts"][lcscs[1]]["price"]:
        tomorrow["parts"][lcscs[1]]["price"] = round(tomorrow["parts"][lcscs[1]]["price"] * 1.35, 4)
    return tomorrow
