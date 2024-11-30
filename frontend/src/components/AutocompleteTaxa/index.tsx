import React, {useEffect, useState} from 'react';
import useDebounce from "@/tools/debouncer";
import {autocompleteTaxa} from "@/services/apiService";
import Autocomplete from '@mui/joy/Autocomplete';


interface AutocompleteProps {
    onSelectionChange?: (selectedOption: Options | null) => void;
}

interface Options {
    id: number
    title: string
}

function convertObjectToList(obj: Record<string, any>): Array<{ id: any; title: string }> {
    const resultList: Array<{ id: any; title: string }> = [];

    Object.keys(obj).forEach((key) => {
        resultList.push({id: obj[key], title: key});
    });

    return resultList;
}

function omitKeyAndOwnerState<T extends object>(obj: T): Omit<T, 'key' | 'ownerState'> {
    const {key, ownerState, ...rest} = obj;
    return rest;
}


const AutocompleteTaxa: React.FC<AutocompleteProps> = ({onSelectionChange}) => {
    const [inputValue, setInputValue] = useState('');
    const [suggestions, setSuggestions] = useState<Options[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const debouncedFetchSuggestions = useDebounce(inputValue, 500)


    const fetchSuggestions = async (userInput: string) => {
        if (!userInput || userInput.length < 3) {
            setSuggestions([]);
            return;
        }
        try {
            autocompleteTaxa({taxon_name: userInput}).then((results) =>
                setSuggestions(convertObjectToList(results)))
                .catch((error) => setError(error.message))
                .finally(() => {
                        setLoading(false)
                        setError(null)
                    }
                );
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        }
    };


    useEffect(() => {
        if (debouncedFetchSuggestions) {
            fetchSuggestions(debouncedFetchSuggestions)
        }
    }, [debouncedFetchSuggestions])

    const handleSelectionChange = (event: React.ChangeEvent<{}>, value: Options | null) => {
        if (onSelectionChange !== undefined)
            onSelectionChange(value);
    }

    return (
        <div>
            <Autocomplete
                onInputChange={(e, value) => setInputValue(value)}
                onChange={handleSelectionChange}
                getOptionLabel={(option) => option.title}
                isOptionEqualToValue={(option, value) => option.title === value.title}
                renderOption={(props, option, index) => {
                    const key = `listItem-${index}-${option.id}`;
                    return (
                        <li key={key} {...omitKeyAndOwnerState(props)} >
                            {option.title}
                        </li>

                    );
                }}
                options={suggestions}/>
        </div>
    );
};

export default AutocompleteTaxa;