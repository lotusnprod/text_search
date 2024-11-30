'use client'

import React, {useEffect, useState} from "react";
import Input from "@mui/joy/Input";
import {LotusAPIItem} from "@/interfaces/schemas";
import TaxaResults from "@/components/TaxaResults";
import useDebounce from "@/tools/debouncer";

export default function Page() {
    const [searchQuery, setSearchQuery] = useState<LotusAPIItem>({});
    const [searchQuerySent, setSearchQuerySent] = useState<LotusAPIItem>({});
    const debouncedQuery = useDebounce(searchQuery, 500)

    useEffect(() => {
        if (debouncedQuery) {
            setSearchQuerySent(debouncedQuery)
        }
    }, [debouncedQuery])

    const updateQuery = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery({ taxon: {name: event.target.value }})
    }

    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-24">
            <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
                <Input onChange={updateQuery} />
            </div>
            <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
                <TaxaResults searchQuery={searchQuerySent} />
            </div>
        </main>
    )
}
