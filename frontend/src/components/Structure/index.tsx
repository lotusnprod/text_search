'use client'

import React from 'react';
import MoleculeStructure from "@/components/MoleculeStructure";

interface Prout {
    // Define the structure of the prout object here
}

interface StructureProps {
    id: string;
    structure: string;
    highlight: string;
}

const Structure: React.FC<StructureProps> = ({id, structure, highlight}) => {
    return (
        <div className="mr-4 mb-1 p-4 bg-gray-200">
            <MoleculeStructure
                structure={structure} highlight={highlight}
            />
            <a href={`https://www.wikidata.org/wiki/Q${id}`} className="text-black">Q{id} - Wikidata page</a>
        </div>
    );
};

export default Structure;
