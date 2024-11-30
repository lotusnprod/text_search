'use client'

import React, { useState, useEffect } from 'react';
import {structureDepiction} from "@/services/apiService";

interface SvgRendererProps {
  structure: string;
  highlight: string;
}

const SvgRenderer: React.FC<SvgRendererProps> = ({ structure, highlight }) => {
  const [svgContent, setSvgContent] = useState<string>('');

  useEffect(() => {
    const fetchSvg = async () => {
      try {
        const svgData = await structureDepiction({structure: structure, highlight: highlight});
        if (svgData.svg === undefined) {
          return;
        }
        setSvgContent(svgData.svg);
      } catch (error) {
        console.error('Error fetching SVG:', error);
      }
    };

    fetchSvg();
  }, []);

  return (
    <div>
      {/* If the SVG is XML text, use dangerouslySetInnerHTML */}
      <div dangerouslySetInnerHTML={{ __html: svgContent }} />

      {/* If the SVG is a URL, use an img tag */}
      {/* <img src={svgContent} alt="SVG from API" /> */}
    </div>
  );
};

export default SvgRenderer;
