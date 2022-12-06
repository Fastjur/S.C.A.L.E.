from enum import Enum

from rest_framework import serializers


class ProcessType(Enum):
    DAY_AHEAD = "A01"
    INTRA_DAY_INCREMENTAL = "A02"
    REALISED = "A16"
    INTRADAY_TOTAL = "A18"
    WEEK_AHEAD = "A31"
    MONTH_AHEAD = "A32"
    YEAR_AHEAD = "A33"
    SYNCHRONISATION_PROCESS = "A39"
    INTRADAY_PROCESS = "A40"
    REPLACEMENT_RESERVE = "A46"
    MANUAL_FREQUENCY_RESTORATION_RESERVE = "A47"
    AUTOMATIC_FREQUENCY_RESTORATION_RESERVE = "A51"
    FREQUENCY_CONTAINMENT_RESERVE = "A52"
    FREQUENCY_RESTORATION_RESERVE = "A56"
    SCHEDULED_ACTIVATION_M_FRR = "A60"
    DIRECT_ACTIVATION_M_FRR = "A61"
    CENTRAL_SELECTION_A_FRR = "A67"
    LOCAL_SELECTION_A_FRR = "A68"

    def __str__(self):
        string_representation = {
            "A01": "Day ahead",
            "A02": "Intra day incremental",
            "A16": "Realised",
            "A18": "Intraday total",
            "A31": "Week ahead",
            "A32": "Month ahead",
            "A33": "Year ahead",
            "A39": "Synchronisation process",
            "A40": "Intraday process",
            "A46": "Replacement reserve",
            "A47": "Manual frequency restoration reserve",
            "A51": "Automatic frequency restoration reserve",
            "A52": "Frequency containment reserve",
            "A56": "Frequency restoration reserve",
            "A60": "Scheduled activation mFRR",
            "A61": "Direct activation mFRR",
            "A67": "Central Selection aFRR",
            "A68": "Local Selection aFRR",
        }
        return string_representation[self.value]


class ProcessTypeSerializer(serializers.Field):
    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        return ProcessType(data)


class Resolution(Enum):
    FifteenMinutes = "PT15M"
    SixtyMinutes = "PT60M"

    def get_minutes(self):
        resolution_minutes = {
            Resolution.FifteenMinutes: 15,
            Resolution.SixtyMinutes: 60,
        }

        if self in resolution_minutes:
            return resolution_minutes[self]
        else:
            raise Exception("Unknown resolution")

    def __str__(self):
        string_representation = {
            "PT15M": "Fifteen minutes",
            "PT60M": "Sixty minutes",
        }
        return string_representation[self.value]


class ResolutionSerializer(serializers.Field):
    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        return Resolution(data)


