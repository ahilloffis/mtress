import time
import pandas as pd
import json

from oemof.solph import views, processing

from meta_model.enaq_meta_model import ENaQMetaModel


def extract_result_sequence(results, label, resample=None):
    """
    :param results:
    :param label:
    :param resample: resampling frequency identifier (e.g. 'D')
    :return:
    """
    sequences = views.node(results, label)['sequences']
    if resample is not None:
        sequences = sequences.resample(resample).mean()
    return sequences


def main(number_of_time_steps=365*24):
    meteo = pd.read_csv('meteo.csv',
                        comment='#', index_col=0,
                        sep=',',
                        parse_dates=True)

    day_ahead = pd.read_csv('day-ahead.csv',
                            comment='#', index_col=0,
                            sep=',',
                            parse_dates=True)

    demand = pd.read_csv('demand.csv',
                         comment='#', index_col=0,
                         sep=',',
                         parse_dates=True)

    generation = pd.read_csv('generation.csv',
                             comment='#', index_col=0,
                             sep=',',
                             parse_dates=True)

    spec_co2 = pd.read_csv('spec_co2_de.csv',
                           comment='#', index_col=0,
                           sep=',',
                           parse_dates=True)

    data = meteo.join(day_ahead)
    data = data.join(demand)
    data = data.join(generation)
    data = data.join(spec_co2)

    del day_ahead
    del demand
    del generation
    del spec_co2

    data = data.dropna()
    data = data.resample("1h").mean()

    data = data.head(number_of_time_steps)

    time_series = {
        'meteorology': {
            'temp_air': meteo['temp_air'],  # K
            'temp_soil': meteo['temp_soil']},  # K
        'chp': {
            'feed_in_tariff_funded': data['price'] + 7.5,  # €/MWh
            'feed_in_tariff_unfunded': data['price'],  # €/MWh
            'own_consumption_tariff_funded': data['price'] + 3.5},  # €/MWh
        'pv': {
            'generation': data['PV']},  # MW
        'wind_turbine': {
            'generation': data['WT']},  # MW
        'solar_thermal': {
            'generation': data.filter(regex='ST')},  # MW
        'energy_cost': {
            'electricity': {
                'AP': data['price'] + 17,  # €/MWh
                'market': data['price']}},  # €/MW
        'demand': {
            'electricity': data['electricity'],  # MW (time series)
            'heating': data['heating'],  # MW (time series)
            'dhw': data['dhw']},  # MW (time series),
        'co2': {
            'el_in': data['spec_co2 (t/MWh)'],  # t/MWh
            'el_out': -data['spec_co2 (t/MWh)']}  # t/MWh
    }

    with open('variables.json') as f:
        variables = json.load(f)

    for key1 in time_series:
        if key1 not in variables:
            variables[key1] = time_series[key1]
        else:
            for key2 in time_series[key1]:
                if type(time_series[key1][key2]) == dict:
                    for key3 in time_series[key1][key2]:
                        variables[key1][key2][key3] = time_series[key1][key2][key3]
                else:
                    variables[key1][key2] = time_series[key1][key2]

    meta_model = ENaQMetaModel(**variables)

    print('Start solving')
    start = time.time()
    meta_model.model.solve(solver="cbc",
                           solve_kwargs={'tee': False},
                           solver_io='lp',
                           cmdline_options={'ratio': 0.01})
    end = time.time()
    print("Time to solve: " + str(end - start) + " Seconds")

    energy_system = meta_model.energy_system
    energy_system.results['valid'] = True
    energy_system.results['main'] = processing.results(
        meta_model.model)
    energy_system.results['main'] = views.convert_keys_to_strings(
        energy_system.results['main'])
    energy_system.results['meta'] = processing.meta_results(
        meta_model.model)

    heat_demand = meta_model.thermal_demand()

    print("Heat demand: {:.3f}".format(heat_demand))
    print("{:04.1f} % geothermal coverage".format(
        100 * meta_model.heat_geothermal() / heat_demand))
    print("{:04.1f} % solar coverage".format(
        100 * meta_model.heat_solar_thermal() / heat_demand))
    print("{:04.1f} % CHP coverage".format(
        100 * meta_model.heat_chp() / heat_demand))
    print("{:04.1f} % pellet coverage".format(
        100 * meta_model.heat_pellet() / heat_demand))
    print("{:04.1f} % boiler coverage".format(
        100 * meta_model.heat_boiler() / heat_demand))
    print("{:04.1f} % power2heat coverage".format(
        100 * meta_model.heat_p2h() / heat_demand))


if __name__ == '__main__':
    main()
