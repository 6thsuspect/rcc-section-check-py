import math

# ----------------------------------------------------------------------
# Table 19 of IS 456:2000 - Design shear strength of concrete (τ_c, N/mm²)
# Rows: percentage steel p (%); Columns: fck = 20, 25, 30, 35, 40
# ----------------------------------------------------------------------
TAU_C_TABLE = {
    0.15: [0.28, 0.29, 0.29, 0.29, 0.30],
    0.25: [0.36, 0.36, 0.37, 0.37, 0.38],
    0.50: [0.48, 0.49, 0.50, 0.50, 0.51],
    0.75: [0.56, 0.57, 0.59, 0.59, 0.60],
    1.00: [0.62, 0.64, 0.66, 0.67, 0.68],
    1.25: [0.67, 0.70, 0.71, 0.73, 0.74],
    1.50: [0.72, 0.74, 0.76, 0.78, 0.79],
    1.75: [0.75, 0.78, 0.80, 0.82, 0.84],
    2.00: [0.79, 0.82, 0.84, 0.86, 0.88],
    2.25: [0.81, 0.85, 0.88, 0.90, 0.92],
    2.50: [0.82, 0.88, 0.91, 0.93, 0.95],
    2.75: [0.82, 0.90, 0.94, 0.96, 0.98],
    3.00: [0.82, 0.91, 0.96, 0.99, 1.01]
}

# List of fck values corresponding to columns
FCK_LIST = [20, 25, 30, 35, 40]

def interpolate_tau_c(p, fck):
    """Return τ_c from Table 19 by linear interpolation for given p (%) and fck (MPa)."""
    # Cap p at 3.0
    p = min(p, 3.0)
    p = max(p, 0.15)  # minimum p in table

    # Get p values sorted
    p_keys = sorted(TAU_C_TABLE.keys())

    # Find bracketing p values
    if p in p_keys:
        p_low = p_high = p
    else:
        p_high = min([x for x in p_keys if x >= p])
        p_low = max([x for x in p_keys if x <= p])

    # Interpolate τ_c for given fck at p_low and p_high
    fck_list = FCK_LIST
    if fck in fck_list:
        idx = fck_list.index(fck)
        tau_low = TAU_C_TABLE[p_low][idx]
        tau_high = TAU_C_TABLE[p_high][idx] if p_high != p_low else tau_low
    else:
        # Interpolate fck between available grades
        fck_low = max([x for x in fck_list if x <= fck])
        fck_high = min([x for x in fck_list if x >= fck])
        idx_low = fck_list.index(fck_low)
        idx_high = fck_list.index(fck_high)
        # τ_c at p_low for both fck_low and fck_high
        tau_p_low_fck_low = TAU_C_TABLE[p_low][idx_low]
        tau_p_low_fck_high = TAU_C_TABLE[p_low][idx_high]
        tau_p_high_fck_low = TAU_C_TABLE[p_high][idx_low] if p_high != p_low else tau_p_low_fck_low
        tau_p_high_fck_high = TAU_C_TABLE[p_high][idx_high] if p_high != p_low else tau_p_low_fck_high

        # Interpolate for fck at p_low and p_high
        if fck_high != fck_low:
            frac = (fck - fck_low) / (fck_high - fck_low)
            tau_low = tau_p_low_fck_low + frac * (tau_p_low_fck_high - tau_p_low_fck_low)
            tau_high = tau_p_high_fck_low + frac * (tau_p_high_fck_high - tau_p_high_fck_low)
        else:
            tau_low = tau_p_low_fck_low
            tau_high = tau_p_high_fck_low

    # Interpolate for p if p not exactly in table
    if p_high != p_low:
        frac_p = (p - p_low) / (p_high - p_low)
        tau_c = tau_low + frac_p * (tau_high - tau_low)
    else:
        tau_c = tau_low

    return tau_c


