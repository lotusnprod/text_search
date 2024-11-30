'use client'

import {StandaloneStructServiceProvider} from "ketcher-standalone";
import React from "react";
import { Editor as KetcherEditor } from "ketcher-react";
import styled from "@emotion/styled";
import { Config } from "ketcher-react/dist/script";
import { Ketcher } from "ketcher-core";
import 'ketcher-react/dist/index.css';
import {createRoot} from "react-dom/client";


const structServiceProvider = new StandaloneStructServiceProvider();

interface KetcherEditorWrapperProps {
  height: number;
}

const KetcherEditorWrapper = styled.div<KetcherEditorWrapperProps>((props) => ({
  height: `${props.height}px`,
}));

KetcherEditorWrapper.defaultProps = {
  // TypeScript has trouble detecting types here because it's a static field.
  // @ts-ignore
  height: "500",
};

export interface KetcherEditorProps
  extends Omit<
    Config,
    "element" | "staticResourcesUrl" | "structServiceProvider"
  > {
  onInit?: (ketcher: Ketcher) => void;
  height: number;
}

export const KetcherEditorLotus = ({
  height,
  ...rest
}: KetcherEditorProps) => (
  <KetcherEditorWrapper height={height}>
    <div id="ketcher-root" />
    <KetcherEditor
      staticResourcesUrl={process.env.PUBLIC_URL!}
      structServiceProvider={structServiceProvider}
      {...rest}
    />
  </KetcherEditorWrapper>
);

export default KetcherEditorLotus;