# Circular RCC Section Design & Analysis Tool

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![IS 456](https://img.shields.io/badge/Design%20Code-IS%20456%3A2000-orange)](#design-codes)
[![IRC 112](https://img.shields.io/badge/Shear-IRC%3A112--2011-green)](#shear-analysis)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
---
> **Use**
[![Python IDE](https://img.shields.io/badge/IDE-Python%20IDE-3776AB?logo=python&logoColor=white)](https://www.onlineide.pro/playground/python?utm_source=online-python&utm_medium=navbar&utm_campaign=onlineidepro)

> **A calculation-oriented Python tool for structural engineers to analyse circular reinforced-concrete (RCC) sections for axial load, uniaxial/biaxial bending, shear and serviceability checks.**

---

## 📌 Overview

This project provides a numerical analysis framework for **circular reinforced concrete sections**. It combines:

- Fibre-based section discretisation
- Reinforcement-layer modelling
- Nonlinear ULS strain compatibility
- Biaxial bending interaction checking
- Cracked-section SLS analysis
- Shear checks using **IS 456:2000**
- Shear checks using a simplified **IRC:112-2011** approach

The flexural module models concrete and reinforcement at discrete fibres/bars and calculates internal axial force and bending moments from the resulting strain distribution. The shear module evaluates concrete shear resistance and, where required, the contribution of shear reinforcement.

---

## ✨ Key Features

<details>
<summary><b>Click to expand — Flexural Analysis</b></summary>

### Circular RC Section

- User-defined section diameter and clear cover
- Arbitrary reinforcement layers
- Single bars
- Two-bar bundles
- Three-bar triplets
- Multiple reinforcement layers
- Automatic calculation of total steel area and reinforcement percentage

### ULS Analysis

- Concrete parabolic-rectangular stress model
- Bilinear steel stress model
- Axial load + biaxial bending
- Uniaxial moment capacity about X and Y axes
- Strain compatibility and curvature-based analysis
- Biaxial interaction ratio
- `alpha_n` calculation for the interaction equation
- Safe / Not Safe assessment

The implementation explicitly identifies the biaxial check with **IS 456:2000 Clause 39.6**.

</details>

<details>
<summary><b>Click to expand — Serviceability Analysis</b></summary>

### SLS Checks

- Cracked-section analysis
- Linear elastic concrete in compression
- Linear elastic reinforcement
- Concrete compressive stress
- Steel tensile stress
- Approximate crack-width calculation
- Comparison against permissible limits

</details>

<details>
<summary><b>Click to expand — Shear Analysis</b></summary>

### IS 456:2000

The shear module includes:

- Design shear strength of concrete, `τc`
- Table 19 interpolation
- Effect of axial compression
- Nominal shear stress, `τv`
- Minimum shear reinforcement
- Stirrup contribution
- Total shear capacity
- Safe / Not Safe assessment

The implementation uses the Table 19 values embedded in the supplied calculation module and interpolates for percentage steel and concrete strength. fileciteturn1file0L3-L20

### IRC:112-2011

The module includes a simplified shear-resistance calculation using:

- Design material strengths
- Longitudinal reinforcement ratio
- Axial compression stress
- `k` factor
- Concrete shear resistance `V_Rd,c`
- Minimum shear resistance
- Shear reinforcement resistance `V_Rd,s`
- Maximum shear resistance `V_Rd,max`
- Final safety check

</details>

---

## 🧮 Analysis Workflow

```text
                ┌───────────────────────┐
                │ Circular RC Section   │
                │ D, Cover, Materials   │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Reinforcement Layout  │
                │ Layers / Bundles /    │
                │ Triplets              │
                └───────────┬───────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
   ┌──────────────────┐          ┌──────────────────┐
   │ Flexural Analysis│          │ Shear Analysis   │
   │ ULS + SLS        │          │ IS 456 / IRC 112 │
   └────────┬─────────┘          └────────┬─────────┘
            │                             │
            ▼                             ▼
   ┌──────────────────┐          ┌──────────────────┐
   │ N-Mx-My Capacity │          │ Vc + Vs Capacity │
   │ Interaction      │          │ + Limits         │
   └────────┬─────────┘          └────────┬─────────┘
            │                             │
            └──────────────┬──────────────┘
                           ▼
                 ┌─────────────────────┐
                 │ Design Check Result │
                 │ SAFE / NOT SAFE     │
                 └─────────────────────┘
```

---

## 📐 Design Codes

| Analysis | Code / Reference | Implementation |
|---|---|---|
| Concrete & steel properties | IS 456:2000 | ULS/SLS material models |
| Biaxial bending | IS 456:2000 Cl. 39.6 | Interaction equation |
| Concrete shear strength | IS 456:2000 Table 19 | Interpolation |
| Minimum shear reinforcement | IS 456:2000 Cl. 26.5.1.6 | Check included |
| Shear resistance | IRC:112-2011 | Simplified implementation |

> **Engineering note:** The IRC:112 module is explicitly described in the source as a **simplified Eurocode-based approach**. It should therefore be independently verified against the governing project provisions before use for final design.

---

## 📥 Input Parameters

### Section

| Parameter | Description | Unit |
|---|---|---|
| `D` | Circular section diameter | mm |
| `cover` | Clear cover to outermost reinforcement | mm |

### Materials

| Parameter | Description | Unit |
|---|---|---|
| `fck` | Characteristic concrete strength | MPa |
| `fy` | Characteristic reinforcement strength | MPa |

### Reinforcement

| Parameter | Description |
|---|---|
| Number of bars | Total longitudinal reinforcement |
| Bar diameter | Longitudinal bar diameter |
| Layer radius | Radius of each reinforcement layer |
| Group type | `single`, `bundle`, or `triplet` |
| Stirrup diameter | Shear reinforcement diameter |
| Stirrup spacing | Shear reinforcement spacing |
| Number of legs | Number of stirrup legs |

### Loads

#### ULS

- Factored axial load `Pu`
- Factored moment `Mux`
- Factored moment `Muy`
- Compression is positive; tension is negative

#### SLS

- Service axial load `P`
- Service moment `Mx`
- Service moment `My`

The supplied flexural program collects these inputs interactively from the command line. fileciteturn0file0L397-L465

---

## 🔍 Flexural Module

### 1. Fibre Discretisation

The circular concrete section is divided into small square fibres. The supplied implementation uses a **5 mm grid spacing** for concrete discretisation. fileciteturn0file0L73-L92

Each concrete fibre stores:

```text
(x, y, area)
```

Reinforcement bars are represented individually by:

```text
(x, y, area)
```

This allows the section forces to be obtained directly from the strain distribution.

### 2. Strain Compatibility

The strain at any point is defined as:

```text
ε = ε₀ + κx·y + κy·x
```

where:

- `ε₀` = strain at the section centroid
- `κx` = curvature associated with bending about X
- `κy` = curvature associated with bending about Y

The resulting stresses are integrated over the concrete fibres and reinforcement bars to obtain:

```text
N   = Axial force
Mx  = Moment about X
My  = Moment about Y
```

The supplied implementation uses this formulation for both ULS and SLS force calculations. fileciteturn0file0L142-L169

---

## 📊 ULS Biaxial Check

The program calculates:

- `Mux1` = uniaxial moment capacity about X
- `Muy1` = uniaxial moment capacity about Y
- `alpha_n` = interaction exponent
- Biaxial interaction ratio

The implemented interaction expression is:

```text
(|Mux| / Mux1)^alpha_n + (|Muy| / Muy1)^alpha_n ≤ 1.0
```

Therefore:

| Ratio | Result |
|---:|---|
| `≤ 1.0` | ✅ SAFE |
| `> 1.0` | ❌ NOT SAFE |

The source identifies this calculation as the **IS 456 Clause 39.6** biaxial bending check. fileciteturn0file0L238-L260

---

## 🧱 SLS Check

The serviceability module performs a cracked-section analysis and reports:

- Maximum concrete compressive stress
- Maximum steel tensile stress
- Approximate crack width

The current supplied implementation compares the calculated values with:

```text
Permissible concrete stress = 0.45 fck
Permissible steel stress    = 0.87 fy
Permissible crack width     = 0.30 mm
```

These limits are implemented directly in the supplied program. fileciteturn0file0L479-L493

---

## 🌀 Shear Module

### IS 456 Shear Check

The supplied IS 456 implementation calculates:

```text
d      = 0.8D
b      = D
τv     = Vu / (b·d)
```

It then obtains `τc` by interpolation from the embedded Table 19 dataset. fileciteturn1file0L79-L106

Axial compression can increase the effective concrete shear strength, subject to the implemented cap:

```text
δ ≤ 1.5
```

If:

```text
τv ≤ τc,eff
```

the section does not require shear reinforcement for the calculated shear demand, although the implementation still checks/proposes minimum reinforcement.

If:

```text
τv > τc,eff
```

the program evaluates the provided stirrup contribution and total shear capacity. fileciteturn1file0L108-L162

---

## 🌉 IRC:112 Shear Check

The IRC module evaluates the concrete contribution without shear reinforcement first.

Key calculated parameters include:

```text
ρ       = Asl / (bwd)
σcp     = Pu / Ac
k       = 1 + √(200/d)
V_Rd,c  = Concrete shear resistance
V_Rd,s  = Shear reinforcement resistance
V_Rd,max = Maximum shear resistance
```

The supplied implementation limits `ρ` and axial stress according to the values coded in the module and uses `cotθ = 2.5` for the shear-reinforcement calculation. fileciteturn1file0L166-L214 fileciteturn1file0L239-L259

---

## 🚀 Getting Started

### Requirements

Install Python 3.9+ and the required packages:

```bash
pip install numpy scipy
```

### Run the Flexural Analysis

```bash
python circular_rc_section.py
```

### Run the Shear Analysis

```bash
python shear_check.py
```

> Replace the filenames above with the actual filenames in your repository.

---

## 🖥️ Example Console Flow

```text
======================================================================
Circular RC Section Design Check (IS 456:2000)
======================================================================

Enter diameter of circular section (mm):
Enter clear cover to outermost reinforcement (mm):
Enter characteristic concrete strength fck (MPa):
Enter characteristic steel strength fy (MPa):

Reinforcement arrangement options:
1. Single layer
2. Alternate bars (two layers)
3. Multiple layers (user-defined)

--- Loads ---
Enter factored axial load Pu (kN):
Enter factored moment Mux (kNm):
Enter factored moment Muy (kNm):

--- ULS Check ---
Uniaxial moment capacity about x
Uniaxial moment capacity about y
Alpha_n
Interaction ratio

ULS: OK, section is safe.
```

The available reinforcement options and corresponding inputs are defined directly in the supplied program. fileciteturn0file0L410-L454

---

## 📋 Output Summary

### Flexure

```text
Total steel area As
Gross concrete area Ac
Percentage of steel

Uniaxial Mux capacity
Uniaxial Muy capacity
Alpha_n
Biaxial interaction ratio
ULS status

Maximum concrete stress
Maximum steel stress
Approximate crack width
SLS status
```

### Shear

```text
Effective depth
Longitudinal reinforcement ratio
Nominal shear stress / design shear resistance
Concrete shear capacity
Stirrup shear capacity
Total shear capacity
Maximum shear capacity
Minimum shear reinforcement
SAFE / NOT SAFE
```

---

## 🧩 Project Structure

A recommended repository structure is:

```text
circular-rcc-section-design/
│
├── src/
│   ├── circular_rc_section.py
│   └── shear_check.py
│
├── examples/
│   └── example_input.txt
│
├── tests/
│   ├── test_flexure.py
│   └── test_shear.py
│
├── docs/
│   └── methodology.md
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

## ⚠️ Engineering Limitations & Verification

This repository is a **calculation and engineering-analysis tool**, not a substitute for independent design verification.

Before using results for a project submission:

- Verify all equations against the **current governing edition** of the relevant code.
- Verify assumptions made for circular-section effective depth and width.
- Independently verify stress-strain models and permissible stresses.
- Review the crack-width methodology for the specific design case.
- Review the simplified IRC:112 implementation against the exact project requirements.
- Check minimum and maximum reinforcement, detailing, spacing, confinement and ductility requirements separately where applicable.
- Validate results against hand calculations or an independently verified commercial/engineering analysis package.

The supplied source itself contains simplified assumptions in the shear implementation, including `d = 0.8D` and `b = D`. fileciteturn1file0L90-L103

---

## 🛠️ Roadmap

Potential future improvements:

- [ ] Interactive circular-section geometry editor
- [ ] Graphical reinforcement placement
- [ ] Automatic reinforcement detailing
- [ ] P-M interaction diagram
- [ ] Full 3D P-Mx-My interaction surface
- [ ] Moment-curvature analysis
- [ ] Automatic neutral-axis search
- [ ] Improved crack-width calculation
- [ ] Code-clause-linked calculation report
- [ ] PDF calculation report
- [ ] Excel export
- [ ] Interactive stress/strain plots
- [ ] Reinforcement utilization visualization
- [ ] Unit system selector
- [ ] GUI / web application
- [ ] Automated validation test suite

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/new-analysis
```

3. Make and test your changes
4. Commit your changes

```bash
git commit -m "Add new analysis feature"
```

5. Push the branch

```bash
git push origin feature/new-analysis
```

6. Open a Pull Request

For engineering-related changes, include the relevant code clause, equation/reference, assumptions and validation example.

---

## 📚 References

- **IS 456:2000** — Plain and Reinforced Concrete — Code of Practice
- **IRC:112-2011** — Code of Practice for Concrete Road Bridges
- Relevant project specifications and amendments should be checked before final design use.

---

## 👨‍💻 Author

**Arvind Singh Rawat**  
Bridge Design Engineer | RCC • PSC • Steel Structures

Structural engineering tools and automation for practical bridge and structural design workflows.

- LinkedIn: [linkedin.com/in/arvindrawat400](https://www.linkedin.com/in/arvindrawat400/)
- Email: [arvindrawat400@gmail.com](mailto:arvindrawat400@gmail.com)

---

## 📄 License

This project can be released under the **MIT License**. Add the full [MIT License](LICENSE) file to the repository before publishing under MIT.

---

<div align="center">

### 🏗️ Built for Structural Engineers

**Circular RCC Section • Flexure • Biaxial Bending • Shear • Serviceability**

⭐ If this project is useful, consider giving it a star on GitHub.

</div>
