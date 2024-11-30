'use client'

import React from 'react';

const KetcherLoading = () => {
    return (
        <div className="w-full flex justify-center items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900">
                Loading Ketcher
            </div>
        </div>
    )
}

export default KetcherLoading;