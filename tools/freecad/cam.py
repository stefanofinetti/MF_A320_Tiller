# Centring cam for the tiller: profile synthesis from the wanted torque curve.
#
# Mechanism (assembly frame, Z up, steering axis at the origin, see docs/assembly.md):
#   - the cam turns with the shaft by theta;
#   - a 608ZZ roller (R_ROLLER) sits on an arm that pivots at PIVOT; at theta = 0 the
#     roller centre is at (RP0, 0), straight above the pivot (+Y);
#   - a compression spring pushes the arm tip, ARM_TIP from the pivot, towards -X.
# The arm turns outwards by beta; the spring is compressed by TIP * sin(beta) more.
# Energy balance: U_spring(beta) = integral of T(theta), so each theta gives a beta,
# the roller centre in cam coordinates (pitch curve), and the cam = pitch curve
# offset inwards by the roller radius.
import numpy as np

P = dict(
    RP0=31.0,          # roller centre radius at theta = 0
    ARM_ROLLER=35.0,   # pivot to roller centre
    ARM_TIP=53.0,      # pivot to spring line
    R_ROLLER=11.0,     # 608ZZ, OD 22
    F0=15.0,           # spring preload at centre, N
    K=2.0,             # spring rate, N/mm
    T_C=60.0,          # soft detent: torque reached within a few degrees of centre, Nmm
    TH_D=3.0,          # detent width, deg
    K_LIN=115.0,       # torque slope over the travel, Nmm/rad
    T_END=220.0,       # extra torque at the end of the travel, Nmm
    TH_WARN=60.0,      # where the end warning starts, deg
    TH_MAX=75.0,       # travel each way, deg
    TH_PROFILE=82.0,   # profile drawn a little past the stop, deg
)


def torque(th, p=P):
    """Wanted restoring torque (Nmm) at cam angle th (rad), positive for th > 0."""
    s = np.sign(th); a = np.abs(th)
    w0, w1 = np.radians(p['TH_WARN']), np.radians(p['TH_MAX'])
    warn = np.clip((a - w0) / (w1 - w0), 0, None) ** 2
    return s * (p['T_C'] * np.tanh(a / np.radians(p['TH_D'])) + p['K_LIN'] * a + p['T_END'] * warn)


def synth(p=P, n=661):
    th = np.linspace(-np.radians(p['TH_PROFILE']), np.radians(p['TH_PROFILE']), n)
    # energy U(theta) = integral of T from 0
    t = torque(th, p)
    U = np.zeros(n); i0 = n // 2
    for i in range(i0 + 1, n):
        U[i] = U[i - 1] + 0.5 * (t[i] + t[i - 1]) * (th[i] - th[i - 1])
    for i in range(i0 - 1, -1, -1):
        U[i] = U[i + 1] + 0.5 * (t[i] + t[i + 1]) * (th[i] - th[i + 1])
    # spring energy for an extra tip travel x: F0 x + K x^2 / 2  ->  x
    x = (-p['F0'] + np.sqrt(p['F0'] ** 2 + 2 * p['K'] * U)) / p['K']
    beta = np.arcsin(np.clip(x / p['ARM_TIP'], -1, 1))
    pivot = np.array([p['RP0'], -p['ARM_ROLLER']])
    C = pivot + p['ARM_ROLLER'] * np.c_[np.sin(beta), np.cos(beta)]      # world
    c, s = np.cos(-th), np.sin(-th)                                        # into cam frame
    pitch = np.c_[c * C[:, 0] - s * C[:, 1], s * C[:, 0] + c * C[:, 1]]
    # inward offset by the roller radius
    d = np.gradient(pitch, axis=0); d /= np.linalg.norm(d, axis=1)[:, None]
    nrm = np.c_[d[:, 1], -d[:, 0]]            # pitch runs counter-clockwise -> outward normal
    if np.mean(np.einsum('ij,ij->i', nrm, pitch)) < 0:
        nrm = -nrm
    prof = pitch - p['R_ROLLER'] * nrm
    # curvature check (no undercut): radius of curvature of the pitch curve > roller radius where convex
    dd = np.gradient(pitch, axis=0); d2 = np.gradient(dd, axis=0)
    k = (dd[:, 0] * d2[:, 1] - dd[:, 1] * d2[:, 0]) / np.linalg.norm(dd, axis=1) ** 3
    rho_min = np.min(1 / np.maximum(k, 1e-9))
    force = p['F0'] + p['K'] * x
    return dict(th=th, T=t, U=U, x=x, beta=beta, pitch=pitch, prof=prof, rho_min=rho_min,
                spring_force=force)


if __name__ == "__main__":
    import sys
    r = synth()
    th = np.degrees(r['th']); R = np.linalg.norm(r['prof'], axis=1); Rp = np.linalg.norm(r['pitch'], axis=1)
    for a in (0, 3, 10, 30, 60, 70, 75, 82):
        i = np.argmin(np.abs(th - a))
        print(f"theta {a:3d}: torque {r['T'][i]:6.1f} Nmm  cam r {R[i]:6.2f}  pitch r {Rp[i]:6.2f}  "
              f"spring +{r['x'][i]:5.2f} mm  force {r['spring_force'][i]:5.1f} N")
    print("min convex curvature radius of the pitch curve:", round(r['rho_min'], 2), "(roller 11)")
    if len(sys.argv) > 1:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(16, 7))
        ax[0].plot(th, r['T'] / 1000 * 1000); ax[0].set_xlabel('deg'); ax[0].set_ylabel('torque Nmm'); ax[0].grid(alpha=.4)
        ax[0].plot(th, r['T'] / 60, '--', label='force at grip r60, N x1000/60'); ax[0].legend()
        ax[1].plot(*r['prof'].T, label='cam'); ax[1].plot(*r['pitch'].T, ':', label='pitch')
        ax[1].add_patch(plt.Circle((0, 0), 6, fill=False)); ax[1].set_aspect('equal'); ax[1].grid(alpha=.4); ax[1].legend()
        plt.tight_layout(); plt.savefig(sys.argv[1], dpi=70)
