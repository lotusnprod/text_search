'use client'

import {Experimental_CssVarsProvider} from '@mui/material/styles';
import React, {useEffect, useState} from 'react';
import {fetchTaxa} from "@/services/apiService";
import {components} from "@/interfaces/lotus_api";
import {Button, Card, Link, Sheet, Table} from "@mui/joy";
import {LotusAPIItem, TaxonObject} from "@/interfaces/schemas";
import {Pagination} from "@mui/material";

interface TaxonResultQuery {
    searchQuery: LotusAPIItem;
}


const ITEMS_PER_PAGE = 20; // Set the number of items per page


const TaxaResults: React.FC<TaxonResultQuery> = ({searchQuery}) => {
    const [currentPage, setCurrentPage] = useState(1);
    const [apiData, setApiData] = useState<components["schemas"]["TaxonResult"] | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => {
        if ((searchQuery.taxon?.name || "") == "") return
        setLoading(true)
        fetchTaxa(searchQuery).then(setApiData)
            .catch((error) => setError(error.message))
            .finally(() => {
                    setLoading(false)
                    setError(null)
                }
            );
    }, [searchQuery]);


    const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
        setCurrentPage(value);
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    // Calculate the total number of pages
    const totalPages = apiData && apiData.objects ? Math.ceil(Object.keys(apiData.objects).length / ITEMS_PER_PAGE) : 0;

    // Get the current items
    const currentItems: [string, TaxonObject][] = apiData && apiData.objects
        ? Object.entries(apiData.objects)
            .slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
        : [];
    if (currentItems.length == 0) {
        return <div>No results</div>
    }
    return (<Sheet>
        Taxon searching
        <Experimental_CssVarsProvider>
            <Pagination page={currentPage} count={totalPages} onChange={handlePageChange} color="primary"/>
        </Experimental_CssVarsProvider>
        <Table aria-label="basic table">
            <thead>
            <tr>
                <th style={{width: '40%'}}>Name</th>
                <th>Structures</th>
                <th>References</th>
            </tr>
            </thead>
            <tbody>
            {currentItems.map(([index, item]) => (
               <tr>
                   <td>
                       <Link href={"/taxon/"+index}>{item.name}</Link>
                   </td>
                   <td><Link href={"/structures?taxon_wid="+encodeURIComponent(index || "")+"&taxon_name="+encodeURIComponent(item.name || "")}>?</Link></td>
                   <td>?</td>
               </tr>
            ))}
            </tbody>
        </Table>

        <Experimental_CssVarsProvider>
            <Pagination page={currentPage} count={totalPages} onChange={handlePageChange} color="primary"/>
        </Experimental_CssVarsProvider>
    </Sheet>)
}

export default TaxaResults
