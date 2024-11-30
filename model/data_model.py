import functools
import io
import logging
import pickle
from collections.abc import Iterable
from pathlib import Path

import requests
from rdkit import Chem, DataStructs
from rdkit.Chem import rdSubstructLibrary
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import aliased

from api.models import ReferenceObject, StructureObject, TaxonObject, StructureDetails
from chemistry_helpers import fingerprint, standardize
from sdf_helpers import find_structures_bytes_ranges, mmap_file, read_selected_ranges
from storage.models import (
    Journals,
    References,
    Structures,
    StructuresDescriptors,
    TaxoNames,
    TaxoParents,
    TaxoRankNames,
    TaxoRanks,
    Triplets,
)
from storage.storage import Storage

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.WARNING)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.WARNING)
requests_log.propagate = True


class DataModel:
    def __init__(self, path: Path = Path("./data")):
        self.db = self.load_all_data(path)
        # TODO add descriptors
        self.sdf = self.load_sdf_data(path)
        self.sdf_ranges = self.load_sdf_ranges(self.sdf)
        self.storage = Storage(path)
        self.taxa_name_db = self.preload_taxa()
        self.path = path

    @classmethod
    @functools.lru_cache(maxsize=None)
    def load_all_data(cls, path: Path):
        with open(path / "database_chemo.pkl", "rb") as f:
            data = pickle.load(f)
        new_lib = rdSubstructLibrary.SubstructLibrary()
        new_lib_h = rdSubstructLibrary.SubstructLibrary()
        with io.BytesIO(data["structure_library"]) as i:
            new_lib.InitFromStream(i)
        with io.BytesIO(data["structure_library_h"]) as i:
            new_lib_h.InitFromStream(i)
        data["structure_library"] = new_lib
        data["structure_library_h"] = new_lib_h
        return data

    @classmethod
    @functools.lru_cache(maxsize=None)
    def load_sdf_data(cls, path: Path):
        mmaped_sdf = mmap_file(path / "lotus.sdf")
        return mmaped_sdf

    @classmethod
    @functools.lru_cache(maxsize=None)
    def load_sdf_ranges(cls, sdf):
        ranges = find_structures_bytes_ranges(sdf)
        return ranges

    ### Taxonomy
    def get_taxon_object_from_dict_of_tids(
            self, tids: Iterable[int]
    ) -> dict[int, TaxonObject]:
        with self.storage.session() as session:
            result = (
                session.query(
                    TaxoNames.id,
                    TaxoNames.name,
                )
                .filter(TaxoNames.id.in_(tids))
                .all()
            )

            if result:
                return {
                    row.id: TaxonObject(
                        name=row.name,
                    )
                    for row in result
                }
            else:
                return {}

    def get_taxon_object_from_tid(self, tid: int) -> dict | None:
        return self.get_taxon_object_from_dict_of_tids([tid])

    def get_taxa_with_name_matching(self, query: str, exact=False) -> set[int]:
        with self.storage.session() as session:
            if exact:
                matcher = TaxoNames.name == query
            else:
                matcher = TaxoNames.name.like(f"%{query}%")
            result = session.query(TaxoNames.id).filter(matcher)
            return {row[0] for row in result}

    def get_rank_name_from_wid(self, wid: int) -> str | None:
        with self.storage.session() as session:
            result = session.get(TaxoRankNames, wid)
            if result is None:
                return None
            return result.name

    def resolve_taxon(self, query: str) -> any:
        query = {
            "nameStrings": [query],
            "withVernaculars": False,
            "withCapitalization": True,
            "withAllMatches": True,
        }
        log.debug(f"Querying GN resolver... {query}")

        try:
            response = requests.post(
                "https://verifier.globalnames.org/api/v1/verifications",
                json=query,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            log.error(f"Impossible to connect to GN resolver {e}.")
            return None
        log.debug(response.json())
        return response.json()

    def get_ranks_string(self, wid: int) -> str:
        with self.storage.session() as session:
            result = session.query(TaxoRanks.rank_id).filter(TaxoRanks.id == wid)
            rank_ids = [row[0] for row in result]
        if len(rank_ids) > 0:
            n_ranks = [self.get_rank_name_from_wid(int(it)) for it in rank_ids]
            ranks = " (" + ", ".join(set(n_ranks)) + ")"
        else:
            ranks = ""
        return ranks

    ### Structureonomy
    @functools.lru_cache(maxsize=None)
    def structures_set(self) -> set[int]:
        # TODO use DB
        return set(self.db["structure_wid"])

    def get_structure_object_from_sid(self, sid: int) -> dict | None:
        return self.get_structure_object_from_dict_of_sids([sid])

    def get_structure_descriptors_from_dict_of_sids(
            self, sids: Iterable[int]
    ) -> Iterable[tuple[int, str]]:
        with self.storage.session() as session:
            result = (
                session.query(
                    StructuresDescriptors.descriptor_name,
                    StructuresDescriptors.descriptor_value,
                )
                .filter(StructuresDescriptors.structure_id.in_(sids))
                .distinct()
                .all()
            )
            result_dict = {}
            if result:
                for descriptor_name, descriptor_value in result:
                    if descriptor_name in result_dict:
                        result_dict[descriptor_name].append(descriptor_value)
                    else:
                        result_dict[descriptor_name] = [descriptor_value]
                return result_dict
            else:
                return result_dict

    def get_structure_sdf_from_dict_of_sids(
            self, sids: Iterable[int]
    ) -> Iterable[tuple[int, str]]:
        ranges = self.sdf_ranges
        blocks = []
        for sid in sids:
            blocks.append(read_selected_ranges(self.sdf, [ranges[sid]]))
        return "".join(blocks)

    def get_structure_object_from_dict_of_sids(
            self,
            sids: Iterable[int],
            return_descriptors: bool = False,
    ) -> dict[int, StructureObject]:
        with self.storage.session() as session:
            descriptors = {}
            if return_descriptors:
                descriptors = self.get_structure_descriptors_from_dict_of_sids(sids)
            result = (
                session.query(
                    Structures.id,
                    Structures.smiles,
                    Structures.smiles_no_stereo,
                    Structures.inchi,
                    Structures.inchi_no_stereo,
                    Structures.inchikey,
                    Structures.inchikey_no_stereo,
                    Structures.formula,
                )
                .filter(Structures.id.in_(sids))
                .all()
            )
            if result:
                return {
                    row.id: StructureObject(
                        smiles=row.smiles,
                        smiles_no_stereo=row.smiles_no_stereo,
                        inchi=row.inchi,
                        inchi_no_stereo=row.inchi_no_stereo,
                        inchikey=row.inchikey,
                        inchikey_no_stereo=row.inchikey_no_stereo,
                        formula=row.formula,
                        descriptors=descriptors,
                    )
                    for row in result
                }
            else:
                return {}

    def get_structure_with_descriptors(self, descriptors: dict) -> set[int]:
        with self.storage.session() as session:
            query = session.query(StructuresDescriptors.structure_id)

            # Separate descriptors into min and max dictionaries
            min_descriptors = {}
            max_descriptors = {}
            for key, value in descriptors.items():
                descriptor_name = key[:-4]  # Remove "_min" or "_max" suffix
                if key.endswith("_min"):
                    min_descriptors[descriptor_name] = value
                if key.endswith("_max"):
                    max_descriptors[descriptor_name] = value

            # Apply min and max filters separately
            query_min = None
            for descriptor_name, min_value in min_descriptors.items():
                min_condition = (
                    StructuresDescriptors.descriptor_name == descriptor_name,
                    StructuresDescriptors.descriptor_value >= min_value,
                )
                query_min = query.filter(and_(*min_condition))

            query_max = None
            for descriptor_name, max_value in max_descriptors.items():
                max_condition = (
                    StructuresDescriptors.descriptor_name == descriptor_name,
                    StructuresDescriptors.descriptor_value <= max_value,
                )
                query_max = query.filter(and_(*max_condition))

            # Intersect the results of min and max queries
            if query_min is not None and query_max is not None:
                result = query_min.intersect(query_max).all()
            elif query_min is not None:
                result = query_min.all()
            elif query_max is not None:
                result = query_max.all()
            else:
                result = query.all()
            return {row[0] for row in result}

    def get_structure_with_formula(self, formula: str) -> set[int]:
        with self.storage.session() as session:
            result = session.query(Structures.id).filter(Structures.formula == formula)
            return {row[0] for row in result}

    def structure_get_mol_fp_and_explicit(self, query: str) -> tuple[any, any, bool]:
        explicit_h = "[H]" in query
        p = Chem.SmilesParserParams()
        p.removeHs = not explicit_h
        mol = Chem.MolFromSmiles(query, p)

        if not explicit_h:
            mol = standardize(mol)

        fp = fingerprint(mol)
        return mol, fp, explicit_h

    ## COMMENT (AR): Should we rename this to structure_search_from_smiles
    ## and have same for InChI and co and then wrap them to a `structure_search`
    ## with inchi = "InChI=1S/" in query ...
    def structure_search(self, query: str) -> list[tuple[int, float]]:
        mol, fp, explicit_h = self.structure_get_mol_fp_and_explicit(query)

        if explicit_h:
            db = self.db["structure_sim_h_fps"]
        else:
            db = self.db["structure_sim_fps"]
        scores = DataStructs.BulkTanimotoSimilarity(fp, db)
        return [(wid, score) for wid, score in zip(self.db["structure_wid"], scores)]

    def structure_search_substructure(
            self, query: str, chirality: bool = False
    ) -> list[tuple[int, float]]:
        mol, fp, explicit_h = self.structure_get_mol_fp_and_explicit(query)

        if explicit_h:
            db = self.db["structure_library_h"]
            fp_db = self.db["structure_sim_h_fps"]
        else:
            db = self.db["structure_library"]
            fp_db = self.db["structure_sim_fps"]

        iids = db.GetMatches(
            mol,
            numThreads=-1,
            maxResults=-1,
            useQueryQueryMatches=True,
            useChirality=chirality,
        )
        # TODO letting WID for now (also in data_structures) but to keep in mind
        new_keys = [self.db["structure_wid"][iid] for iid in iids]
        out = []
        for iid, wid in zip(iids, new_keys):
            out.append((wid, DataStructs.TanimotoSimilarity(fp, fp_db[iid])))
        return out

    def structure_get_tsv_from_scores(self, wids: list[int], scores) -> str:
        out = "Wikidata link\tSimilarity\tSmiles\n"
        structure_objects = self.get_structure_object_from_dict_of_sids(wids)
        smiles_dict = {
            wid: structure_object.smiles
            for wid, structure_object in structure_objects.items()
        }
        for idx, score in enumerate(scores):
            wid = wids[idx]
            smiles = smiles_dict[wid]
            out += f"http://www.wikidata.org/entity/Q{wid}\t{score:.3f}\t{smiles}\n"
        return out

    ### Biblionomy
    def get_reference_with_id(self, rid: int) -> set[int]:
        with self.storage.session() as session:
            result = session.query(References.id).filter(References.id == rid)
            return {row[0] for row in result}

    def get_reference_object_from_dict_of_rids(
            self, rids: Iterable[int]
    ) -> dict[int, ReferenceObject]:
        with self.storage.session() as session:
            result = (
                session.query(
                    References.id,
                    References.doi,
                    References.title,
                    References.date,
                    References.journal,
                )
                .filter(References.id.in_(rids))
                .all()
            )

            journal_ids = {row.journal for row in result}

            journal_titles = {}
            if journal_ids:  # Only query if there are journal IDs
                result_journal = session.query(
                    Journals.id,
                    Journals.title,
                ).filter(Journals.id.in_(journal_ids))
                journal_titles = {
                    journal.id: journal.title for journal in result_journal
                }

            if result:
                return {
                    row.id: ReferenceObject(
                        doi=row.doi,
                        title=row.title,
                        date=row.date,
                        journal=journal_titles.get(row.journal),
                    )
                    for row in result
                }
            else:
                return {}

    def get_reference_object_from_rid(self, rid: int) -> dict | None:
        return self.get_reference_object_from_dict_of_rids([rid])

    def get_references_with_doi(self, doi: str) -> set[int]:
        with self.storage.session() as session:
            result = session.query(References.id).filter(
                References.doi.like(f"%{doi}%")
            )
            return {row[0] for row in result}

    def get_references_with_date(
            self, date_min: str = None, date_max: str = None
    ) -> set[int]:
        with self.storage.session() as session:
            query = session.query(References.id)
            if date_min is not None and date_max is not None:
                query = query.filter(References.date.between(date_min, date_max))
            elif date_min is not None:
                query = query.filter(References.date >= date_min)
            elif date_max is not None:
                query = query.filter(References.date <= date_max)
            result = query.all()
            return {row[0] for row in result}

    def get_references_with_journal(self, journal_title: str) -> set[int]:
        with self.storage.session() as session:
            result = (
                session.query(References.id)
                .filter(
                    References.journal.in_(
                        session.query(Journals.id).filter(
                            Journals.title.like(f"%{journal_title}%")
                        )
                    )
                )
                .all()
            )
            return {row[0] for row in result}

    def get_references_with_title(self, title: str) -> set[int]:
        with self.storage.session() as session:
            result = session.query(References.id).filter(
                References.title.like(f"%{title}%")
            )
            return {row[0] for row in result}

    ### Mixonomy
    # Todo, we probably want to still return that as a set
    def get_structures_of_taxon(self, tid: int, recursive: bool = True) -> set[int]:
        matching_structures = self.storage.get_generic_of_generic(
            Triplets.structure_id, Triplets.taxon_id, tid
        )

        if recursive:
            with self.storage.session() as session:
                # if exist
                result = session.query(TaxoParents.child_id).filter(
                    TaxoParents.parent_id == tid
                )

                for row in result:
                    for structure in self.get_structures_of_taxon(row[0]):
                        matching_structures.add(structure)
        return matching_structures

    def get_taxa_of_structure(self, sid: int) -> set[int]:
        return self.storage.get_generic_of_generic(
            Triplets.taxon_id, Triplets.structure_id, sid
        )

    def get_structures_of_reference(self, rid: int) -> set[int]:
        return self.storage.get_generic_of_generic(
            Triplets.structure_id, Triplets.reference_id, rid
        )

    def get_taxa_of_reference(self, rid: int) -> set[int]:
        return self.storage.get_generic_of_generic(
            Triplets.taxon_id, Triplets.reference_id, rid
        )

    def get_references_of_structure(self, sid: int) -> set[int]:
        return self.storage.get_generic_of_generic(
            Triplets.reference_id, Triplets.structure_id, sid
        )

    def get_references_of_taxon(self, tid: int) -> set[int]:
        return self.storage.get_generic_of_generic(
            Triplets.reference_id, Triplets.taxon_id, tid
        )

    def get_references_of_structures(self, structures: set[int]) -> set[int]:
        return self.storage.get_generics_of_generics(
            Triplets.reference_id, Triplets.structure_id, structures
        )

    def get_references_of_taxa(self, taxa: set[int]) -> set[int]:
        return self.storage.get_generics_of_generics(
            Triplets.reference_id, Triplets.taxon_id, taxa
        )

    def get_structures_of_references(self, references: set[int]) -> set[int]:
        return self.storage.get_generics_of_generics(
            Triplets.structure_id, Triplets.reference_id, references
        )

    def get_taxa_of_structures(self, structures: set[int]) -> set[int]:
        return self.storage.get_generics_of_generics(
            Triplets.taxon_id, Triplets.structure_id, structures
        )

    def get_taxa_of_references(self, references: set[int]) -> set[int]:
        return self.storage.get_generics_of_generics(
            Triplets.taxon_id, Triplets.reference_id, references
        )

    def get_triplets_for(
            self,
            reference_ids: set[int] | None,
            structure_ids: set[int] | None,
            taxon_ids: set[int] | None,
    ) -> set[tuple[int, int, int]]:
        return self.storage.get_triplets_for(reference_ids, structure_ids, taxon_ids)

    def get_taxon_by_id(self, tid: int) -> set[int]:
        with self.storage.session() as session:
            result = session.query(Triplets.taxon_id).filter(Triplets.taxon_id == tid)
            return {row[0] for row in result.distinct()}

    def get_taxon_children_by_id(self, tid: int) -> set[int]:
        with self.storage.session() as session:
            # Recursive query to fetch all children for the given taxon ID
            recursive_query = (
                session.query(TaxoParents.child_id)
                .filter(TaxoParents.parent_id == tid)
                .cte(name="recursive_query", recursive=True)
            )

            alias = aliased(TaxoParents)
            recursive_query = recursive_query.union_all(
                session.query(alias.child_id).filter(
                    alias.parent_id == recursive_query.c.child_id
                )
            )

            result = set(session.query(recursive_query).all())

            ## This is working but not recursively to get all children
            # result = session.query(TaxoParents.id).filter(
            #     TaxoParents.parent_id == tid
            # )
            return {row[0] for row in result}

    def preload_taxa(self):
        with self.storage.session() as session:
            result = session.query(TaxoNames.id, TaxoNames.name).all()
            return {row[1]: row[0] for row in result}

    def get_dict_of_taxa_from_name(self, taxon_name: str) -> dict[str, int]:
        with self.storage.session() as session:
            matcher = TaxoNames.name.like(f"{taxon_name}%")
            result = session.query(TaxoNames.name, TaxoNames.id).filter(matcher)
        return {row[0]: row[1] for row in result}

    def get_structure_details(self, structure_id: int) -> StructureDetails:
        with (self.storage.session() as session):
            structure_details = session.query(Structures.inchi,
                                              Structures.smiles, Structures.formula, Structures.inchi_no_stereo,
                                              Structures.inchikey
                                              ).filter(Structures.id == structure_id).first()
            structure_descriptors = session.query(StructuresDescriptors.descriptor_name,
                                                  StructuresDescriptors.descriptor_value).filter(
                StructuresDescriptors.structure_id == structure_id)

            properties = {item[0]: float(item[1]) for item in structure_descriptors}

            return StructureDetails(
                inchi=structure_details.inchi,
                smiles=structure_details.smiles,
                formula=structure_details.formula,
                inchi_no_stereo=structure_details.inchi_no_stereo,
                inchikey=structure_details.inchikey,
                properties=properties
            )
