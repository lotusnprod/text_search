import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi_versioning import VersionedFastAPI, version

from api.models import (
    AutocompleteTaxa,
    DepictionStructure,
    Item,
    ReferenceObject,
    ReferenceResult,
    StructureObject,
    StructureResult,
    TaxonObject,
    TaxonResult,
    TripletResult, StructureDetails,
)
from api.queries import (
    get_references_for_item,
    get_structures_for_item,
    get_structure_details,
    get_taxa_for_item,
    get_triplets_for_item,
)
from chemistry_helpers import molecule_svg
from model.data_model import DataModel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

description = """
LOTUSFast API helps you do awesome stuff. 🚀
"""

data_model: None | DataModel = None


def get_data_model() -> DataModel:
    """
    A bit messy, but that way we can inject our own in tests
    :return:
    """
    global data_model
    return data_model


app = FastAPI(
    title="LOTUS FastAPI",
    description=description,
    summary="An awesome way to access natural products related data.",
    version="1.0",
    # TODO
    # terms_of_service="http://example.com/terms/",
    # contact={
    #     "name": "Deadpoolio the Amazing",
    #     "url": "http://x-force.example.com/contact/",
    #     "email": "dp@x-force.example.com",
    # },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global data_model
    data_model = DataModel()
    yield
    data_model = None


@app.post("/triplets")
@version(1, 0)
async def search_triplets(
    item: Item, dm: DataModel = Depends(get_data_model)
) -> TripletResult:
    triplets = get_triplets_for_item(item, dm)

    if item.modeEnum == "objects":
        return TripletResult(
            triplets=triplets,
            references={
                wid: value
                for wid, value in dm.get_reference_object_from_dict_of_rids(
                    [reference_id for reference_id, _, _ in triplets]
                ).items()
            },
            structures={
                wid: value
                for wid, value in dm.get_structure_object_from_dict_of_sids(
                    [structure_id for _, structure_id, _ in triplets]
                ).items()
            },
            taxa={
                wid: value
                for wid, value in dm.get_taxon_object_from_dict_of_tids(
                    [taxon_id for _, _, taxon_id in triplets]
                ).items()
            },
            description="Triplets matching the query",
            count=len(triplets),
        )
    else:
        return TripletResult(
            triplets=triplets,
            description="Triplets matching the query",
            count=len(triplets),
        )


@app.post("/structures")
@version(1, 0)
async def search_structures(
    item: Item, dm: DataModel = Depends(get_data_model)
) -> StructureResult:
    dict_items = get_structures_for_item(item, dm)

    if item.structure.option.sdf:
        return StructureResult(
            ids=dict_items.keys(),
            objects={sid: value for sid, value in dict_items.items()},
            sdf=dm.get_structure_sdf_from_dict_of_sids(dict_items),
            description="Structures matching the query",
            count=len(dict_items),
        )
    elif item.modeEnum == "objects":
        return StructureResult(
            ids=dict_items.keys(),
            objects={sid: value for sid, value in dict_items.items()},
            description="Structures matching the query",
            count=len(dict_items),
        )
    else:
        return StructureResult(
            ids=dict_items.keys(),
            description="Structures matching the query",
            count=len(dict_items),
        )

@app.get("/structure")
@version(1, 0)
async def structure_details(structure_id: int, dm: DataModel = Depends(get_data_model)) -> StructureDetails:
        return get_structure_details(structure_id, dm)


@app.post("/taxa")
@version(1, 0)
async def search_taxa(
    item: Item, dm: DataModel = Depends(get_data_model)
) -> TaxonResult:
    dict_items = get_taxa_for_item(item, dm)

    if item.modeEnum == "objects":
        return TaxonResult(
            ids=dict_items.keys(),
            objects={tid: value for tid, value in dict_items.items()},
            description="Taxa matching the query",
            count=len(dict_items),
        )
    else:
        return TaxonResult(
            ids=dict_items.keys(),
            description="Taxa matching the query",
            count=len(dict_items),
        )


@app.post("/references")
@version(1, 0)
async def search_references(
    item: Item, dm: DataModel = Depends(get_data_model)
) -> ReferenceResult:
    dict_items = get_references_for_item(item, dm)

    if item.modeEnum == "objects":
        return ReferenceResult(
            ids=dict_items.keys(),
            objects={rid: value for rid, value in dict_items.items()},
            description="References matching the query",
            count=len(dict_items),
        )
    else:
        return ReferenceResult(
            ids=dict_items.keys(),
            description="References matching the query",
            count=len(dict_items),
        )


@app.post("/autocomplete/taxa")
@version(1, 0)
async def autocomplete_taxa(
    inp: AutocompleteTaxa, dm: DataModel = Depends(get_data_model)
) -> dict[str, int]:
    return dm.get_dict_of_taxa_from_name(inp.taxon_name)


@app.post("/depiction/structure")
@version(1, 0)
async def depiction_structure(
    depiction_structure: DepictionStructure,
) -> dict[str, str]:
    return {
        "svg": molecule_svg(
            depiction_structure.structure, highlight=depiction_structure.highlight
        )
    }


@app.get("/descriptors/")
@version(1, 0)
async def get_descriptors():
    from rdkit.Chem import Descriptors

    return [desc[0] for desc in Descriptors._descList]


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "logging.Formatter",
            "fmt": "%(levelname)s %(name)s@%(lineno)d %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "my_project.ColorStreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": "TRACE"},
    },
}

app = VersionedFastAPI(
    app, enable_latest=True, log_config=LOGGING_CONFIG, lifespan=lifespan
)
