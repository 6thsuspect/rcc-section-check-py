import numpy as np
import math
from scipy.optimize import brentq

# ----------------------------------------------------------------------
# Material properties as per IS 456
# ----------------------------------------------------------------------
def material_properties(fck, fy):
    """Return design strengths and moduli."""
    Es = 200000.0          # MPa
    Ec = 5000.0 * math.sqrt(fck)  # MPa
    fcd = 0.45 * fck       # MPa (for ULS)
    fyd = 0.87 * fy        # MPa (for ULS)
    return Es, Ec, fcd, fyd

# ----------------------------------------------------------------------
# Stress-strain models
# ----------------------------------------------------------------------
def concrete_stress_uls(strain, fck):
    """Concrete stress for ULS (parabolic-rectangular)."""
    fcd = 0.45 * fck
    if strain <= 0:
        return 0.0
    elif strain <= 0.002:
        return fcd * (2 * strain / 0.002 - (strain / 0.002) ** 2)
    elif strain <= 0.0035:
        return fcd
    else:
        return 0.0

def steel_stress_uls(strain, fy):
    """Steel stress for ULS (bilinear)."""
    Es = 200000.0
    fyd = 0.87 * fy
    stress = Es * strain
    if stress > fyd:
        return fyd
    elif stress < -fyd:
        return -fyd
    else:
        return stress

def concrete_stress_sls(strain, Ec):
    """Concrete stress for SLS (linear, compression only)."""
    if strain <= 0:
        return 0.0
    else:
        return Ec * strain

def steel_stress_sls(strain, Es):
    """Steel stress for SLS (linear)."""
    return Es * strain

