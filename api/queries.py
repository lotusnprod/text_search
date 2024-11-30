import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status

from api.models import (
    Item,
    ReferenceItem,
    ReferenceOption,
    StructureItem,
    StructureOption,
    TaxonItem,
    TaxonOption, StructureDetails, TaxonObject, ReferenceObject,
)
from model.data_model import DataModel
from storage.models import Structures

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_date(date_str: str) -> datetime:
    # TODO this has to be explained in the API doc
    formats = ["%Y", "%Y-%m", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid date format",
    )


def references_from_reference_in_item(dm: DataModel, item: Item) -> set[int] | None:
    """Returns the WID of matching references."""
    references = None

    wid = item.reference.wid
    doi = item.reference.doi
    title = item.reference.title
    date_min = item.reference.option.date_min
    date_max = item.reference.option.date_max
    journal = item.reference.option.journal

    if len([param for param in [wid, doi, title] if param is not None]) >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only one of ['wid', 'doi', 'title'] should be provided",
        )
    elif wid is not None or doi is not None or title is not None:
        if wid:
            references = dm.get_reference_with_id(wid)
        elif doi:
            references = dm.get_references_with_doi(doi)
        elif title:
            references = dm.get_references_with_title(title)

    if date_min is not None or date_max is not None:
        if date_min is not None:
            date_min = parse_date(date_min)
        if date_max is not None:
            date_max = parse_date(date_max)
        references_within_date_range = dm.get_references_with_date(date_min, date_max)
        if references is None:
            references = references_within_date_range
        else:
            references &= references_within_date_range

    if journal:
        references_with_journal = dm.get_references_with_journal(journal)
        if references is None:
            references = references_with_journal
        else:
            references &= references_with_journal

        return references
    else:
        return references


def structures_from_structure_in_item(dm: DataModel, item: Item) -> set[int] | None:
    """Returns the WID of matching structures."""
    structures = None

    wid = item.structure.wid
    molecule = item.structure.molecule
    formula = item.structure.formula
    sub = item.structure.option.substructure_search
    sim = item.structure.option.similarity_level
    descriptors = item.structure.option.descriptors

    args = len([param for param in [wid, molecule, formula] if param is not None])

    if args > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only one of ['wid', 'molecule', 'formula'] should be provided",
        )
    elif args > 0:
        # This needs to be explained in the API doc
        if wid:
            if wid in dm.structures_set():
                return {wid}
            else:
                return set()

        if sub:
            try:
                results = dm.structure_search_substructure(molecule)
                structures = {_id for _id, _ in results}
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"The structure given is invalid: {molecule}",
                )

        elif formula:
            try:
                structures = dm.get_structure_with_formula(formula)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"The formula given is invalid: {formula}",
                )

        elif molecule:
            try:
                results = dm.structure_search(molecule)
                structures = {_id for _id, score in results if score >= sim}
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"The structure given is invalid: {molecule}",
                )

        return structures

    if descriptors is not None:
        try:
            structures_with_descriptors = dm.get_structure_with_descriptors(descriptors)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"The descriptors given are invalid: {descriptors}",
            )
        if structures is None:
            structures = structures_with_descriptors
        else:
            structures &= structures_with_descriptors

    return structures


def taxa_from_taxon_in_item(dm: DataModel, item: Item) -> set[int] | None:
    """Returns the WID of matching taxa."""
    wid = item.taxon.wid
    name = item.taxon.name
    children = item.taxon.option.taxon_children

    if len([param for param in [wid, name] if param is not None]) >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only one of ['wid', 'name'] should be provided",
        )
    if wid is not None or name is not None:
        # This needs to be explained in the API doc
        if wid:
            return (
                {child for child in dm.get_taxon_children_by_id(wid)}
                if children
                else dm.get_taxon_by_id(wid)
            )
        elif name:
            t = dm.get_taxa_with_name_matching(name)
            return (
                {child for tt in t for child in dm.get_taxon_children_by_id(tt)}
                if children
                else t
            )

    return None


