# Thermal Stability Analysis Tool (Method 2)

A Python/Web-based application for analyzing **Atmospheric Thermal Stability** using meteorological data collected from wind masts. This project converts an existing Excel-based thermal stability calculator into an interactive software application.

---

## Overview

Atmospheric stability plays a crucial role in **Wind Resource Assessment (WRA)**, weather analysis, and renewable energy studies. It determines how air moves vertically in the atmosphere, affecting wind flow, turbulence, and temperature distribution.

This application implements **Method 2** from the provided Thermal Stability Excel tool. It accepts wind speed and temperature measurements from multiple sensor heights, performs the required calculations, and classifies atmospheric stability.

---

## Objectives

- Replace the manual Excel-based workflow with an automated application.
- Implement the complete calculation logic of **Method 2**.
- Accept meteorological data as input.
- Compute all derived parameters automatically.
- Classify atmospheric stability.
- Display results in tables and graphical form.
- Export processed results for further analysis.

---

## Atmospheric Stability

Atmospheric stability describes the tendency of air to resist or enhance vertical motion.

The atmosphere is generally classified into:

- **Stable**
- **Neutral**
- **Unstable**

The classification depends on temperature gradients and wind characteristics measured at different heights.

---

## Method Implemented

This project follows **Method 2** from the provided Thermal Stability tool.

Method 2 uses meteorological measurements collected at multiple elevations and applies the corresponding physical equations to determine atmospheric stability.

---

## Workflow

```text
Upload Input Data
        │
        ▼
Validate Input Parameters
        │
        ▼
Perform Method 2 Calculations
        │
        ▼
Compute Derived Parameters
        │
        ▼
Classify Atmospheric Stability
        │
        ▼
Generate Tables & Graphs
        │
        ▼
Export Results
```

---
