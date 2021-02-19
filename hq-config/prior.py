# Imports we typically need for defining the prior:
import astropy.units as u
import pymc3 as pm
import exoplanet.units as xu
from exoplanet.distributions import Angle
import thejoker as tj

# The prior used to run The Joker: please edit below
with pm.Model() as model:
    s = xu.with_unit(pm.Lognormal('s', -3.5, 1),
                     u.km/u.s)

    prior = tj.JokerPrior.default(
        P_min=1.5*u.day, P_max=16384*u.day,
        sigma_K0=30*u.km/u.s,
        sigma_v=100*u.km/u.s,
        s=s
    )

with pm.Model() as model:
    s = xu.with_unit(pm.Lognormal('s', -3.5, 1),
                     u.km/u.s)

    # See note above: when running MCMC, we will sample in the parameters
    # (M0 - omega, omega) instead of (M0, omega)
    M0_m_omega = xu.with_unit(Angle('M0_m_omega'), u.radian)
    omega = xu.with_unit(Angle('omega'), u.radian)
    M0 = xu.with_unit(pm.Deterministic('M0', M0_m_omega + omega),
                      u.radian)

    prior_mcmc = tj.JokerPrior.default(
        P_min=1.5*u.day, P_max=16384*u.day,
        sigma_K0=30*u.km/u.s,
        sigma_v=150*u.km/u.s,
        s=s,
        pars={'M0': M0, 'omega': omega}
    )
