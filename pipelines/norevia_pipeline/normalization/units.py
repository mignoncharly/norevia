from dataclasses import replace
from decimal import Decimal

from norevia_pipeline.contracts import CandidateObservation

CONVERSIONS = {
    ("EUR_100KWH", "EUR_KWH"): lambda value: value / Decimal(100),
    ("fraction", "percent"): lambda value: value * Decimal(100),
}


def convert_unit(observation: CandidateObservation, target_unit: str) -> CandidateObservation:
    if observation.unit == target_unit:
        return observation
    converter = CONVERSIONS.get((observation.unit, target_unit))
    if converter is None:
        raise ValueError(f"No registered conversion from {observation.unit} to {target_unit}")
    return replace(
        observation,
        value=converter(observation.value),
        unit=target_unit,
        transformations=(*observation.transformations, f"unit:{observation.unit}->{target_unit}"),
    )
