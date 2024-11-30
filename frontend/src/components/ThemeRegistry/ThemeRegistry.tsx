'use client';
import * as React from 'react';
import {CssVarsProvider} from '@mui/joy/styles';
import CssBaseline from '@mui/joy/CssBaseline';
import NextAppDirEmotionCacheProvider from './EmotionCache';
import theme from './theme';
import {Box} from "@mui/joy";
import MenuBar from "@/components/MenuBar";

export default function ThemeRegistry({children}: { children: React.ReactNode }) {
    return (
        <NextAppDirEmotionCacheProvider options={{key: 'joy'}}>
            <CssVarsProvider theme={theme} disableTransitionOnChange>
                <CssBaseline/>
                <Box sx={{display: 'flex', minHeight: '100dvh'}}>
                    <MenuBar/>
                    <Box
                        component="main"
                        className="MainContent"
                        sx={{
                            px: {xs: 2, md: 6},
                            pt: {
                                xs: 'calc(12px + var(--Header-height))',
                                sm: 'calc(12px + var(--Header-height))',
                                md: 3,
                            },
                            pb: {xs: 2, sm: 2, md: 3},
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                            minWidth: 0,
                            height: '100dvh',
                            gap: 1,
                        }}
                    >
                        {children}
                    </Box>
                </Box>
            </CssVarsProvider>
        </NextAppDirEmotionCacheProvider>
    );
}