def check_shear_IS456(D, cover, fck, fy, Pu_kN, Vu_kN, n_bars, dia_bar, stirrup_dia, stirrup_spacing, n_legs):
    """
    Shear check as per IS 456:2000 for circular section.
    D: diameter (mm), cover: clear cover (mm), fck, fy in MPa.
    Pu_kN: axial load (kN) (compression positive), Vu_kN: applied shear (kN).
    n_bars, dia_bar: longitudinal reinforcement.
    stirrup_dia, stirrup_spacing: if shear reinforcement provided; if spacing=0, no stirrups.
    n_legs: number of legs of stirrups (usually 2).
    """
    print("\n--- Shear Check as per IS 456:2000 ---")

    # Effective depth and width
    d = 0.8 * D   # simplified assumption for circular section
    b = D         # width taken as diameter
    bd = b * d    # effective shear area

    # Concrete area (gross)
    Ag = math.pi / 4 * D**2

    # Longitudinal steel area and percentage
    Ast = n_bars * (math.pi / 4) * dia_bar**2
    p = 100 * Ast / bd   # percentage steel on effective area

    # Shear stress
    tau_v = Vu_kN * 1000 / bd   # N/mm²

    # Concrete shear strength from Table 19
    tau_c = interpolate_tau_c(p, fck)

    # Enhancement due to axial compression (if Pu > 0)
    if Pu_kN > 0:
        delta = 1 + 3 * Pu_kN * 1000 / (Ag * fck)
        if delta > 1.5:
            delta = 1.5
        tau_c_eff = tau_c * delta
    else:
        tau_c_eff = tau_c

    print(f"Effective depth d = 0.8D = {d:.0f} mm, b = D = {b:.0f} mm")
    print(f"Percentage steel p = {p:.2f}%")
    print(f"Nominal shear stress τ_v = {tau_v:.3f} N/mm²")
    print(f"Design shear strength of concrete τ_c = {tau_c:.3f} N/mm²")
    if Pu_kN > 0:
        print(f"Enhancement factor δ = {delta:.2f}, Enhanced τ_c = {tau_c_eff:.3f} N/mm²")

    # Check if shear reinforcement required
    if tau_v <= tau_c_eff:
        print("\nτ_v <= τ_c_eff: Shear reinforcement is NOT required.")
        print("Provide minimum shear reinforcement as per IS 456 Cl.26.5.1.6:")
        # Minimum Asv/sv = 0.4/(0.87 fy) * b
        Asv_sv_min = 0.4 / (0.87 * fy) * b
        print(f"Minimum Asv/sv = {Asv_sv_min:.4f} mm²/mm")
        if stirrup_spacing > 0:
            Asv_provided = n_legs * (math.pi / 4) * stirrup_dia**2
            Asv_sv_provided = Asv_provided / stirrup_spacing
            print(f"Provided Asv/sv = {Asv_sv_provided:.4f} mm²/mm")
            if Asv_sv_provided >= Asv_sv_min:
                print("Provided shear reinforcement is adequate.")
            else:
                print("Warning: Provided shear reinforcement is less than minimum required.")
        else:
            print("No shear reinforcement provided; minimum must be provided.")
        return True   # safe

    else:
        print("\nτ_v > τ_c_eff: Shear reinforcement is REQUIRED.")
        if stirrup_spacing <= 0:
            print("No shear reinforcement provided - section is NOT safe.")
            return False
        else:
            # Contribution of shear reinforcement
            Asv = n_legs * (math.pi / 4) * stirrup_dia**2   # mm²
            Vus = 0.87 * fy * Asv * d / stirrup_spacing / 1000   # kN
            Vc = tau_c_eff * bd / 1000   # kN
            Vn = Vc + Vus
            print(f"Shear capacity of concrete Vc = {Vc:.2f} kN")
            print(f"Shear capacity of stirrups Vus = {Vus:.2f} kN")
            print(f"Total shear capacity Vn = Vc + Vus = {Vn:.2f} kN")
            print(f"Applied shear Vu = {Vu_kN:.2f} kN")
            if Vn >= Vu_kN:
                print("Section is SAFE in shear.")
                return True
            else:
                print("Section is NOT SAFE. Increase stirrup diameter or reduce spacing.")
                return False


