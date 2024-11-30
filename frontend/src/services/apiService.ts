import {components} from "@/interfaces/lotus_api";

async function callApi<T, U>(url: string, body: T): Promise<U> {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error(response.statusText);
    }
    return await response.json();
}

export const fetchStructures = async (input: components["schemas"]["item"]): Promise<components["schemas"]["StructureResult"]> => {
    return callApi('/api/v1_0/structures', input)
}

export const fetchTaxa = async (input: components["schemas"]["item"]): Promise<components["schemas"]["TaxonResult"]> => {
    return callApi('/api/v1_0/taxa', input)
}

export const autocompleteTaxa = async (input: components["schemas"]["taxaQuery"]): Promise<components["schemas"]["taxaResult"]> => {
    return callApi('/api/v1_0/autocomplete/taxa', input)

}

export const structureDepiction = async (input: components["schemas"]["depictStructureQuery"]): Promise<components["schemas"]["depictStructureResponse"]> => {
   return callApi('/api/v1_0/depiction/structure', input)
}