# ----------------------------------------------------------------------
# Section discretisation
# ----------------------------------------------------------------------
class CircularSection:
    def __init__(self, D, cover, layers):
        """
        D       : overall diameter (mm)
        cover   : clear cover to outermost reinforcement (mm)
        layers  : list of dicts, each with keys:
                    'n_bars'       : total number of bars in the layer
                    'dia'          : bar diameter (mm)
                    'radius'       : radius of the layer (mm) from centre
                    'group_type'   : 'single', 'bundle', or 'triplet'
        """
        self.D = D
        self.R = D / 2.0
        self.cover = cover
        self.layers = layers

        # Concrete discretisation: small squares (fibres)
        self.dx = 5.0   # grid spacing (mm)
        self.concrete_fibres = []   # list of (x, y, area)
        self._discretise_concrete()

        # Steel bars coordinates and areas
        self.steel_bars = []   # list of (x, y, area)
        self._place_steel()

        # Total steel area
        self.Asc = sum(bar[2] for bar in self.steel_bars)

    def _discretise_concrete(self):
        """Create a grid of small square fibres covering the circle."""
        R = self.R
        dx = self.dx
        for x in np.arange(-R, R, dx):
            for y in np.arange(-R, R, dx):
                if x*x + y*y <= R*R:
                    self.concrete_fibres.append((x + dx/2, y + dx/2, dx*dx))

    def _place_steel(self):
        """Place bars according to layer specifications, supporting single, bundle, and triplet groups."""
        for layer in self.layers:
            n_bars = layer['n_bars']
            dia = layer['dia']
            r = layer['radius']
            group_type = layer.get('group_type', 'single')  # default to single
            area_bar = math.pi * dia**2 / 4.0

            # Determine number of bars per group
            if group_type == 'single':
                bars_per_group = 1
            elif group_type == 'bundle':
                bars_per_group = 2
            elif group_type == 'triplet':
                bars_per_group = 3
            else:
                raise ValueError(f"Unknown group type: {group_type}")

            if n_bars % bars_per_group != 0:
                raise ValueError(f"Number of bars ({n_bars}) must be divisible by {bars_per_group} for group type '{group_type}'")

            n_groups = n_bars // bars_per_group

            # Angular spacing between adjacent bars within a group (for bundle/triplet)
            # For small angles, arc length ≈ r * Δθ; set Δθ = dia / r (so centre-to-centre = dia)
            if bars_per_group > 1:
                delta_theta = dia / r  # radians
            else:
                delta_theta = 0.0

            # Place groups evenly around the circle
            for i in range(n_groups):
                base_angle = 2 * math.pi * i / n_groups
                if bars_per_group == 1:
                    angles = [base_angle]
                elif bars_per_group == 2:
                    # Two bars side by side tangentially
                    angles = [base_angle - delta_theta/2, base_angle + delta_theta/2]
                elif bars_per_group == 3:
                    # Three bars in a row tangentially
                    angles = [base_angle - delta_theta, base_angle, base_angle + delta_theta]

                for angle in angles:
                    x = r * math.cos(angle)
                    y = r * math.sin(angle)
                    self.steel_bars.append((x, y, area_bar))

    # ------------------------------------------------------------------
    # Internal force calculation from strain distribution
    # ------------------------------------------------------------------
    def compute_forces_uls(self, eps0, kx, ky, fck, fy):
        """
        Given strain at centroid eps0 and curvatures kx (about x-axis, causing strain variation with y)
        and ky (about y-axis, causing strain variation with x), compute N, Mx, My (ULS).
        Strain at a point (x, y) = eps0 + kx*y + ky*x.
        """
        N = 0.0
        Mx = 0.0
        My = 0.0

        for x, y, area in self.concrete_fibres:
            strain = eps0 + kx * y + ky * x
            stress = concrete_stress_uls(strain, fck)
            N += stress * area
            Mx += stress * area * y
            My += stress * area * x

        for x, y, area in self.steel_bars:
            strain = eps0 + kx * y + ky * x
            stress = steel_stress_uls(strain, fy)
            N += stress * area
            Mx += stress * area * y
            My += stress * area * x

        return N, Mx, My

    def compute_forces_sls(self, eps0, kx, ky, Ec, Es):
        """
        Linear elastic (SLS), concrete in compression only.
        Strain at (x,y) = eps0 + kx*y + ky*x.
        """
        N = 0.0
        Mx = 0.0
        My = 0.0

        for x, y, area in self.concrete_fibres:
            strain = eps0 + kx * y + ky * x
            stress = concrete_stress_sls(strain, Ec)
            N += stress * area
            Mx += stress * area * y
            My += stress * area * x

        for x, y, area in self.steel_bars:
            strain = eps0 + kx * y + ky * x
            stress = steel_stress_sls(strain, Es)
            N += stress * area
            Mx += stress * area * y
            My += stress * area * x

        return N, Mx, My

    # ------------------------------------------------------------------
    # Uniaxial ULS capacity for a given axial load
    # ------------------------------------------------------------------
    def uniaxial_capacity_uls(self, Pu, axis, fck, fy):
        """
        Find uniaxial moment capacity about 'axis' ('x' or 'y') for axial load Pu.
        Assumes bending about that axis only (other curvature zero).
        Uses strain compatibility and scans over neutral axis depth.
        Returns moment capacity (Nmm).
        """
        R = self.R
        eps_cu = 0.0035
        c_values = np.logspace(-2, 3, 300) * R
        results = []

        for c in c_values:
            kappa = eps_cu / c
            eps0 = -kappa * (R - c)
            if axis == 'x':
                N, Mx, _ = self.compute_forces_uls(eps0, kappa, 0.0, fck, fy)
                M = Mx
            else:
                N, _, My = self.compute_forces_uls(eps0, 0.0, kappa, fck, fy)
                M = My
            results.append((c, N, M))

        results.sort(key=lambda t: t[1])
        Ns = [r[1] for r in results]
        Ms = [r[2] for r in results]

        capacities = []
        for i in range(len(Ns) - 1):
            if (Ns[i] - Pu) * (Ns[i+1] - Pu) <= 0:
                if abs(Ns[i+1] - Ns[i]) > 1e-12:
                    t = (Pu - Ns[i]) / (Ns[i+1] - Ns[i])
                    M_cap = Ms[i] + t * (Ms[i+1] - Ms[i])
                    capacities.append(M_cap)
        if capacities:
            return max(capacities)
        else:
            return 0.0

    # ------------------------------------------------------------------
    # ULS biaxial check
    # ------------------------------------------------------------------
    def check_uls(self, Pu, Mux, Muy, fck, fy):
        """
        Check biaxial bending per IS 456 Clause 39.6.
        Pu  : factored axial load (N) [compression positive]
        Mux, Muy : factored moments (Nmm) about x and y axes.
        Returns capacity ratio, alpha_n, Mux1, Muy1.
        """
        Puz = 0.45 * fck * (math.pi * self.R**2) + 0.75 * fy * self.Asc

        Mux1 = self.uniaxial_capacity_uls(Pu, 'x', fck, fy)
        Muy1 = self.uniaxial_capacity_uls(Pu, 'y', fck, fy)

        if Puz > 0:
            alpha_n = 0.667 + 1.667 * (Pu / Puz)
        else:
            alpha_n = 1.0
        alpha_n = max(1.0, min(2.0, alpha_n))

        ratio = (abs(Mux) / Mux1) ** alpha_n + (abs(Muy) / Muy1) ** alpha_n if (Mux1 > 0 and Muy1 > 0) else 1e9
        return ratio, alpha_n, Mux1, Muy1

    # ------------------------------------------------------------------
    # SLS analysis (cracked section, uniaxial bending)
    # ------------------------------------------------------------------
    def sls_uniaxial(self, P, M, Ec, Es):
        """
        Perform cracked section analysis under axial load P and moment M.
        Assumes bending about x-axis (strain varies with y).
        Returns: eps0, kappa, sigma_c_max, sigma_s_max_tension, neutral_axis_depth
        """
        R = self.R

        def residual(c_guess):
            y_NA = R - c_guess
            A_c = 0.0
            Sy_c = 0.0
            Iy_c = 0.0
            for x, y, area in self.concrete_fibres:
                if y >= y_NA:
                    A_c += area
                    Sy_c += y * area
                    Iy_c += y**2 * area

            A_st = 0.0
            Sy_st = 0.0
            Iy_st = 0.0
            for x, y, area in self.steel_bars:
                A_st += area
                Sy_st += y * area
                Iy_st += y**2 * area

            A = Ec * A_c + Es * A_st
            B = Ec * Sy_c + Es * Sy_st
            C = Ec * Iy_c + Es * Iy_st

            det = A * C - B * B
            if abs(det) < 1e-12:
                return 1e9
            eps0 = (P * C - M * B) / det
            kappa = (A * M - B * P) / det

            if abs(kappa) > 1e-12:
                y_NA_actual = -eps0 / kappa
            else:
                y_NA_actual = -R if eps0 >= 0 else R
            c_actual = R - y_NA_actual
            return c_actual - c_guess

        c_low = 0.01 * R
        c_high = 10 * self.D
        try:
            c_solution = brentq(residual, c_low, c_high, xtol=1e-3)
        except (ValueError, RuntimeError):
            c_solution = 10 * self.D

        y_NA = R - c_solution
        A_c = 0.0
        Sy_c = 0.0
        Iy_c = 0.0
        for x, y, area in self.concrete_fibres:
            if y >= y_NA:
                A_c += area
                Sy_c += y * area
                Iy_c += y**2 * area

        A_st = 0.0
        Sy_st = 0.0
        Iy_st = 0.0
        for x, y, area in self.steel_bars:
            A_st += area
            Sy_st += y * area
            Iy_st += y**2 * area

        A = Ec * A_c + Es * A_st
        B = Ec * Sy_c + Es * Sy_st
        C = Ec * Iy_c + Es * Iy_st
        det = A * C - B * B
        eps0 = (P * C - M * B) / det
        kappa = (A * M - B * P) / det

        strain_top = eps0 + kappa * R
        sigma_c_max = Ec * max(strain_top, 0.0)

        sigma_s_max_tension = 0.0
        for x, y, area in self.steel_bars:
            strain = eps0 + kappa * y
            stress = Es * strain
            if stress < sigma_s_max_tension:
                sigma_s_max_tension = stress
        sigma_s_max_tension = abs(sigma_s_max_tension)

        return eps0, kappa, sigma_c_max, sigma_s_max_tension, c_solution

    def check_sls(self, P, Mux, Muy, fck, fy):
        """
        Serviceability check.
        P   : service axial load (N)
        Mux, Muy : service moments (Nmm)
        Returns: max concrete stress, max steel stress, approximate crack width.
        """
        Es, Ec, _, _ = material_properties(fck, fy)

        M_resultant = math.sqrt(Mux**2 + Muy**2)
        if M_resultant < 1e-6:
            sigma_c = P / (math.pi * self.R**2)
            sigma_s = Es * (sigma_c / Ec)
            return sigma_c, sigma_s, 0.0

        eps0, kappa, sigma_c_max, sigma_s_max_tension, c = self.sls_uniaxial(P, M_resultant, Ec, Es)

        min_y = min(bar[1] for bar in self.steel_bars)
        bar_radius = min_y
        a_cr = self.cover + 12.0   # assumed bar diameter ~12mm for spacing
        c_min = self.cover
        h = self.D
        x = c
        d = self.R - bar_radius
        strain_tension_bar = eps0 + kappa * min_y
        es = abs(strain_tension_bar)
        b = self.D
        As_tension = sum(area for x, y, area in self.steel_bars if y <= 0)
        if As_tension > 0:
            epsilon_m = es - (b * (h - x)**2) / (3 * Es * As_tension * (d - x))
        else:
            epsilon_m = es
        if epsilon_m < 0:
            epsilon_m = 0.0
        if (1 + 2*(a_cr - c_min)/(h - x)) > 0:
            crack_width = 3 * a_cr * epsilon_m / (1 + 2*(a_cr - c_min)/(h - x))
        else:
            crack_width = 0.0

        return sigma_c_max, sigma_s_max_tension, crack_width


