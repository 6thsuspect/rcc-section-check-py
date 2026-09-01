import math

# ------------------------- Helper functions -------------------------
def get_float(prompt, positive=True):
    """Get a float from user with optional positivity check."""
    while True:
        try:
            val = float(input(prompt))
            if positive and val <= 0:
                print("Value must be positive. Try again.")
                continue
            return val
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_int(prompt, positive=True, min_val=None):
    """Get an integer from user."""
    while True:
        try:
            val = int(input(prompt))
            if positive and val <= 0:
                print("Value must be positive. Try again.")
                continue
            if min_val is not None and val < min_val:
                print(f"Value must be at least {min_val}. Try again.")
                continue
            return val
        except ValueError:
            print("Invalid input. Please enter an integer.")

# ------------------------- Input functions -------------------------
def input_section_props():
    """Collect basic section and material data."""
    print("\n--- Section and Material Data ---")
    b = get_float("Width of section b (mm): ")
    D = get_float("Overall depth D (mm): ")
    d = get_float("Effective depth d (mm): ")
    fck = get_float("Characteristic concrete strength fck (N/mm²): ")
    fy = get_float("Yield strength of steel fy (N/mm²): ")
    Vu = get_float("Applied shear force Vu (kN): ")
    return b, D, d, fck, fy, Vu

def input_reinforcement():
    """
    Collect tension reinforcement details.
    Supports multiple layers, alternate bar diameters, and bundling.
    Returns total area of tension steel (Ast) in mm².
    """
    print("\n--- Tension Reinforcement Details ---")
    n_layers = get_int("Number of tension reinforcement layers: ")
    total_area = 0.0
    for i in range(1, n_layers + 1):
        print(f"\nLayer {i}:")
        n_bars_total = get_int("Total number of bars in this layer: ")
        # Ask if all bars have same diameter
        same_dia = input("Are all bars same diameter? (y/n): ").strip().lower()
        if same_dia == 'y':
            dia = get_float("Diameter of bars (mm): ")
            area_layer = n_bars_total * (math.pi * dia**2 / 4)
        else:
            # Alternate diameters: ask for two diameters and number of each
            n1 = get_int("Number of bars with first diameter: ")
            n2 = n_bars_total - n1
            if n2 < 0:
                print("Error: total number of bars inconsistent.")
                return None
            dia1 = get_float("First bar diameter (mm): ")
            dia2 = get_float("Second bar diameter (mm): ")
            area_layer = n1 * (math.pi * dia1**2 / 4) + n2 * (math.pi * dia2**2 / 4)
        
        # Bundling option (optional, does not affect area)
        bundled = input("Are any bars bundled in this layer? (y/n): ").strip().lower()
        if bundled == 'y':
            bundle_size = get_int("Number of bars per bundle: ")
            print(f"Note: Bundling of {bundle_size} bars recorded (affects detailing only).")
        
        total_area += area_layer
        print(f"Area of steel in layer {i} = {area_layer:.2f} mm²")
    
    return total_area

def input_shear_reinf():
    """Collect shear reinforcement (stirrup) details."""
    print("\n--- Shear Reinforcement (Stirrups) ---")
    n_legs = get_int("Number of stirrup legs (vertical legs crossing shear crack): ")
    dia_stirrup = get_float("Diameter of stirrup bar (mm): ")
    spacing = get_float("Spacing of stirrups along the beam (mm): ")
    return n_legs, dia_stirrup, spacing

