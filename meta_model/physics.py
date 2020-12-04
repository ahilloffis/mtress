import numpy as np

# Absolute zero
ZERO_CELSIUS = 273.15  # K

# Natural gas
HS_PER_HI_GAS = 1.11  # according to DIN V 18599

# Wood pellets
HS_PER_HI_WP = 1.08  # according to DIN V 18599
HHV_WP = 4.8  # kWh/kg  /  MWh/t

# Water in heat storage
H2O_HEAT_CAPACITY = 4.182  # kJ/(kg*K)
H2O_HEAT_FUSION = 0.09265  # MWh/t, = 333.55 J/g
H2O_DENSITY = 1000  # Kg/m^3
H2O_HEAT_CAPACITY = 4.182  # kJ/(kg*K)

# Thermal conductivity
TC_CONCRETE = 0.8  # W / (m * K)
TC_INSULATION = 0.04  # W / (m * K)

# improve readability, used e.g. for J -> Wh
SECONDS_PER_HOUR = 3600


def kilo_to_mega(arg):
    """
    use to make explicit unit conversions instead of just dividing by 1000
    """
    return arg/1000


def celsius_to_kelvin(arg):
    """
    converts °C to K
    """
    return ZERO_CELSIUS + arg


def kelvin_to_celsius(arg):
    """
    converts K to °C
    """
    return arg - ZERO_CELSIUS


def kJ_to_MWh(arg):  # pylint: disable=C0103
    """
    converts kJ to MWh
    """
    return kilo_to_mega(arg / SECONDS_PER_HOUR)


def carnot_efficiency(temp_in, temp_out):
    if not isinstance(temp_out, (int, float)):
        temp_in = np.full(len(temp_out), temp_in)

    return temp_out / np.maximum(temp_out - temp_in, 1e-3)


def calc_cop(temp_source, temp_target):
    '''
    Temperature inputs in Kelvin
    '''
    cop_norm = 4.7

    temp_source_norm = celsius_to_kelvin(0)
    temp_target_norm = celsius_to_kelvin(35)

    cpf = 1 / carnot_efficiency(temp_source_norm,
                                temp_target_norm) * cop_norm

    try:
        max_cop = cop_norm
        if not isinstance(temp_target, (int, float)):
            max_cop = np.full(len(temp_target), cop_norm)
        clipped_cop = np.minimum(
            carnot_efficiency(temp_source, temp_target) * cpf,
            max_cop)
    except ValueError:
        max_cop = np.full(len(temp_source), cop_norm)

        clipped_cop = np.minimum(carnot_efficiency(
            temp_source, temp_target)
                                 * cpf, max_cop)

    return clipped_cop


if __name__ == "__main__":
    temp_target = np.asanyarray([celsius_to_kelvin(50), celsius_to_kelvin(70)])
    res = calc_cop(celsius_to_kelvin(10), temp_target)
    print(res)
    print(calc_cop(273, 310))
