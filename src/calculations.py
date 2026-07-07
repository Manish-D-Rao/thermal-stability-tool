import math


def calculate_delta_t(t1, t2):
    return ((t1 - t2) / (59 - 22)) * 100


def calculate_shear(u1, u2):
    return math.log(u1 / u2) / math.log(59 / 22)


# thermal_stability["py_shear"] = thermal_stability.apply(
#     lambda row: calculate_shear(row["ws59"], row["ws22"]),
#     axis=1
# )


def calculate_ws_bin(u):  # u59
    return round(u * 2) / 2