# ------------------------- IS 456:2000 -------------------------
def tau_c_IS456(fck, p):
    """
    Return design shear strength of concrete (τc) in N/mm² according to Table 19 of IS 456.
    p is percentage steel = 100*Ast/(b*d).
    Linear interpolation is used between table values.
    """
    # Table 19 values for different concrete grades (fck) and p values
    # p values: 0.15,0.25,0.50,0.75,1.00,1.25,1.50,1.75,2.00,2.25,2.50,2.75,3.00
    table = {
        'M15': [0.28,0.35,0.46,0.54,0.60,0.64,0.68,0.71,0.74,0.76,0.79,0.81,0.82],
        'M20': [0.28,0.36,0.48,0.56,0.62,0.67,0.72,0.75,0.79,0.81,0.82,0.84,0.85],
        'M25': [0.29,0.36,0.49,0.57,0.64,0.70,0.74,0.78,0.81,0.84,0.86,0.88,0.90],
        'M30': [0.29,0.37,0.50,0.59,0.66,0.71,0.76,0.80,0.83,0.85,0.88,0.90,0.92],
        'M35': [0.29,0.37,0.50,0.59,0.67,0.73,0.78,0.82,0.86,0.88,0.91,0.93,0.95],
        'M40': [0.30,0.38,0.51,0.60,0.68,0.74,0.79,0.84,0.88,0.91,0.93,0.95,0.97],
        'M45': [0.30,0.38,0.52,0.61,0.69,0.75,0.81,0.85,0.89,0.92,0.95,0.97,0.99],
        'M50': [0.30,0.39,0.53,0.62,0.70,0.76,0.82,0.87,0.91,0.94,0.97,0.99,1.01],
    }
    p_list = [0.15,0.25,0.50,0.75,1.00,1.25,1.50,1.75,2.00,2.25,2.50,2.75,3.00]
    grade = f'M{int(fck)}'
    if grade not in table:
        # fallback to M20 if grade not found
        grade = 'M20'
        print(f"Warning: Concrete grade {grade} not found in Table 19. Using M20 values.")
    vals = table[grade]
    if p <= p_list[0]:
        return vals[0]
    if p >= p_list[-1]:
        return vals[-1]
    for i in range(len(p_list)-1):
        if p_list[i] <= p <= p_list[i+1]:
            # linear interpolation
            slope = (vals[i+1] - vals[i]) / (p_list[i+1] - p_list[i])
            return vals[i] + slope * (p - p_list[i])

def tau_c_max_IS456(fck):
    """Return maximum shear stress τcmax from Table 20 of IS 456."""
    table_max = {15: 2.5, 20: 2.8, 25: 3.1, 30: 3.5, 35: 3.7, 40: 4.0}
    key = int(fck)
    if key in table_max:
        return table_max[key]
    else:
        print(f"Warning: τcmax not defined for M{key}. Assuming 2.8 N/mm².")
        return 2.8

def check_shear_IS(b, d, fck, fy, Vu, Ast, n_legs, dia_stirrup, spacing):
    """Perform shear check per IS 456:2000."""
    print("\n=== Shear Check as per IS 456:2000 ===")
    # Convert Vu from kN to N
    Vu_N = Vu * 1000.0
    # Percentage steel
    p = 100.0 * Ast / (b * d)
    print(f"Percentage tension steel p = {p:.2f}%")
    tau_c = tau_c_IS456(fck, p)
    Vc = tau_c * b * d  # in N
    print(f"Design shear strength of concrete τc = {tau_c:.3f} N/mm²")
    print(f"Concrete shear capacity Vc = {Vc/1000:.2f} kN")

    # Check maximum shear stress
    tau_v = Vu_N / (b * d)
    tau_cmax = tau_c_max_IS456(fck)
    print(f"Nominal shear stress τv = {tau_v:.3f} N/mm²")
    print(f"Maximum permissible shear stress τcmax = {tau_cmax} N/mm²")
    if tau_v > tau_cmax:
        print("Section is inadequate (τv > τcmax). Increase section size.")
        return

    # Stirrup capacity
    Asv = n_legs * (math.pi * dia_stirrup**2 / 4)  # mm²
    Vus = 0.87 * fy * Asv * d / spacing  # in N
    print(f"Stirrup area Asv = {Asv:.2f} mm²")
    print(f"Shear capacity of stirrups Vus = {Vus/1000:.2f} kN")

    V_total = Vc + Vus
    print(f"Total shear capacity Vc + Vus = {V_total/1000:.2f} kN")

    if Vu_N <= Vc:
        print("No shear reinforcement required (Vu ≤ Vc), but minimum stirrups should be provided.")
    elif Vu_N <= V_total:
        print("Provided shear reinforcement is adequate (Vu ≤ Vc + Vus).")
    else:
        print("Shear reinforcement insufficient! Increase stirrup area or reduce spacing.")

