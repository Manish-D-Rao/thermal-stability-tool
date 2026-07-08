import math


def calculate_delta_t(t1, t2):
    return ((t1 - t2) / (59 - 22)) * 100


# thermal_stability["py_delta_t"] = calculate_delta_t(thermal_stability["temp59"], thermal_stability["temp22"])


def calculate_shear(u1, u2):
    if not u1 or not u2:
        return ""
    return math.log(u1 / u2) / math.log(59 / 22)


# thermal_stability["py_shear"] = thermal_stability.apply(
#     lambda row: calculate_shear(row["ws59"], row["ws22"]),
#     axis=1
# )


def calculate_ws_bin(u):  # u59
    return round(u * 2) / 2


# thermal_stability["py_ws_bin"] = calculate_ws_bin(thermal_stability["ws59"])


def calculate_ti(u, u_SD):
    return u_SD / u


# thermal_stability["py_ti"] = calculate_ti(thermal_stability["ws59"], thermal_stability["ws59_sd"])


def calculate_ws120(u, shear):
    if shear.empty:
        return ""
    return round((u * ((105 / 59) ** shear)), 2)


# thermal_stability["py_ws120"] = calculate_ws120(thermal_stability["ws59"], thermal_stability["py_shear"])


def calculate_ri(u59, u22, t59, t22):
    g = 9.81

    t_upper = t59 + 273.15
    t_lower = t22 + 273.15

    delta_z = 59 - 22

    temp_gradient = (t_upper - t_lower) / (delta_z + 9.8)

    wind_diff = u59 - u22

    ri = (g * temp_gradient * delta_z**2) / (t_lower * wind_diff**2)

    return round(ri, 2)


# thermal_stability["py_ri"] = calculate_ri(thermal_stability["ws59"], thermal_stability["ws22"], thermal_stability["temp59"], thermal_stability["temp22"])


def calculate_stability(ri):
    if ri < -0.2:
        return "strongly unstable"
    elif -0.2 <= ri < -0.1:
        return "unstable"
    elif -0.1 <= ri < 0.1:
        return "neutral"
    elif 0.1 <= ri < 0.25:
        return "stable"
    else:
        return "strongly stable"


# thermal_stability["py_stability"] = thermal_stability.apply(
#     lambda row: calculate_stability(row["py_ri"]),
#     axis=1
# )
