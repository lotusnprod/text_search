'use client'

import * as React from "react";
import {Suspense, useCallback, useRef, useState} from "react";
import "ketcher-react/dist/index.css";
import {Ketcher} from "ketcher-core";
import KetcherLoading from "@/components/KetcherLoading";
import dynamic from "next/dynamic";

const KetcherEditorLotus = React.lazy(
    () => import("../KetcherEditorLotus")
);

export interface KetcherLotusMethods {
    getValue: () => string;
}

interface KetcherLotusProps {
    structure: string
}

const KetcherLotus = React.forwardRef<KetcherLotusMethods, KetcherLotusProps>(
    ({structure}, ref) => {
        React.useImperativeHandle(ref, () => ({
            getValue() {
                const smile = ((global as any).ketcher).getSmiles()
                return smile;
            },
        }));

        const editorusRef = useRef(null);
        const [molecule, setMolecule] = useState<string>(structure);


        const handleKetcherInit = useCallback(
            (ketcher: Ketcher) => {
                ;(global as any).ketcher = ketcher
                if (molecule) { // TODO need to figure that out
                    (global as any).ketcher.setMolecule(molecule);
                }
            },
            [molecule]
        );

        return (
            <div ref={editorusRef}>
                <Suspense fallback={<KetcherLoading/>}>
                    <KetcherEditorLotus
                        height={500}
                        errorHandler={console.error.bind(console)}
                        onInit={handleKetcherInit}
                    />
                </Suspense>
            </div>
        );
    });

export default KetcherLotus;