class BusinessType(Enum):
    PRODUCTION = "A01"
    CONSUMPTION = "A04"
    BALANCE_ENERGY_DEVIATION = "A19"
    GENERAL_CAPACITY_INFORMATION = "A25"
    ALREADY_ALLOCATED_CAPACITY = "A29"
    INSTALLED_GENERATION = "A37"
    REQUESTED_CAPACITY = "A43"
    SYSTEM_OPERATOR_REDISPATCHING = "A46"
    PLANNED_MAINTENANCE = "A53"
    UNPLANNED_OUTAGE = "A54"
    MINIMUM_POSSIBLE = "A60"
    MAXIMUM_POSSIBLE = "A61"
    INTERNAL_REDISPATCH = "A85"
    POSITIVE_FORECAST_MARGIN = "A91"
    NEGATIVE_FORECAST_MARGIN = "A92"
    WIND_GENERATION = "A93"
    SOLAR_GENERATION = "A94"
    FREQUENCY_CONTAINMENT_RESERVE = "A95"
    AUTOMATIC_FREQUENCY_RESTORATION_RESERVE = "A96"
    MANUAL_FREQUENCY_RESTORATION_RESERVE = "A97"
    REPLACEMENT_RESERVE = "A98"
    INTERCONNECTOR_NETWORK_EVOLUTION = "B01"
    INTERCONNECTOR_NETWORK_DISMANTLING = "B02"
    COUNTER_TRADE = "B03"
    CONGESTION_COSTS = "B04"
    CAPACITY_ALLOCATED = "B05"
    AUCTION_REVENUE = "B07"
    TOTAL_NOMINATED_CAPACITY = "B08"
    NET_POSITION = "B09"
    CONGESTION_INCOME = "B10"
    PRODUCTION_UNIT = "B11"
    AREA_CONTROL_ERROR = "B33"
    OFFER = "B74"
    NEED = "B75"
    PROCURED_CAPACITY = "B95"
    SHARED_BALANCING_RESERVE_CAPACITY = "C22"
    SHARE_OF_RESERVE_CAPACITY = "C23"
    ACTUAL_RESERVE_CAPACITY = "C24"

    def __str__(self):
        string_representation = {
            "A01": "Production",
            "A04": "Consumption",
            "A19": "Balance energy deviation",
            "A25": "General Capacity Information",
            "A29": "Already allocated capacity (AAC)",
            "A37": "Installed generation",
            "A43": "Requested capacity (without price)",
            "A46": "System Operator redispatching",
            "A53": "Planned maintenance",
            "A54": "Unplanned outage",
            "A60": "Minimum possible",
            "A61": "Maximum possible",
            "A85": "Internal redispatch",
            "A91": "Positive forecast margin (if installed capacity > load "
            "forecast)",
            "A92": "Negative forecast margin (if load forecast > installed "
            "capacity)",
            "A93": "Wind generation",
            "A94": "Solar generation",
            "A95": "Frequency containment reserve",
            "A96": "Automatic frequency restoration reserve",
            "A97": "Manual frequency restoration reserve",
            "A98": "Replacement reserve",
            "B01": "Interconnector network evolution",
            "B02": "Interconnector network dismantling",
            "B03": "Counter trade",
            "B04": "Congestion costs",
            "B05": "Capacity allocated (including price)",
            "B07": "Auction revenue",
            "B08": "Total nominated capacity",
            "B09": "Net position",
            "B10": "Congestion income",
            "B11": "Production unit",
            "B33": "Area Control Error",
            "B74": "Offer",
            "B75": "Need",
            "B95": "Procured capacity",
            "C22": "Shared Balancing Reserve Capacity",
            "C23": "Share of reserve capacity",
            "C24": "Actual reserve capacity",
        }
        return string_representation[self.value]


class BusinessTypeSerializer(serializers.Field):
    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        return BusinessType(data)


class PsrType(Enum):
    MIXED = "A03"
    GENERATION = "A04"
    LOAD = "A05"
    BIOMASS = "B01"
    FOSSIL_BROWN_COAL_LIGNITE = "B02"
    FOSSIL_COAL_DERIVED_GAS = "B03"
    FOSSIL_GAS = "B04"
    FOSSIL_HARD_COAL = "B05"
    FOSSIL_OIL = "B06"
    FOSSIL_OIL_SHALE = "B07"
    FOSSIL_PEAT = "B08"
    GEOTHERMAL = "B09"
    HYDRO_PUMPED_STORAGE = "B10"
    HYDRO_RUN_OF_RIVER_AND_POUNDAGE = "B11"
    HYDRO_WATER_RESERVOIR = "B12"
    MARINE = "B13"
    NUCLEAR = "B14"
    OTHER_RENEWABLE = "B15"
    SOLAR = "B16"
    WASTE = "B17"
    WIND_OFFSHORE = "B18"
    WIND_ONSHORE = "B19"
    OTHER = "B20"
    AC_LINK = "B21"
    DC_LINK = "B22"
    SUBSTATION = "B23"
    TRANSFORMER = "B24"

    def __str__(self):
        string_representation = {
            "A03": "Mixed",
            "A04": "Generation",
            "A05": "Load",
            "B01": "Biomass",
            "B02": "Fossil Brown coal/Lignite",
            "B03": "Fossil Coal-derived gas",
            "B04": "Fossil Gas",
            "B05": "Fossil Hard coal",
            "B06": "Fossil Oil",
            "B07": "Fossil Oil shale",
            "B08": "Fossil Peat",
            "B09": "Geothermal",
            "B10": "Hydro Pumped Storage",
            "B11": "Hydro Run-of-river and poundage",
            "B12": "Hydro Water Reservoir",
            "B13": "Marine",
            "B14": "Nuclear",
            "B15": "Other renewable",
            "B16": "Solar",
            "B17": "Waste",
            "B18": "Wind Offshore",
            "B19": "Wind Onshore",
            "B20": "Other",
            "B21": "AC Link",
            "B22": "DC Link",
            "B23": "Substation",
            "B24": "Transformer",
        }
        return string_representation[self.value]


class PsrTypeSerializer(serializers.Field):
    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        return PsrType(data)


