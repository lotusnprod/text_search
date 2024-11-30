from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class ReferenceOption(BaseModel):
    date_min: Optional[str] = None
    date_max: Optional[str] = None
    journal: Optional[str] = None


class StructureOption(BaseModel):
    descriptors: Optional[Dict[str, int]] = None
    return_descriptors: bool = False
    substructure_search: bool = False
    similarity_level: float = 1.0
    sdf: bool = False


class TaxonOption(BaseModel):
    taxon_children: bool = False


class ReferenceItem(BaseModel):
    wid: Optional[int] = None
    doi: Optional[str] = None
    title: Optional[str] = None
    option: ReferenceOption = ReferenceOption()
    # limit: Optional[int] = None


class StructureItem(BaseModel):
    wid: Optional[int] = None
    molecule: Optional[str] = None
    formula: Optional[str] = None
    option: StructureOption = StructureOption()
    # limit: Optional[int] = None


class TaxonItem(BaseModel):
    wid: Optional[int] = None
    name: Optional[str] = None
    option: TaxonOption = TaxonOption()
    # limit: Optional[int] = None


class Item(BaseModel):
    reference: ReferenceItem = ReferenceItem()
    structure: StructureItem = StructureItem()
    taxon: TaxonItem = TaxonItem()
    limit: Optional[int] = None
    modeEnum: str = "objects"
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reference": {
                        "wid": 44488598,
                        "doi": "10.1080/1057563021000040466",
                        "title": "Iridoids from Seeds of Gentiana Lutea",
                        "option": {
                            "date_min": "1999-12-31",
                            "date_max": "2024-01-01",
                            "journal": "Natural Product Research",
                        },
                    },
                    "structure": {
                        "wid": 27151406,
                        "molecule": "C=C[C@@H]1[C@@H]2CCOC(=O)C2=CO[C@H]1O[C@H]3[C@@H]([C@H]([C@@H]([C@H](O3)CO)O)O)O",
                        "formula": "C16H22O9",
                        "option": {
                            "descriptors": {"NumHAcceptors_min": 1},
                            "return_descriptors": False,
                            "substructure_search": True,
                            "similarity_level": 0.8,
                            "sdf": False,
                        },
                    },
                    "taxon": {
                        "wid": 158572,
                        "name": "Gentiana lutea",
                        "option": {"taxon_children": True},
                    },
                    "limit": 1000,
                    "modeEnum": "ids",
                }
            ]
        }
    }


class ReferenceObject(BaseModel):
    doi: str
    title: str
    date: str
    journal: str


class ReferenceResult(BaseModel):
    ids: List[int]
    objects: Optional[Dict[int, ReferenceObject]] = None
    count: Optional[int]
    description: Optional[str]


class StructureObject(BaseModel):
    smiles: str
    smiles_no_stereo: str
    inchi: str
    inchi_no_stereo: str
    inchikey: str
    inchikey_no_stereo: str
    formula: str
    descriptors: Optional[Dict] = None


class StructureResult(BaseModel):
    ids: List[int]
    objects: Optional[Dict[int, StructureObject]] = None
    sdf: Optional[str] = None
    count: Optional[int]
    description: Optional[str]


class TaxonObject(BaseModel):
    name: str


class TaxonResult(BaseModel):
    ids: List[int]
    objects: Optional[Dict[int, TaxonObject]] = None
    count: Optional[int]
    description: Optional[str]


class TripletResult(BaseModel):
    triplets: List[List[int]]
    references: Optional[Dict[int, ReferenceObject]] = None
    structures: Optional[Dict[int, StructureObject]] = None
    taxa: Optional[Dict[int, TaxonObject]] = None
    count: Optional[int]
    description: Optional[str]


class AutocompleteTaxa(BaseModel):
    taxon_name: str


class DepictionStructure(BaseModel):
    structure: str
    highlight: str | None = None

class StructureDetails(BaseModel):
    inchi: str
    smiles: str
    formula: str
    inchi_no_stereo: str
    inchikey: str
    properties: dict[str, float]
