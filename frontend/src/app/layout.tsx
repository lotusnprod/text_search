import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import React from "react";
import MenuBar from "@/components/MenuBar";
import {Box, CssBaseline, CssVarsProvider} from "@mui/joy";
import ThemeRegistry from "@/components/ThemeRegistry/ThemeRegistry";

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'LOTUS: Natural Products for people by people',
  description: 'We explore new ways to share knowledge in Natural Products research.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
      <ThemeRegistry>{children}</ThemeRegistry>
      </body>
    </html>
  )
}