class DocumentType(Enum):
    FINALISED_SCHEDULE = "A09"
    AGGREGATED_ENERGY_DATA_REPORT = "A11"
    ACQUIRING_SYSTEM_OPERATOR_RESERVE_SCHEDULE = "A15"
    BID_DOCUMENT = "A24"
    ALLOCATION_RESULT_DOCUMENT = "A25"
    CAPACITY_DOCUMENT = "A26"
    AGREED_CAPACITY = "A31"
    RESERVE_BID_DOCUMENT = "A37"
    RESERVE_ALLOCATION_RESULT_DOCUMENT = "A38"
    PRICE_DOCUMENT = "A44"
    ESTIMATED_NET_TRANSFER_CAPACITY = "A61"
    REDISPATCH_NOTICE = "A63"
    SYSTEM_TOTAL_LOAD = "A65"
    INSTALLED_GENERATION_PER_TYPE = "A68"
    WIND_AND_SOLAR_FORECAST = "A69"
    LOAD_FORECAST_MARGIN = "A70"
    GENERATION_FORECAST = "A71"
    RESERVOIR_FILLING_INFORMATION = "A72"
    ACTUAL_GENERATION = "A73"
    WIND_AND_SOLAR_GENERATION = "A74"
    ACTUAL_GENERATION_PER_TYPE = "A75"
    LOAD_UNAVAILABILITY = "A76"
    PRODUCTION_UNAVAILABILITY = "A77"
    TRANSMISSION_UNAVAILABILITY = "A78"
    OFFSHORE_GRID_INFRASTRUCTURE_UNAVAILABILITY = "A79"
    GENERATION_UNAVAILABILITY = "A80"
    CONTRACTED_RESERVES = "A81"
    ACCEPTED_OFFERS = "A82"
    ACTIVATED_BALANCING_QUANTITIES = "A83"
    ACTIVATED_BALANCING_PRICES = "A84"
    IMBALANCE_PRICES = "A85"
    IMBALANCE_VOLUME = "A86"
    FINANCIAL_SITUATION = "A87"
    CROSS_BORDER_BALANCING = "A88"
    CONTRACTED_RESERVE_PRICES = "A89"
    INTERCONNECTION_NETWORK_EXPANSION = "A90"
    COUNTER_TRADE_NOTICE = "A91"
    CONGESTION_COSTS = "A92"
    DC_LINK_CAPACITY = "A93"
    NON_EU_ALLOCATIONS = "A94"
    CONFIGURATION_DOCUMENT = "A95"
    FLOW_BASED_ALLOCATIONS = "B11"
    AGGREGATED_NETTED_EXTERNAL_TSO_SCHEDULE_DOCUMENT = "B17"
    BID_AVAILABILITY_DOCUMENT = "B45"

    def __str__(self):
        string_representation = {
            "A09": "Finalised schedule",
            "A11": "Aggregated energy data report",
            "A15": "Acquiring system operator reserve schedule",
            "A24": "Bid document",
            "A25": "Allocation result document",
            "A26": "Capacity document",
            "A31": "Agreed capacity",
            "A37": "Reserve bid document",
            "A38": "Reserve allocation result document",
            "A44": "Price Document",
            "A61": "Estimated Net Transfer Capacity",
            "A63": "Redispatch notice",
            "A65": "System total load",
            "A68": "Installed generation per type",
            "A69": "Wind and solar forecast",
            "A70": "Load forecast margin",
            "A71": "Generation forecast",
            "A72": "Reservoir filling information",
            "A73": "Actual generation",
            "A74": "Wind and solar generation",
            "A75": "Actual generation per type",
            "A76": "Load unavailability",
            "A77": "Production unavailability",
            "A78": "Transmission unavailability",
            "A79": "Offshore grid infrastructure unavailability",
            "A80": "Generation unavailability",
            "A81": "Contracted reserves",
            "A82": "Accepted offers",
            "A83": "Activated balancing quantities",
            "A84": "Activated balancing prices",
            "A85": "Imbalance prices",
            "A86": "Imbalance volume",
            "A87": "Financial situation",
            "A88": "Cross border balancing",
            "A89": "Contracted reserve prices",
            "A90": "Interconnection network expansion",
            "A91": "Counter trade notice",
            "A92": "Congestion costs",
            "A93": "DC link capacity",
            "A94": "Non EU allocations",
            "A95": "Configuration document",
            "B11": "Flow-based allocations",
            "B17": "Aggregated netted external TSO schedule document",
            "B45": "Bid Availability Document",
        }
        return string_representation[self.value]
