from enum import Enum

RESOURCES_FOLDER = "../resources"

class Season(Enum):
    T_2024_2025 = "2024-2025"
    T_2023_2024 = "2023-2024"
    T_2022_2023 = "2022-2023"
    T_2021_2022 = "2021-2022"
    T_2020_2021 = "2020-2021"
    T_2019_2020 = "2019-2020"
    T_2018_2019 = "2018-2019"

class Competition(Enum):
    T_PREFERENT = "preferent"
    T_SENIOR = "senior"
    T_VETERAN = "veterans"