def references_from_structure_in_item(dm: DataModel, item: Item) -> set[int] | None:
    structures = structures_from_structure_in_item(dm, item)

    if structures is None:
        return None

    return dm.get_references_of_structures(structures)


def references_from_taxon_in_item(dm: DataModel, item: Item) -> set[int] | None:
    taxa = taxa_from_taxon_in_item(dm, item)

    if taxa is None:
        return None

    return dm.get_references_of_taxa(taxa)


def structures_from_reference_in_item(dm: DataModel, item: Item) -> set[int] | None:
    references = references_from_reference_in_item(dm, item)

    if references is None:
        return None

    return dm.get_structures_of_references(references)


def structures_from_taxon_in_item(dm: DataModel, item: Item) -> set[int] | None:
    taxa = taxa_from_taxon_in_item(dm, item)

    if taxa is None:
        return None

    # TODO Set recursive=True to have all the structures from the parents too?
    #      We may have issues if we have a lot, and it will require a bit more work to get it with the db
    #      We could also have all the parenting relations in the DB and it would be much much faster
    out = set()
    for taxon in taxa:
        out.update(dm.get_structures_of_taxon(taxon))

    return out


def taxa_from_structure_in_item(dm: DataModel, item: Item) -> set[int] | None:
    structures = structures_from_structure_in_item(dm, item)

    if structures is None:
        return None

    return dm.get_taxa_of_structures(structures)


def taxa_from_reference_in_item(dm: DataModel, item: Item) -> set[int] | None:
    references = references_from_reference_in_item(dm, item)

    if references is None:
        return None

    return dm.get_taxa_of_references(references)


def combine_and_filter_outputs(sets: list[set], limit: int) -> list[int]:
    non_none_outputs = [s for s in sets if s is not None]

    items = list(set.intersection(*non_none_outputs) if non_none_outputs else set())

    if limit == 0:
        return items
    else:
        return items[:limit]


def apply_limit(item: Item, items: list[Any] | set[Any]) -> list[Any]:
    lim = item.limit

    if lim == 0:
        return list(items)
    else:
        return list(items)[:lim]


def get_triplets_for_item(item: Item, dm: DataModel) -> list[tuple[int, int, int]]:
    triplets_set = dm.get_triplets_for(
        reference_ids=references_from_reference_in_item(dm, item),
        structure_ids=structures_from_structure_in_item(dm, item),
        taxon_ids=taxa_from_taxon_in_item(dm, item),
    )

    return apply_limit(item, triplets_set)


def get_structures_for_item(item: Item, dm: DataModel) -> dict[int, str]:
    ids = combine_and_filter_outputs(
        [
            structures_from_structure_in_item(dm, item),
            structures_from_taxon_in_item(dm, item),
            structures_from_reference_in_item(dm, item),
        ],
        limit=item.limit,
    )

    return dm.get_structure_object_from_dict_of_sids(
        ids, item.structure.option.return_descriptors
    )


def get_taxa_for_item(item: Item, dm: DataModel) -> dict[int, TaxonObject]:
    ids = combine_and_filter_outputs(
        [
            taxa_from_taxon_in_item(dm, item),
            taxa_from_structure_in_item(dm, item),
            taxa_from_reference_in_item(dm, item),
        ],
        limit=item.limit,
    )

    return dm.get_taxon_object_from_dict_of_tids(ids)


def get_references_for_item(item: Item, dm: DataModel) -> dict[int, ReferenceObject]:
    ids = combine_and_filter_outputs(
        [
            references_from_reference_in_item(dm, item),
            references_from_structure_in_item(dm, item),
            references_from_taxon_in_item(dm, item),
        ],
        limit=item.limit,
    )

    return dm.get_reference_object_from_dict_of_rids(ids)


def get_structure_details(structure_id: int, dm: DataModel) -> StructureDetails:
    return dm.get_structure_details(structure_id)
