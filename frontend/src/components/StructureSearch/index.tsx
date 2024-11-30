'use client'

import React, {useRef, useState} from "react";
import KetcherLotus, {KetcherLotusMethods} from "@/components/KetcherLotus";
import dynamic from "next/dynamic";
import AutocompleteTaxa from "@/components/AutocompleteTaxa";
import {Chip, FormControl, FormLabel} from "@mui/joy";
import {LotusAPIItem} from "@/interfaces/schemas";

interface StructureSearchProps {
    onSearchSubmit: (searchValue: LotusAPIItem) => void;
}

function parseToIntOrUndefined(str: string | null): number | undefined {
    if (!str) return undefined;
    const num = parseInt(str, 10);
    return isNaN(num) ? undefined : num;
}

const StructureSearch: React.FC<StructureSearchProps> =
    ({onSearchSubmit}) => {
        const hasRunOnce = useRef(false);
        const queryParams = new URLSearchParams(location.search);
        const [substructureSearch, setSubstructureSearch] = useState(false);
        const [selectedTaxa, setSelectedTaxa] =
            useState<number | undefined>(parseToIntOrUndefined(queryParams.get('taxon_wid')));
        const ketcherRef = useRef<KetcherLotusMethods>(null);

        const submit = async () => {
            const smiles = ketcherRef.current ? await ketcherRef.current.getValue() : ""
            var query: LotusAPIItem = {
                taxon: {
                    wid: selectedTaxa
                }
            }
            if (smiles && smiles != "") {
                query["structure"] = {
                    molecule: smiles,
                    option: {substructure_search: substructureSearch}
                }
            }

            onSearchSubmit(query)

        }
        const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
            event.preventDefault()
            submit()
        }

        if (!hasRunOnce.current) {
            // Your code here will run only on the initial render
            hasRunOnce.current = true
            if (queryParams.get('taxon_wid')) {
                submit()
            }
        }

        return (
            <main>
                <div className="w-full">
                    <KetcherLotus ref={ketcherRef}/>
                </div>
                <FormControl>
                    <FormLabel>Restrict by taxon</FormLabel>
                    {
                        queryParams.get('taxon_name') ?
                            <Chip>Searching in {queryParams.get('taxon_name')}</Chip> :
                            <AutocompleteTaxa
                                onSelectionChange={(selectedOption) => setSelectedTaxa(selectedOption?.id)}/>
                    }
                </FormControl>
                <form className="flex flex-col space-y-4" onSubmit={handleSubmit}>
                    <label className="inline-flex items-center">
                        <input className='bg-gray-200 text-black shadow-inner rounded-l p-2 flex-1' id='smiles'
                               type='checkbox'
                               aria-label='Substructure search'
                               onChange={e => setSubstructureSearch(!substructureSearch)}
                        />
                        <span className="ml-2 text-gray-700">Substructure search</span>
                    </label>

                    <button className='bg-blue-600 hover:bg-blue-700 duration-300 text-white shadow p-2 rounded-r'
                            type='submit'>
                        Search structure
                    </button>
                    {}
                </form>
            </main>
        )
    }
export default dynamic(() => Promise.resolve(StructureSearch), {
    ssr: false
})
