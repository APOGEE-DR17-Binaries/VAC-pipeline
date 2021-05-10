# Imports we typically need for defining the prior:
import astropy.units as u
import pymc3 as pm
import exoplanet.units as xu
from exoplanet.distributions import Angle
import thejoker as tj


defaults = {
    'P_min': 1.5 * u.day,
    'P_max': 16384 * u.day,
    'sigma_v': 100 * u.km/u.s,
    'sigma_K0': 30 * u.km/u.s,
    'logs_mean': -3.5,
    'logs_std': 1.
}


def get_prior(**kwargs):
    for k, v in defaults.items():
        kwargs.setdefault(k, v)

    with pm.Model() as model:
        s = xu.with_unit(
            pm.Lognormal('s', kwargs['logs_mean'], kwargs['logs_std']),
            u.km/u.s
        )

        prior = tj.JokerPrior.default(
            P_min=kwargs['P_min'], P_max=kwargs['P_max'],
            sigma_K0=kwargs['sigma_K0'],
            sigma_v=kwargs['sigma_v'],
            s=s
        )

    return prior, model


def get_prior_mcmc(**kwargs):
    for k, v in defaults.items():
        kwargs.setdefault(k, v)

    with pm.Model() as model:
        s = xu.with_unit(
            pm.Lognormal('s', kwargs['logs_mean'], kwargs['logs_std']),
            u.km/u.s
        )

        # When running MCMC, we will sample in the parameters
        #     (M0 - omega, M0 + omega) instead of (M0, omega)
        M0_m_omega = xu.with_unit(Angle('M0_m_omega'), u.radian)
        omega = xu.with_unit(Angle('omega'), u.radian)
        M0 = xu.with_unit(pm.Deterministic('M0', M0_m_omega + omega),
                          u.radian)

        prior_mcmc = tj.JokerPrior.default(
            P_min=kwargs['P_min'], P_max=kwargs['P_max'],
            sigma_K0=kwargs['sigma_K0'],
            sigma_v=kwargs['sigma_v'],
            s=s,
            pars={'M0': M0, 'omega': omega}
        )

    return prior_mcmc, model
