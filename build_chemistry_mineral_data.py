#!/usr/bin/env python3
"""Build the public KnitWeb chemistry and mineral enrichment index."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "data" / "chemistry_minerals.json"
PUBCHEM_PERIODIC_TABLE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON"
COMPOSITION_BASIS = "ideal_formula_mass_percent_from_formula"


ISOTOPE_VARIANTS = {
    "H": [
        {"isotope": "H-1", "mass_number": 1, "abundance_percent": 99.985, "stability": "stable"},
        {"isotope": "H-2", "mass_number": 2, "abundance_percent": 0.015, "stability": "stable", "alias": "D"},
        {"isotope": "H-3", "mass_number": 3, "abundance_percent": None, "stability": "radioactive", "half_life": "12.32 y"},
    ],
    "C": [
        {"isotope": "C-12", "mass_number": 12, "abundance_percent": 98.93, "stability": "stable"},
        {"isotope": "C-13", "mass_number": 13, "abundance_percent": 1.07, "stability": "stable"},
        {"isotope": "C-14", "mass_number": 14, "abundance_percent": None, "stability": "radioactive", "half_life": "5730 y"},
    ],
    "O": [
        {"isotope": "O-16", "mass_number": 16, "abundance_percent": 99.757, "stability": "stable"},
        {"isotope": "O-17", "mass_number": 17, "abundance_percent": 0.038, "stability": "stable"},
        {"isotope": "O-18", "mass_number": 18, "abundance_percent": 0.205, "stability": "stable"},
    ],
    "Li": [
        {"isotope": "Li-6", "mass_number": 6, "abundance_percent": 7.59, "stability": "stable"},
        {"isotope": "Li-7", "mass_number": 7, "abundance_percent": 92.41, "stability": "stable"},
    ],
    "Mg": [
        {"isotope": "Mg-24", "mass_number": 24, "abundance_percent": 78.99, "stability": "stable"},
        {"isotope": "Mg-25", "mass_number": 25, "abundance_percent": 10.00, "stability": "stable"},
        {"isotope": "Mg-26", "mass_number": 26, "abundance_percent": 11.01, "stability": "stable"},
    ],
    "Al": [
        {"isotope": "Al-27", "mass_number": 27, "abundance_percent": 100.0, "stability": "stable"},
    ],
    "Si": [
        {"isotope": "Si-28", "mass_number": 28, "abundance_percent": 92.223, "stability": "stable"},
        {"isotope": "Si-29", "mass_number": 29, "abundance_percent": 4.685, "stability": "stable"},
        {"isotope": "Si-30", "mass_number": 30, "abundance_percent": 3.092, "stability": "stable"},
        {"isotope": "Si-31", "mass_number": 31, "abundance_percent": None, "stability": "radioactive", "half_life": "157.36 min"},
    ],
    "S": [
        {"isotope": "S-32", "mass_number": 32, "abundance_percent": 94.99, "stability": "stable"},
        {"isotope": "S-33", "mass_number": 33, "abundance_percent": 0.75, "stability": "stable"},
        {"isotope": "S-34", "mass_number": 34, "abundance_percent": 4.25, "stability": "stable"},
        {"isotope": "S-36", "mass_number": 36, "abundance_percent": 0.01, "stability": "stable"},
    ],
    "Cl": [
        {"isotope": "Cl-35", "mass_number": 35, "abundance_percent": 75.76, "stability": "stable"},
        {"isotope": "Cl-37", "mass_number": 37, "abundance_percent": 24.24, "stability": "stable"},
    ],
    "K": [
        {"isotope": "K-39", "mass_number": 39, "abundance_percent": 93.2581, "stability": "stable"},
        {"isotope": "K-40", "mass_number": 40, "abundance_percent": 0.0117, "stability": "radioactive"},
        {"isotope": "K-41", "mass_number": 41, "abundance_percent": 6.7302, "stability": "stable"},
    ],
    "Ca": [
        {"isotope": "Ca-40", "mass_number": 40, "abundance_percent": 96.941, "stability": "stable"},
        {"isotope": "Ca-42", "mass_number": 42, "abundance_percent": 0.647, "stability": "stable"},
        {"isotope": "Ca-43", "mass_number": 43, "abundance_percent": 0.135, "stability": "stable"},
        {"isotope": "Ca-44", "mass_number": 44, "abundance_percent": 2.086, "stability": "stable"},
        {"isotope": "Ca-46", "mass_number": 46, "abundance_percent": 0.004, "stability": "stable"},
        {"isotope": "Ca-48", "mass_number": 48, "abundance_percent": 0.187, "stability": "stable"},
    ],
    "Ti": [
        {"isotope": "Ti-46", "mass_number": 46, "abundance_percent": 8.25, "stability": "stable"},
        {"isotope": "Ti-47", "mass_number": 47, "abundance_percent": 7.44, "stability": "stable"},
        {"isotope": "Ti-48", "mass_number": 48, "abundance_percent": 73.72, "stability": "stable"},
        {"isotope": "Ti-49", "mass_number": 49, "abundance_percent": 5.41, "stability": "stable"},
        {"isotope": "Ti-50", "mass_number": 50, "abundance_percent": 5.18, "stability": "stable"},
    ],
    "V": [
        {"isotope": "V-50", "mass_number": 50, "abundance_percent": 0.25, "stability": "radioactive"},
        {"isotope": "V-51", "mass_number": 51, "abundance_percent": 99.75, "stability": "stable"},
    ],
    "Fe": [
        {"isotope": "Fe-54", "mass_number": 54, "abundance_percent": 5.845, "stability": "stable"},
        {"isotope": "Fe-56", "mass_number": 56, "abundance_percent": 91.754, "stability": "stable"},
        {"isotope": "Fe-57", "mass_number": 57, "abundance_percent": 2.119, "stability": "stable"},
        {"isotope": "Fe-58", "mass_number": 58, "abundance_percent": 0.282, "stability": "stable"},
    ],
    "Ni": [
        {"isotope": "Ni-58", "mass_number": 58, "abundance_percent": 68.0769, "stability": "stable"},
        {"isotope": "Ni-60", "mass_number": 60, "abundance_percent": 26.2231, "stability": "stable"},
        {"isotope": "Ni-61", "mass_number": 61, "abundance_percent": 1.1399, "stability": "stable"},
        {"isotope": "Ni-62", "mass_number": 62, "abundance_percent": 3.6346, "stability": "stable"},
        {"isotope": "Ni-64", "mass_number": 64, "abundance_percent": 0.9255, "stability": "stable"},
    ],
    "Cu": [
        {"isotope": "Cu-63", "mass_number": 63, "abundance_percent": 69.15, "stability": "stable"},
        {"isotope": "Cu-65", "mass_number": 65, "abundance_percent": 30.85, "stability": "stable"},
    ],
    "Zn": [
        {"isotope": "Zn-64", "mass_number": 64, "abundance_percent": 49.17, "stability": "stable"},
        {"isotope": "Zn-66", "mass_number": 66, "abundance_percent": 27.73, "stability": "stable"},
        {"isotope": "Zn-67", "mass_number": 67, "abundance_percent": 4.04, "stability": "stable"},
        {"isotope": "Zn-68", "mass_number": 68, "abundance_percent": 18.45, "stability": "stable"},
        {"isotope": "Zn-70", "mass_number": 70, "abundance_percent": 0.61, "stability": "stable"},
    ],
    "Pb": [
        {"isotope": "Pb-204", "mass_number": 204, "abundance_percent": 1.4, "stability": "stable"},
        {"isotope": "Pb-206", "mass_number": 206, "abundance_percent": 24.1, "stability": "stable"},
        {"isotope": "Pb-207", "mass_number": 207, "abundance_percent": 22.1, "stability": "stable"},
        {"isotope": "Pb-208", "mass_number": 208, "abundance_percent": 52.4, "stability": "stable"},
    ],
    "U": [
        {"isotope": "U-234", "mass_number": 234, "abundance_percent": 0.0055, "stability": "radioactive"},
        {"isotope": "U-235", "mass_number": 235, "abundance_percent": 0.7200, "stability": "radioactive"},
        {"isotope": "U-238", "mass_number": 238, "abundance_percent": 99.2745, "stability": "radioactive"},
    ],
}


MINERAL_SEED = [
    {
        "id": "quartz",
        "name": "Quartz",
        "formula": "SiO2",
        "formula_atoms": {"Si": 1, "O": 2},
        "mineral_class": "silicate",
        "target_elements": ["Si", "O"],
        "enrichment_note": "High-silica feedstock candidate when low impurity quartz is required.",
    },
    {
        "id": "hematite",
        "name": "Hematite",
        "formula": "Fe2O3",
        "formula_atoms": {"Fe": 2, "O": 3},
        "mineral_class": "oxide",
        "target_elements": ["Fe"],
        "enrichment_note": "Major iron ore mineral with high ideal iron mass percentage.",
    },
    {
        "id": "magnetite",
        "name": "Magnetite",
        "formula": "Fe3O4",
        "formula_atoms": {"Fe": 3, "O": 4},
        "mineral_class": "oxide",
        "target_elements": ["Fe"],
        "enrichment_note": "Dense magnetic iron oxide useful for separations based on magnetic response.",
    },
    {
        "id": "goethite",
        "name": "Goethite",
        "formula": "FeO(OH)",
        "formula_atoms": {"Fe": 1, "O": 2, "H": 1},
        "mineral_class": "oxide-hydroxide",
        "target_elements": ["Fe"],
        "enrichment_note": "Hydrated iron phase; water/hydroxyl content lowers ideal iron percentage.",
    },
    {
        "id": "ilmenite",
        "name": "Ilmenite",
        "formula": "FeTiO3",
        "formula_atoms": {"Fe": 1, "Ti": 1, "O": 3},
        "mineral_class": "oxide",
        "target_elements": ["Ti", "Fe"],
        "enrichment_note": "Titanium-bearing oxide commonly evaluated as a Ti feed mineral.",
    },
    {
        "id": "rutile",
        "name": "Rutile",
        "formula": "TiO2",
        "formula_atoms": {"Ti": 1, "O": 2},
        "mineral_class": "oxide",
        "target_elements": ["Ti"],
        "enrichment_note": "High titanium dioxide mineral and benchmark Ti enrichment candidate.",
    },
    {
        "id": "anatase",
        "name": "Anatase",
        "formula": "TiO2",
        "formula_atoms": {"Ti": 1, "O": 2},
        "mineral_class": "oxide",
        "target_elements": ["Ti"],
        "enrichment_note": "TiO2 polymorph with the same ideal mass composition as rutile.",
    },
    {
        "id": "gibbsite",
        "name": "Gibbsite",
        "formula": "Al(OH)3",
        "formula_atoms": {"Al": 1, "O": 3, "H": 3},
        "mineral_class": "hydroxide",
        "target_elements": ["Al"],
        "enrichment_note": "Aluminum hydroxide phase in bauxite-style enrichment workflows.",
    },
    {
        "id": "corundum",
        "name": "Corundum",
        "formula": "Al2O3",
        "formula_atoms": {"Al": 2, "O": 3},
        "mineral_class": "oxide",
        "target_elements": ["Al"],
        "enrichment_note": "Alumina mineral with high ideal aluminum percentage.",
    },
    {
        "id": "calcite",
        "name": "Calcite",
        "formula": "CaCO3",
        "formula_atoms": {"Ca": 1, "C": 1, "O": 3},
        "mineral_class": "carbonate",
        "target_elements": ["Ca", "C"],
        "enrichment_note": "Calcium carbonate reference mineral for carbonate-rich material streams.",
    },
    {
        "id": "dolomite",
        "name": "Dolomite",
        "formula": "CaMg(CO3)2",
        "formula_atoms": {"Ca": 1, "Mg": 1, "C": 2, "O": 6},
        "mineral_class": "carbonate",
        "target_elements": ["Ca", "Mg"],
        "enrichment_note": "Calcium-magnesium carbonate useful when Mg/Ca balance matters.",
    },
    {
        "id": "gypsum",
        "name": "Gypsum",
        "formula": "CaSO4.2H2O",
        "formula_atoms": {"Ca": 1, "S": 1, "O": 6, "H": 4},
        "mineral_class": "sulfate",
        "target_elements": ["Ca", "S"],
        "enrichment_note": "Hydrated sulfate; water strongly affects mass-balance interpretation.",
    },
    {
        "id": "halite",
        "name": "Halite",
        "formula": "NaCl",
        "formula_atoms": {"Na": 1, "Cl": 1},
        "mineral_class": "halide",
        "target_elements": ["Na", "Cl"],
        "enrichment_note": "Sodium chloride reference for brines and evaporite separations.",
    },
    {
        "id": "sylvite",
        "name": "Sylvite",
        "formula": "KCl",
        "formula_atoms": {"K": 1, "Cl": 1},
        "mineral_class": "halide",
        "target_elements": ["K", "Cl"],
        "enrichment_note": "Potassium chloride mineral for potash-oriented streams.",
    },
    {
        "id": "fluorite",
        "name": "Fluorite",
        "formula": "CaF2",
        "formula_atoms": {"Ca": 1, "F": 2},
        "mineral_class": "halide",
        "target_elements": ["F", "Ca"],
        "enrichment_note": "Calcium fluoride source mineral with strong halide signature.",
    },
    {
        "id": "apatite",
        "name": "Fluorapatite",
        "formula": "Ca5(PO4)3F",
        "formula_atoms": {"Ca": 5, "P": 3, "O": 12, "F": 1},
        "mineral_class": "phosphate",
        "target_elements": ["P", "Ca", "F"],
        "enrichment_note": "Phosphate mineral family seed for phosphorus and calcium ranking.",
    },
    {
        "id": "spodumene",
        "name": "Spodumene",
        "formula": "LiAlSi2O6",
        "formula_atoms": {"Li": 1, "Al": 1, "Si": 2, "O": 6},
        "mineral_class": "silicate",
        "target_elements": ["Li", "Al", "Si"],
        "enrichment_note": "Lithium aluminosilicate candidate for Li-bearing hard-rock workflows.",
    },
    {
        "id": "enstatite",
        "name": "Enstatite",
        "formula": "MgSiO3",
        "formula_atoms": {"Mg": 1, "Si": 1, "O": 3},
        "mineral_class": "silicate",
        "target_elements": ["Mg", "Si"],
        "enrichment_note": "Magnesium silicate reference for Mg/Si phase tracking.",
    },
    {
        "id": "albite",
        "name": "Albite",
        "formula": "NaAlSi3O8",
        "formula_atoms": {"Na": 1, "Al": 1, "Si": 3, "O": 8},
        "mineral_class": "feldspar",
        "target_elements": ["Na", "Al", "Si"],
        "enrichment_note": "Sodium feldspar seed for aluminosilicate classification.",
    },
    {
        "id": "anorthite",
        "name": "Anorthite",
        "formula": "CaAl2Si2O8",
        "formula_atoms": {"Ca": 1, "Al": 2, "Si": 2, "O": 8},
        "mineral_class": "feldspar",
        "target_elements": ["Ca", "Al", "Si"],
        "enrichment_note": "Calcium feldspar reference in plagioclase-rich material.",
    },
    {
        "id": "orthoclase",
        "name": "Orthoclase",
        "formula": "KAlSi3O8",
        "formula_atoms": {"K": 1, "Al": 1, "Si": 3, "O": 8},
        "mineral_class": "feldspar",
        "target_elements": ["K", "Al", "Si"],
        "enrichment_note": "Potassium feldspar seed for K-bearing silicate ranking.",
    },
    {
        "id": "kaolinite",
        "name": "Kaolinite",
        "formula": "Al2Si2O5(OH)4",
        "formula_atoms": {"Al": 2, "Si": 2, "O": 9, "H": 4},
        "mineral_class": "phyllosilicate",
        "target_elements": ["Al", "Si"],
        "enrichment_note": "Clay mineral seed for hydrated aluminosilicate enrichment.",
    },
    {
        "id": "muscovite",
        "name": "Muscovite",
        "formula": "KAl2(AlSi3O10)(OH)2",
        "formula_atoms": {"K": 1, "Al": 3, "Si": 3, "O": 12, "H": 2},
        "mineral_class": "mica",
        "target_elements": ["K", "Al", "Si"],
        "enrichment_note": "Mica seed linking potassium and aluminosilicate signatures.",
    },
    {
        "id": "biotite",
        "name": "Biotite",
        "formula": "K(Mg,Fe)3AlSi3O10(OH)2",
        "formula_atoms": {"K": 1, "Mg": 1.5, "Fe": 1.5, "Al": 1, "Si": 3, "O": 12, "H": 2},
        "mineral_class": "mica",
        "target_elements": ["K", "Mg", "Fe", "Al", "Si"],
        "enrichment_note": "Approximate Mg/Fe mica seed; exact composition varies across the solid solution.",
    },
    {
        "id": "chalcopyrite",
        "name": "Chalcopyrite",
        "formula": "CuFeS2",
        "formula_atoms": {"Cu": 1, "Fe": 1, "S": 2},
        "mineral_class": "sulfide",
        "target_elements": ["Cu", "Fe", "S"],
        "enrichment_note": "Copper iron sulfide candidate for Cu-bearing enrichment.",
    },
    {
        "id": "pyrite",
        "name": "Pyrite",
        "formula": "FeS2",
        "formula_atoms": {"Fe": 1, "S": 2},
        "mineral_class": "sulfide",
        "target_elements": ["Fe", "S"],
        "enrichment_note": "Iron sulfide reference; useful as a sulfide gangue/interference marker.",
    },
    {
        "id": "galena",
        "name": "Galena",
        "formula": "PbS",
        "formula_atoms": {"Pb": 1, "S": 1},
        "mineral_class": "sulfide",
        "target_elements": ["Pb", "S"],
        "enrichment_note": "Lead sulfide seed with very high ideal lead mass percentage.",
    },
    {
        "id": "sphalerite",
        "name": "Sphalerite",
        "formula": "ZnS",
        "formula_atoms": {"Zn": 1, "S": 1},
        "mineral_class": "sulfide",
        "target_elements": ["Zn", "S"],
        "enrichment_note": "Zinc sulfide mineral for Zn-bearing material streams.",
    },
    {
        "id": "pentlandite",
        "name": "Pentlandite",
        "formula": "(Fe,Ni)9S8",
        "formula_atoms": {"Fe": 4.5, "Ni": 4.5, "S": 8},
        "mineral_class": "sulfide",
        "target_elements": ["Ni", "Fe", "S"],
        "enrichment_note": "Approximate Fe-Ni sulfide seed for nickel enrichment ranking.",
    },
    {
        "id": "cobaltite",
        "name": "Cobaltite",
        "formula": "CoAsS",
        "formula_atoms": {"Co": 1, "As": 1, "S": 1},
        "mineral_class": "sulfide",
        "target_elements": ["Co", "As", "S"],
        "enrichment_note": "Cobalt arsenic sulfide seed for Co-bearing mineral search.",
    },
    {
        "id": "monazite",
        "name": "Monazite",
        "formula": "(Ce,La,Nd,Th)PO4",
        "formula_atoms": {"Ce": 0.4, "La": 0.25, "Nd": 0.25, "Th": 0.1, "P": 1, "O": 4},
        "mineral_class": "phosphate",
        "target_elements": ["Ce", "La", "Nd", "Th", "P"],
        "enrichment_note": "Approximate rare-earth phosphate seed; actual REE mix is deposit dependent.",
    },
    {
        "id": "bastnasite",
        "name": "Bastnasite",
        "formula": "(Ce,La)CO3F",
        "formula_atoms": {"Ce": 0.6, "La": 0.4, "C": 1, "O": 3, "F": 1},
        "mineral_class": "carbonate-fluoride",
        "target_elements": ["Ce", "La", "F"],
        "enrichment_note": "Approximate light rare-earth carbonate-fluoride seed.",
    },
    {
        "id": "zircon",
        "name": "Zircon",
        "formula": "ZrSiO4",
        "formula_atoms": {"Zr": 1, "Si": 1, "O": 4},
        "mineral_class": "silicate",
        "target_elements": ["Zr", "Si"],
        "enrichment_note": "Zirconium silicate seed with silicon and zirconium isotope relevance.",
    },
    {
        "id": "uraninite",
        "name": "Uraninite",
        "formula": "UO2",
        "formula_atoms": {"U": 1, "O": 2},
        "mineral_class": "oxide",
        "target_elements": ["U"],
        "enrichment_note": "High uranium oxide seed. Handle only as a data reference, not an operational guide.",
    },
    {
        "id": "cassiterite",
        "name": "Cassiterite",
        "formula": "SnO2",
        "formula_atoms": {"Sn": 1, "O": 2},
        "mineral_class": "oxide",
        "target_elements": ["Sn"],
        "enrichment_note": "Tin oxide seed with high ideal tin mass percentage.",
    },
    {
        "id": "chromite",
        "name": "Chromite",
        "formula": "FeCr2O4",
        "formula_atoms": {"Fe": 1, "Cr": 2, "O": 4},
        "mineral_class": "oxide",
        "target_elements": ["Cr", "Fe"],
        "enrichment_note": "Chromium-bearing spinel seed for Cr enrichment ranking.",
    },
    {
        "id": "vanadinite",
        "name": "Vanadinite",
        "formula": "Pb5(VO4)3Cl",
        "formula_atoms": {"Pb": 5, "V": 3, "O": 12, "Cl": 1},
        "mineral_class": "vanadate",
        "target_elements": ["V", "Pb", "Cl"],
        "enrichment_note": "Lead chlorovanadate seed connecting vanadium and lead-rich signatures.",
    },
    {
        "id": "carnotite",
        "name": "Carnotite",
        "formula": "K2(UO2)2(VO4)2.3H2O",
        "formula_atoms": {"K": 2, "U": 2, "V": 2, "O": 17, "H": 6},
        "mineral_class": "vanadate",
        "target_elements": ["U", "V", "K"],
        "enrichment_note": "Hydrated potassium uranium vanadate seed linking U and V enrichment profiles.",
    },
]


def load_periodic_table(source: Path | None) -> dict:
    if source:
        return json.loads(source.read_text(encoding="utf-8"))

    request = urllib.request.Request(
        PUBCHEM_PERIODIC_TABLE_URL,
        headers={"User-Agent": "knitweb-chemistry-index-builder/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def first_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"unknown", "n/a", "none"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return Decimal(match.group(0))
    except InvalidOperation:
        return None


def json_number(value: object) -> int | float | None | str:
    number = first_decimal(value)
    if number is None:
        return None if value in (None, "", "Unknown") else str(value)
    if number == number.to_integral_value():
        return int(number)
    return float(number)


def decimal_atom_count(value: object) -> Decimal:
    number = Decimal(str(value))
    if number <= 0:
        raise ValueError(f"atom count must be positive, got {value!r}")
    return number


def json_atom_count(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def parse_oxidation_states(value: object) -> tuple[list[str], list[int]]:
    if value is None:
        return [], []
    states: list[str] = []
    charges: list[int] = []
    for raw in str(value).replace("−", "-").split(","):
        part = raw.strip()
        if not part or part.lower() in {"unknown", "none"}:
            continue
        match = re.fullmatch(r"[+-]?\d+", part)
        if not match:
            states.append(part)
            continue
        charge = int(part)
        states.append(f"{charge:+d}" if charge else "0")
        if charge:
            charges.append(charge)
    return states, charges


def ion_label(symbol: str, charge: int) -> str:
    sign = "+" if charge > 0 else "-"
    magnitude = abs(charge)
    suffix = sign if magnitude == 1 else f"{magnitude}{sign}"
    return f"{symbol}{suffix}"


def build_elements(raw_table: dict) -> tuple[list[dict], dict[str, Decimal]]:
    table = raw_table["Table"]
    columns = table["Columns"]["Column"]
    elements: list[dict] = []
    masses: dict[str, Decimal] = {}

    for row in table["Row"]:
        values = dict(zip(columns, row["Cell"], strict=True))
        symbol = values["Symbol"]
        atomic_number = int(values["AtomicNumber"])
        oxidation_states, charges = parse_oxidation_states(values.get("OxidationStates"))
        mass = first_decimal(values.get("AtomicMass"))
        if mass is not None:
            masses[symbol] = mass

        elements.append(
            {
                "id": f"element:{symbol}",
                "atomic_number": atomic_number,
                "symbol": symbol,
                "name": values["Name"],
                "atomic_mass": values.get("AtomicMass"),
                "cpk_hex_color": values.get("CPKHexColor") or None,
                "electron_configuration": values.get("ElectronConfiguration") or None,
                "neutral_electron_count": atomic_number,
                "electronegativity_pauling": json_number(values.get("Electronegativity")),
                "atomic_radius_pm": json_number(values.get("AtomicRadius")),
                "ionization_energy_ev": json_number(values.get("IonizationEnergy")),
                "electron_affinity_ev": json_number(values.get("ElectronAffinity")),
                "oxidation_states": oxidation_states,
                "common_ions": [{"label": ion_label(symbol, charge), "charge": charge} for charge in charges],
                "standard_state": values.get("StandardState") or None,
                "melting_point_k": json_number(values.get("MeltingPoint")),
                "boiling_point_k": json_number(values.get("BoilingPoint")),
                "density_g_cm3": json_number(values.get("Density")),
                "group_block": values.get("GroupBlock") or None,
                "year_discovered": values.get("YearDiscovered") or None,
                "isotope_variants": ISOTOPE_VARIANTS.get(symbol, []),
                "photon_interactions": [
                    "x-ray fluorescence screening",
                    "absorption/emission spectroscopy",
                    "photoelectric edge lookup in lab-grade cross-section tables",
                ],
                "photo_search_urls": [
                    f"https://pubchem.ncbi.nlm.nih.gov/element/{atomic_number}",
                    f"https://commons.wikimedia.org/w/index.php?search={quote_plus(values['Name'] + ' element')}",
                ],
                "source_urls": [
                    PUBCHEM_PERIODIC_TABLE_URL,
                    f"https://pubchem.ncbi.nlm.nih.gov/element/{atomic_number}",
                ],
            }
        )

    return elements, masses


def compute_composition(atoms: dict[str, object], masses: dict[str, Decimal]) -> tuple[dict[str, int | float], list[dict]]:
    counts = {symbol: decimal_atom_count(count) for symbol, count in atoms.items()}
    missing = sorted(symbol for symbol in counts if symbol not in masses)
    if missing:
        raise KeyError(f"missing atomic masses for {', '.join(missing)}")

    total = sum(counts[symbol] * masses[symbol] for symbol in counts)
    rows = []
    for symbol, count in sorted(counts.items()):
        mass = count * masses[symbol]
        bps = int((mass / total * Decimal("10000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        rows.append(
            {
                "symbol": symbol,
                "atom_count": json_atom_count(count),
                "mass_percent_bps": bps,
            }
        )

    delta = 10000 - sum(row["mass_percent_bps"] for row in rows)
    if delta:
        largest = max(rows, key=lambda row: row["mass_percent_bps"])
        largest["mass_percent_bps"] += delta

    rows.sort(key=lambda row: (-row["mass_percent_bps"], row["symbol"]))
    formula_atoms = {symbol: json_atom_count(count) for symbol, count in counts.items()}
    return formula_atoms, rows


def build_minerals(masses: dict[str, Decimal]) -> tuple[list[dict], list[dict], list[dict]]:
    minerals: list[dict] = []
    edges: list[dict] = []
    candidates_by_symbol: dict[str, list[dict]] = {}

    for seed in MINERAL_SEED:
        formula_atoms, composition = compute_composition(seed["formula_atoms"], masses)
        element_symbols = sorted(formula_atoms)
        mineral = {
            **seed,
            "id": f"mineral:{seed['id']}",
            "formula_atoms": formula_atoms,
            "element_symbols": element_symbols,
            "composition_basis": COMPOSITION_BASIS,
            "ideal_formula_mass_percent": composition,
            "photon_interactions": [
                "reflectance and color inspection",
                "Raman/FTIR phase fingerprinting",
                "x-ray fluorescence or diffraction follow-up",
            ],
            "photo_search_urls": [
                f"https://commons.wikimedia.org/w/index.php?search={quote_plus(seed['name'] + ' mineral')}",
                f"https://www.mindat.org/search.php?search={quote_plus(seed['name'])}",
            ],
            "source_urls": [
                f"https://www.mindat.org/search.php?search={quote_plus(seed['name'])}",
            ],
        }
        minerals.append(mineral)

        for row in composition:
            symbol = row["symbol"]
            edge = {
                "source": mineral["id"],
                "target": f"element:{symbol}",
                "rel": "contains-element",
                "weight_bps": row["mass_percent_bps"],
                "basis": COMPOSITION_BASIS,
            }
            edges.append(edge)
            candidates_by_symbol.setdefault(symbol, []).append(
                {
                    "mineral_id": mineral["id"],
                    "mineral_name": mineral["name"],
                    "formula": mineral["formula"],
                    "mass_percent_bps": row["mass_percent_bps"],
                    "composition_basis": COMPOSITION_BASIS,
                }
            )

    profiles = []
    for symbol, candidates in sorted(candidates_by_symbol.items()):
        ranked = sorted(candidates, key=lambda row: (-row["mass_percent_bps"], row["mineral_name"]))
        profiles.append(
            {
                "symbol": symbol,
                "element_id": f"element:{symbol}",
                "candidate_count": len(ranked),
                "top_candidates": ranked[:12],
            }
        )

    return minerals, edges, profiles


def build_dataset(source: Path | None) -> dict:
    raw_table = load_periodic_table(source)
    elements, masses = build_elements(raw_table)
    minerals, edges, profiles = build_minerals(masses)
    element_symbols = {element["symbol"] for element in elements}

    for mineral in minerals:
        unknown = sorted(set(mineral["element_symbols"]) - element_symbols)
        if unknown:
            raise AssertionError(f"{mineral['id']} references unknown elements: {unknown}")

    return {
        "meta": {
            "schema": "knitweb.chemistry-mineral-index.v1",
            "title": "KnitWeb Chemistry + Mineral Enrichment Index",
            "updated_at": date.today().isoformat(),
            "coverage": "pubchem_all_118_elements_curated_mineral_seed_not_exhaustive",
            "weave_kind": "public_p2p_seed_graph",
            "composition_basis": COMPOSITION_BASIS,
            "composition_note": "Percentages are ideal formula mass percentages; real samples and ore bodies vary by deposit and assay.",
            "routes": {
                "github_pages": "https://knitweb.github.io/chemistry-minerals.html",
                "intelfield": "/intel/data/chemistry_minerals.json",
                "display_mirror": "https://5mart.ml/intel/chemistry-minerals.html",
            },
            "sources": [
                {"name": "PubChem periodic table JSON", "url": PUBCHEM_PERIODIC_TABLE_URL},
                {
                    "name": "NIST atomic weights and isotopic compositions",
                    "url": "https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl",
                },
                {"name": "CIAAW isotopic abundances", "url": "https://www.ciaaw.org/isotopic-abundances.htm"},
                {"name": "Mindat mineral search", "url": "https://www.mindat.org/"},
                {"name": "Wikimedia Commons media search", "url": "https://commons.wikimedia.org/"},
            ],
        },
        "elements": elements,
        "minerals": minerals,
        "edges": edges,
        "enrichment_profiles": profiles,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", type=Path, help="Use a local PubChem periodictable JSON snapshot.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    dataset = build_dataset(args.source_json)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.output} with {len(dataset['elements'])} elements, "
        f"{len(dataset['minerals'])} minerals, and {len(dataset['edges'])} contains-element edges."
    )


if __name__ == "__main__":
    main()