def check_shear_IRC112(D, cover, fck, fy, Pu_kN, Vu_kN, n_bars, dia_bar, stirrup_dia, stirrup_spacing, n_legs):
    """
    Shear check as per IRC:112-2011 (simplified Eurocode-based approach).
    Uses member without shear reinforcement formula first.
    """
    print("\n--- Shear Check as per IRC:112-2011 ---")

    # Material partial safety factors
    gamma_c = 1.5
    gamma_s = 1.15
    fcd = 0.67 * fck / gamma_c
    fyd = fy / gamma_s

    # Effective depth and width (similar assumptions)
    d = 0.8 * D
    b_w = D
    bd = b_w * d

    # Gross concrete area
    Ac = math.pi / 4 * D**2

    # Longitudinal steel
    Asl = n_bars * (math.pi / 4) * dia_bar**2
    rho = Asl / bd   # ratio, not percentage
    rho = min(rho, 0.02)   # limit

    # Axial stress (compression positive)
    if Pu_kN > 0:
        sigma_cp = Pu_kN * 1000 / Ac   # N/mm²
        sigma_cp = min(sigma_cp, 0.2 * fcd)
    else:
        sigma_cp = 0.0

    # k factor
    k = 1 + math.sqrt(200 / d)
    if k > 2.0:
        k = 2.0

    # Design shear resistance without shear reinforcement
    C_Rd_c = 0.12
    k1 = 0.15
    term = C_Rd_c * k * (100 * rho * fck) ** (1/3)
    V_Rd_c = (term + k1 * sigma_cp) * b_w * d / 1000   # kN

    # Minimum shear resistance
    nu_min = 0.031 * k ** (1.5) * math.sqrt(fck)
    V_Rd_c_min = (nu_min + k1 * sigma_cp) * b_w * d / 1000

    V_Rd_c = max(V_Rd_c, V_Rd_c_min)

    print(f"Effective depth d = 0.8D = {d:.0f} mm, width b_w = D = {b_w:.0f} mm")
    print(f"Longitudinal reinforcement ratio ρ = {rho:.4f}")
    print(f"Design shear resistance without shear reinf. V_Rd,c = {V_Rd_c:.2f} kN")
    print(f"Applied shear V_Ed = {Vu_kN:.2f} kN")

    if Vu_kN <= V_Rd_c:
        print("\nNo shear reinforcement required (V_Ed <= V_Rd,c).")
        print("Provide minimum shear reinforcement as per IRC:112.")
        # Minimum Asv/s = 0.08 * sqrt(fck) / fyk * b_w * sin(alpha) ; for vertical alpha=90, sin=1
        Asv_sv_min = 0.08 * math.sqrt(fck) / fy * b_w   # mm²/mm
        print(f"Minimum Asv/s = {Asv_sv_min:.4f} mm²/mm")
        if stirrup_spacing > 0:
            Asv = n_legs * (math.pi / 4) * stirrup_dia**2
            Asv_sv_provided = Asv / stirrup_spacing
            print(f"Provided Asv/s = {Asv_sv_provided:.4f} mm²/mm")
            if Asv_sv_provided >= Asv_sv_min:
                print("Provided minimum shear reinforcement is adequate.")
            else:
                print("Warning: Provided shear reinforcement is less than minimum required.")
        else:
            print("No shear reinforcement provided; minimum must be provided.")
        return True
    else:
        print("\nShear reinforcement is required (V_Ed > V_Rd,c).")
        if stirrup_spacing <= 0:
            print("No shear reinforcement provided - section is NOT safe.")
            return False
        else:
            # Check shear capacity with provided stirrups (assuming cotθ = 2.5, θ=21.8°)
            Asv = n_legs * (math.pi / 4) * stirrup_dia**2   # mm²
            z = 0.9 * d   # lever arm
            cot_theta = 2.5
            V_Rd_s = Asv / stirrup_spacing * z * fyd * cot_theta / 1000   # kN
            V_Rd = V_Rd_c + V_Rd_s  # simplified; actually concrete and steel contributions are not simply additive, but we'll use conservative sum.

            # Maximum shear capacity (crushing of strut)
            alpha_cw = 1.0
            nu1 = 0.6 * (1 - fck / 250)
            V_Rd_max = alpha_cw * b_w * z * nu1 * fcd / (cot_theta + 1 / cot_theta) / 1000

            print(f"Shear capacity of concrete V_Rd,c = {V_Rd_c:.2f} kN")
            print(f"Shear capacity of stirrups V_Rd,s = {V_Rd_s:.2f} kN")
            print(f"Total shear capacity (approx.) = {V_Rd:.2f} kN")
            print(f"Maximum shear capacity V_Rd,max = {V_Rd_max:.2f} kN")
            print(f"Applied shear V_Ed = {Vu_kN:.2f} kN")

            if Vu_kN <= V_Rd and Vu_kN <= V_Rd_max:
                print("Section is SAFE in shear.")
                return True
            else:
                print("Section is NOT SAFE. Increase stirrup diameter or reduce spacing.")
                return False


# ----------------------------------------------------------------------
# Main input section
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("Shear Check of Circular RCC Section")
    print("Choose design code:")
    print("1. IS 456:2000")
    print("2. IRC:112-2011")
    code_choice = input("Enter 1 or 2: ").strip()

    # Common inputs
    D = float(input("Diameter D (mm): "))
    cover = float(input("Clear cover (mm): "))
    fck = float(input("Concrete grade fck (MPa): "))
    fy = float(input("Steel grade fy (MPa): "))
    Pu_kN = float(input("Axial load Pu (kN) [compression positive, 0 if none]: "))
    Vu_kN = float(input("Applied shear force Vu (kN): "))

    n_bars = int(input("Number of longitudinal bars: "))
    dia_bar = float(input("Diameter of longitudinal bars (mm): "))

    stirrup_provided = input("Is shear reinforcement (stirrups/ties) provided? (y/n): ").strip().lower()
    if stirrup_provided == 'y':
        stirrup_dia = float(input("Diameter of stirrups (mm): "))
        stirrup_spacing = float(input("Spacing of stirrups (mm): "))
        n_legs = int(input("Number of legs (usually 2): "))
    else:
        stirrup_dia = 0.0
        stirrup_spacing = 0.0
        n_legs = 0

    if code_choice == '1':
        check_shear_IS456(D, cover, fck, fy, Pu_kN, Vu_kN,
                          n_bars, dia_bar, stirrup_dia, stirrup_spacing, n_legs)
    elif code_choice == '2':
        check_shear_IRC112(D, cover, fck, fy, Pu_kN, Vu_kN,
                           n_bars, dia_bar, stirrup_dia, stirrup_spacing, n_legs)
    else:
        print("Invalid choice. Exiting.")
