'use client'

import React, {useEffect, useState} from 'react';
import {fetchStructures} from "@/services/apiService";
import {components} from "@/interfaces/lotus_api";
import Structure from "@/components/Structure";
import {Grid, Sheet} from "@mui/joy";
import {LotusAPIItem, StructureObject} from "@/interfaces/schemas";
import {Pagination} from "@mui/material";
import {Experimental_CssVarsProvider} from "@mui/material/styles";

interface StructureResultProps {
    searchQuery: LotusAPIItem | undefined;
}


const ITEMS_PER_PAGE = 20; // Set the number of items per page


const StructureResult: React.FC<StructureResultProps> = ({searchQuery}) => {
    const [currentPage, setCurrentPage] = useState(1);
    const [apiData, setApiData] = useState<components["schemas"]["StructureResult"] | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => {
        if (searchQuery) {
            setLoading(true)
            fetchStructures(searchQuery).then(setApiData)
                .catch((error) => setError(error.message))
                .finally(() => {
                        setLoading(false)
                        setError(null)
                    }
                );
        }
    }, [searchQuery]);


    const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
        setCurrentPage(value);
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    // Calculate the total number of pages
    const count = apiData ? Object.keys(apiData.objects).length : 0
    const totalPages = apiData &&
    apiData.objects ? Math.ceil(count / ITEMS_PER_PAGE) : 0;

    // Get the current items
    const currentItems: [string, StructureObject][] = apiData && apiData.objects
        ? Object.entries<StructureObject>(apiData.objects)
            .slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
        : [];
    if (count == 0) {
        return <div>No results</div>
    }
    return (<Sheet>
        Structure searching: {count} results
        <Experimental_CssVarsProvider>
            <Pagination page={currentPage} count={totalPages} onChange={handlePageChange}/>
        </Experimental_CssVarsProvider>

        <Grid container spacing={2} sx={{flexGrow: 1}}>
            {currentItems.map(([index, structure]) => (
                structure ? <Grid key={"grid_structure_" + index} xs={4}>
                        <Structure key={"structure_" + index} id={index} structure={structure.smiles || ""}
                                   highlight={searchQuery?.structure?.molecule || ""}/>
                    </Grid>
                    : null
            ))}
        </Grid>
        <Experimental_CssVarsProvider>
            <Pagination page={currentPage} count={totalPages} onChange={handlePageChange}/>
        </Experimental_CssVarsProvider>
    </Sheet>)
}

export default StructureResult
