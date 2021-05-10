# Imports we typically need for defining the prior:
import astropy.units as u
import pymc3 as pm
import exoplanet.units as xu
from exoplanet.distributions import Angle
import numpy as np
import thejoker as tj
import theano.tensor as tt


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


def get_prior_mcmc(fixed_s=False, **kwargs):
    for k, v in defaults.items():
        kwargs.setdefault(k, v)

    with pm.Model() as model:
        lnP = pm.Uniform('lnP',
                         np.log(kwargs['P_min'].to_value(u.day)),
                         np.log(kwargs['P_max'].to_value(u.day)))
        P = xu.with_unit(
            pm.Deterministic('P', tt.exp(lnP)),
            u.day)

        if fixed_s is False:
            s = pm.Bound(pm.Lognormal, 0, 5.)('s',
                                              kwargs['logs_mean'],
                                              kwargs['logs_std'])
            s = xu.with_unit(s, u.km/u.s)
        else:
            s = fixed_s

        # When running MCMC, we will sample in the parameters
        #     (M0 - omega, M0 + omega) instead of (M0, omega)
        M0_m_omega = xu.with_unit(Angle('M0_m_omega'), u.radian)
        omega = xu.with_unit(Angle('omega'), u.radian)
        M0 = xu.with_unit(pm.Deterministic('M0', M0_m_omega + omega),
                          u.radian)

        prior_mcmc = tj.JokerPrior.default(
            sigma_K0=kwargs['sigma_K0'],
            sigma_v=kwargs['sigma_v'],
            s=s,
            pars={'P': P, 'M0': M0, 'omega': omega}
        )

    return prior_mcmc, model