# ----------------------------------------------------------------------
# Main input and execution
# ----------------------------------------------------------------------
def main():
    print("="*70)
    print("Circular RC Section Design Check (IS 456:2000)")
    print("="*70)

    D = float(input("Enter diameter of circular section (mm): "))
    cover = float(input("Enter clear cover to outermost reinforcement (mm): "))

    fck = float(input("Enter characteristic concrete strength fck (MPa) [e.g., 25]: "))
    fy = float(input("Enter characteristic steel strength fy (MPa) [e.g., 500]: "))

    print("\nReinforcement arrangement options:")
    print("1. Single layer")
    print("2. Alternate bars (two layers)")
    print("3. Multiple layers (user-defined)")
    opt = int(input("Select option (1/2/3): "))

    layers = []
    if opt == 1:
        n_bars = int(input("Enter total number of bars (evenly spaced): "))
        dia = float(input("Enter bar diameter (mm): "))
        radius = D/2 - cover - dia/2
        group_type = input("Enter bar grouping (single/bundle/triplet): ").strip().lower()
        if group_type not in ['single', 'bundle', 'triplet']:
            raise ValueError("Invalid group type")
        layers.append({'n_bars': n_bars, 'dia': dia, 'radius': radius, 'group_type': group_type})

    elif opt == 2:
        n_total = int(input("Enter total number of bars (even): "))
        dia = float(input("Enter bar diameter (mm): "))
        group_type = input("Enter bar grouping (single/bundle/triplet): ").strip().lower()
        if group_type not in ['single', 'bundle', 'triplet']:
            raise ValueError("Invalid group type")
        bars_per_group = {'single':1, 'bundle':2, 'triplet':3}[group_type]
        if n_total % (bars_per_group * 2) != 0:
            raise ValueError("Total bars must be divisible by 2 times bars per group")
        n1 = n_total // 2
        n2 = n_total - n1
        r_outer = D/2 - cover - dia/2
        r_inner = r_outer - max(dia, 25.0)
        layers.append({'n_bars': n1, 'dia': dia, 'radius': r_outer, 'group_type': group_type})
        layers.append({'n_bars': n2, 'dia': dia, 'radius': r_inner, 'group_type': group_type})

    else:
        n_layers = int(input("Enter number of layers: "))
        for i in range(n_layers):
            print(f"\nLayer {i+1}:")
            n_bars = int(input("  Number of bars: "))
            dia = float(input("  Bar diameter (mm): "))
            radius = float(input("  Radius of layer from centre (mm): "))
            group_type = input("  Bar grouping (single/bundle/triplet): ").strip().lower()
            if group_type not in ['single', 'bundle', 'triplet']:
                raise ValueError("Invalid group type")
            layers.append({'n_bars': n_bars, 'dia': dia, 'radius': radius, 'group_type': group_type})

    section = CircularSection(D, cover, layers)
    print(f"\nTotal steel area As = {section.Asc:.2f} mm²")
    print(f"Gross concrete area Ac = {math.pi * (D/2)**2:.2f} mm²")
    print(f"Percentage of steel = {100*section.Asc/(math.pi*(D/2)**2):.2f}%")

    print("\n--- Loads ---")
    Pu = float(input("Enter factored axial load Pu (kN) [compression +, tension -]: ")) * 1000
    Mux = float(input("Enter factored moment Mux (kNm) about x-axis: ")) * 1e6
    Muy = float(input("Enter factored moment Muy (kNm) about y-axis: ")) * 1e6

    P_sls = float(input("Enter service axial load P (kN) [compression +, tension -]: ")) * 1000
    Mux_sls = float(input("Enter service moment Mx (kNm): ")) * 1e6
    Muy_sls = float(input("Enter service moment My (kNm): ")) * 1e6

    print("\n--- ULS Check ---")
    ratio, alpha_n, Mux1, Muy1 = section.check_uls(Pu, Mux, Muy, fck, fy)
    print(f"Uniaxial moment capacity about x (Mux1) = {Mux1/1e6:.2f} kNm")
    print(f"Uniaxial moment capacity about y (Muy1) = {Muy1/1e6:.2f} kNm")
    print(f"Alpha_n = {alpha_n:.3f}")
    print(f"Interaction ratio = {ratio:.3f}")
    if ratio <= 1.0:
        print("ULS: OK, section is safe.")
    else:
        print("ULS: NOT SAFE, ratio > 1.0.")

    print("\n--- SLS Check (approximate) ---")
    sigma_c, sigma_s, crack = section.check_sls(P_sls, Mux_sls, Muy_sls, fck, fy)
    print(f"Maximum concrete compressive stress = {sigma_c:.2f} MPa")
    print(f"Maximum steel tensile stress = {sigma_s:.2f} MPa")
    print(f"Approximate crack width = {crack:.3f} mm")
    sigma_c_per = 0.45 * fck
    sigma_s_per = 0.87 * fy
    crack_per = 0.3
    print(f"Permissible concrete stress = {sigma_c_per:.2f} MPa")
    print(f"Permissible steel stress = {sigma_s_per:.2f} MPa")
    print(f"Permissible crack width = {crack_per} mm")
    if sigma_c <= sigma_c_per and sigma_s <= sigma_s_per and crack <= crack_per:
        print("SLS: OK, section satisfies limits.")
    else:
        print("SLS: NOT OK, check limits.")

if __name__ == "__main__":
    main()