# ------------------------- IRC:112-2011 -------------------------
def check_shear_IRC(b, d, fck, fy, Vu, Ast, n_legs, dia_stirrup, spacing, gamma_c=1.5, cot_theta=1.0):
    """
    Perform shear check per IRC:112-2011 (based on Eurocode 2).
    cot_theta: cotangent of strut inclination angle θ (default 1.0 => θ=45°).
    """
    print("\n=== Shear Check as per IRC:112-2011 ===")
    Vu_N = Vu * 1000.0  # N
    # Effective depth to internal lever arm z ≈ 0.9d
    z = 0.9 * d
    # Design concrete compressive strength
    fcd = fck / gamma_c
    # Factor ν1 (reduction for cracked concrete in shear)
    nu1 = 0.6 * (1 - fck / 250)
    # Maximum shear capacity limited by crushing of concrete struts
    alpha_cw = 1.0  # no prestress
    VRd_max = alpha_cw * b * z * nu1 * fcd / (cot_theta + 1/cot_theta)
    print(f"VRd,max = {VRd_max/1000:.2f} kN (concrete strut crushing capacity)")
    if Vu_N > VRd_max:
        print("Applied shear exceeds VRd,max. Section size is insufficient.")
        return

    # Shear resistance of concrete without shear reinforcement
    k = 1 + math.sqrt(200 / d)
    k = min(k, 2.0)
    rho = Ast / (b * d)
    rho = min(rho, 0.02)
    # Assume σcp = 0 (no axial force)
    sigma_cp = 0.0
    CRd_c = 0.12  # for gamma_c = 1.5 (0.18/gamma_c)
    v_min = 0.031 * k**1.5 * math.sqrt(fck)  # minimum shear stress
    VRd_c = (CRd_c * k * (100 * rho * fck)**(1/3) + 0.15 * sigma_cp) * b * d
    VRd_c_min = (v_min + 0.15 * sigma_cp) * b * d
    VRd_c = max(VRd_c, VRd_c_min)
    print(f"VRd,c = {VRd_c/1000:.2f} kN (concrete shear capacity without shear reinforcement)")

    if Vu_N <= VRd_c:
        print("No shear reinforcement required (Vu ≤ VRd,c), but minimum shear reinforcement should be provided.")
        return

    # Shear reinforcement provided
    Asv = n_legs * (math.pi * dia_stirrup**2 / 4)  # mm²
    # Design yield strength of shear reinforcement
    fywd = fy / 1.15  # partial safety factor for steel
    # Shear capacity provided by stirrups
    VRd_s = Asv / spacing * z * fywd * cot_theta
    print(f"Stirrup area Asv = {Asv:.2f} mm²")
    print(f"VRd,s = {VRd_s/1000:.2f} kN (shear capacity from stirrups)")

    VRd_total = min(VRd_s, VRd_max)  # cannot exceed concrete strut capacity
    print(f"Design shear resistance VRd = {VRd_total/1000:.2f} kN")

    if Vu_N <= VRd_total:
        print("Provided shear reinforcement is adequate.")
    else:
        print("Shear reinforcement insufficient! Increase stirrup area or reduce spacing.")

# ------------------------- Main -------------------------
def main():
    print("Shear Check of Rectangular RC Section")
    print("Codes: IS 456:2000 and IRC:112-2011")
    print("Supports multi-layer tension reinforcement, alternate bar diameters, bundled bars.\n")

    b, D, d, fck, fy, Vu = input_section_props()
    Ast = input_reinforcement()
    if Ast is None:
        return
    n_legs, dia_stirrup, spacing = input_shear_reinf()

    print("\nChoose design code:")
    print("1. IS 456:2000")
    print("2. IRC:112-2011")
    code = input("Enter 1 or 2: ").strip()
    if code == '1':
        check_shear_IS(b, d, fck, fy, Vu, Ast, n_legs, dia_stirrup, spacing)
    elif code == '2':
        check_shear_IRC(b, d, fck, fy, Vu, Ast, n_legs, dia_stirrup, spacing)
    else:
        print("Invalid code selection.")

if __name__ == "__main__":
    main()
